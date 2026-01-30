import os
import time
import shutil
import uuid
import fitz
import numpy as np
import json
import re
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from main import process_all_pdfs
from src.chatbot import get_chatbot_response, get_initial_summary, ChatbotResponse
from src.singletons import embedder
from src.insights import router as insights_router


# ----------------------------
# Helpers
# ----------------------------
def clean_filename(name: str) -> str:
    name = name.lower().strip()
    name = name.replace(" ", "_")
    name = re.sub(r"[^a-z0-9_\-.]", "", name)
    return name


def get_session_root(session_id: str) -> Path:
    root = Path("storage") / "sessions" / session_id
    (root / "pdfs").mkdir(parents=True, exist_ok=True)
    (root / "output").mkdir(parents=True, exist_ok=True)
    return root


def get_session_pdf_dir(session_id: str) -> Path:
    return get_session_root(session_id) / "pdfs"


def get_session_output_dir(session_id: str) -> Path:
    return get_session_root(session_id) / "output"


def get_session_current_json(session_id: str) -> Path:
    return get_session_output_dir(session_id) / "current_doc.json"


def load_json(path: Path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("documents", [])
            except:
                return []
    return []


def cosine_similarity(vec1, vec2):
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(title="IntelliPDF - Folder Session System")
app.include_router(insights_router)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "file://",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/storage", StaticFiles(directory="storage"), name="storage")


# ----------------------------
# Models
# ----------------------------
class ChatbotQuery(BaseModel):
    query: str


class SearchRequest(BaseModel):
    selected_text: str
    top_k: int = 3
    min_score: float = 0.3


# ----------------------------
# Routes
# ----------------------------

@app.post("/upload/new")
async def upload_new(sessionId: str = Form(...), file: UploadFile = File(...)):
    if not sessionId:
        raise HTTPException(status_code=400, detail="sessionId is required")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    session_pdf_dir = get_session_pdf_dir(sessionId)

    original_clean = clean_filename(file.filename)
    documentId = f"doc_{uuid.uuid4().hex[:10]}"
    safe_name = f"{Path(original_clean).stem}_{documentId}.pdf"
    file_path = session_pdf_dir / safe_name

    with open(file_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    try:
        with fitz.open(file_path) as doc:
            num_pages = doc.page_count
    except Exception:
        num_pages = 0

    # delete only this session current json
    session_current_doc = get_session_current_json(sessionId)
    if session_current_doc.exists():
        try:
            session_current_doc.unlink()
        except:
            pass

    return {
        "message": "PDF uploaded",
        "sessionId": sessionId,
        "documentId": documentId,
        "file": {
            "storedName": safe_name,
            "pages": num_pages,
            "url": f"/storage/sessions/{sessionId}/pdfs/{safe_name}",
        }
    }


@app.post("/process")
async def process_endpoint(sessionId: str = Form(...)):
    start = time.time()
    if not sessionId:
        raise HTTPException(status_code=400, detail="sessionId is required")

    session_pdf_dir = get_session_pdf_dir(sessionId)
    session_output_dir = get_session_output_dir(sessionId)

    pdf_files = list(session_pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise HTTPException(status_code=404, detail="No PDFs uploaded for this session")

    session_current_doc_path = session_output_dir / "current_doc.json"

    process_all_pdfs(
        pdf_dir=session_pdf_dir,
        output_current_path=session_current_doc_path
    )
    end = time.time()
    latency = end - start
    print(f"Processing time: {end - start:.2f} seconds")
    return {
        "message": "Processing complete",
        "sessionId": sessionId,
        "process_time_sec": round(latency, 3), 
        "output_file": str(session_current_doc_path).replace("\\", "/"),
    }


@app.post("/chatbot", response_model=ChatbotResponse)
async def chatbot_endpoint(sessionId: str = Query(...), query_data: ChatbotQuery = None):
    start = time.time()
    if query_data is None:
        raise HTTPException(status_code=400, detail="Missing request body")

    session_current_doc = get_session_current_json(sessionId)
    if not session_current_doc.exists():
        return ChatbotResponse(
            response="Please upload and process a PDF first.",
            sources=[],
            relevant_images=[]
        )

    result = get_chatbot_response(query_data.query, current_doc_path=session_current_doc)
    end = time.time()
    latency = end - start
    result_dict = result.dict()
    result_dict["response_time_sec"] = round(latency, 3)
    return result_dict



@app.get("/summary", response_model=ChatbotResponse)
async def get_summary(sessionId: str = Query(...)):
    start = time.time()
    session_current_doc = get_session_current_json(sessionId)

    if not session_current_doc.exists():
        return ChatbotResponse(response="Please upload and process a document first.")

    result =  get_initial_summary(current_doc_path=session_current_doc)

    end = time.time()
    latency = end - start   
    result_dict = result.dict()
    result_dict["summary_time_sec"] = round(latency, 3)
    print(f"Summary time: {latency:.2f} seconds")
    return result_dict

@app.post("/search")
def search_endpoint(sessionId: str = Query(...), req: SearchRequest = None):
    start = time.time()
    if req is None:
        raise HTTPException(status_code=400, detail="Missing request body")

    session_current_doc = get_session_current_json(sessionId)
    docs = load_json(session_current_doc)

    if not docs:
        return {"results": []}

    query_text = req.selected_text.strip()
    if not query_text:
        return {"results": []}

    query_embedding = np.array(embedder.embed_texts([query_text])[0])

    results = []
    for doc in docs:
        for sec in doc.get("sections", []):
            sec_embedding = np.array(sec.get("embedding", []))
            if sec_embedding.size == 0:
                continue

            score = cosine_similarity(query_embedding, sec_embedding)
            if score < req.min_score:
                continue

            snippets = [s["text"] for s in sec.get("snippets", [])][:3]
            results.append({
                "title": doc.get("title", ""),
                "section": sec.get("heading", ""),
                "page_number": sec.get("page_number", 1),
                "snippets": snippets,
                "score": float(score),
            })

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:req.top_k]
    end = time.time()
    latency_ms = (end - start) * 1000
    print(f"Search time: {latency_ms:.2f} ms")
    return {
        "search_time_ms": round(latency_ms, 2),
        "results": results}


@app.delete("/delete/{filename}")
async def delete_pdf(filename: str, sessionId: str = Query(...)):
    session_pdf_dir = get_session_pdf_dir(sessionId)
    file_path = session_pdf_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    file_path.unlink()
    return {"message": f"{filename} deleted successfully"}


@app.delete("/session/clear")
async def clear_session(sessionId: str = Query(...)):
    session_root = Path("storage") / "sessions" / sessionId
    if session_root.exists():
        shutil.rmtree(session_root)
    return {"message": f"Session {sessionId} cleared"}
