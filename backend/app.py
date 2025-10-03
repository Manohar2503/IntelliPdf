import sys
import os
import hashlib
import time
import shutil
import uuid
import fitz
import json
import subprocess
import numpy as np

from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv # Import load_dotenv
from src.search_v2 import search_documents, SearchRequest
# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add current directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Routers
from src.insights import router as insights_router
from src.podcast import router as podcast_router
from src.chatbot import get_chatbot_response, get_initial_summary, ChatbotResponse # Import chatbot functions

# Embedding
from src.ranker import EmbeddingGenerator
from main import process_all_pdfs


class ChatbotQuery(BaseModel):
    query: str
    

# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(title="PDF Insight Nexus")

# ----------------------------
# Required directories
# ----------------------------
os.makedirs("newpdf", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("static/audio", exist_ok=True)

NEWPDF_DIR = Path("newpdf")
OUTPUT_DIR = Path("output")

# ----------------------------
# CORS setup
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],  # frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Mount static folders
# ----------------------------

# ----------------------------
# JSON paths
# ----------------------------
PAST_JSON_PATH = OUTPUT_DIR / "output.json"
CURRENT_JSON_PATH = OUTPUT_DIR / "current_doc.json"


def load_json(path: Path):
    if path.exists():
        print(f"Debug - Loading JSON from {path}")
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                docs = data.get("documents", [])
                print(f"Debug - Found {len(docs)} documents in {path}")
                for doc in docs:
                    if "sections" not in doc:
                        doc["sections"] = []
                return docs
            except json.JSONDecodeError:
                return []
    return []


past_docs = load_json(PAST_JSON_PATH)
current_docs = load_json(CURRENT_JSON_PATH)

embedder = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")


# ----------------------------
# Utilities
# ----------------------------
class SearchRequest(BaseModel):
    selected_text: str
    top_k: int = 3
    min_score: float = 0.3


def cosine_similarity(vec1, vec2):
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm1 * norm2)


# ----------------------------
# API Endpoints
# ----------------------------
@app.get("/test")
def test_recommendation():
    test_text = "The South of France, known for its stunning landscapes..."
    query_embedding = np.array(embedder.embed_texts([test_text])[0])
    results = []
    all_docs = past_docs + current_docs

    for doc in all_docs:
        for sec in doc["sections"]:
            sec_embedding = np.array(sec.get("embedding", []))
            if sec_embedding.size == 0:
                continue
            score = cosine_similarity(query_embedding, sec_embedding)
            snippets = [s["text"] for s in sec.get("snippets", [])]
            snippet_text = snippets[0] if snippets else ""
            results.append({
                "doc_id": doc.get("doc_id", ""),
                "title": doc.get("title", ""),
                "pdf_url": doc.get("file_path", ""),
                "section": sec.get("heading", ""),
                "page_number": sec.get("page_number", 1),
                "snippets": snippets,
                "top_snippet": snippet_text,
                "score": float(score)
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:3]


@app.post("/search")
def search_recommendations(req: SearchRequest):
    query_text = req.selected_text.strip()
    if not query_text:
        return {"error": "No text provided"}

    query_embedding = np.array(embedder.embed_texts([query_text])[0])
    results_by_doc = []
    all_docs = past_docs + current_docs

    for doc in all_docs:
        source = "past" if doc in past_docs else "current"
        doc_matches = []
        for sec in doc["sections"]:
            sec_embedding = np.array(sec.get("embedding", []))
            if sec_embedding.size == 0:
                continue
            score = cosine_similarity(query_embedding, sec_embedding)
            if score < req.min_score:
                continue
            snippets = [s["text"] for s in sec.get("snippets", [])][:3]
            snippet_text = snippets[0] if snippets else ""
            doc_matches.append({
                "section": sec.get("heading", ""),
                "page_number": sec.get("page_number", 1),
                "snippets": snippets,
                "top_snippet": snippet_text,
                "score": float(score)
            })
        if doc_matches:
            doc_matches_sorted = sorted(doc_matches, key=lambda x: x["score"], reverse=True)[:req.top_k]
            pdf_file_path = doc.get("file_path", "")
            encoded_filename = quote(Path(pdf_file_path).name)
            public_pdf_url = f"http://localhost:8080/uploads/{encoded_filename}"
            results_by_doc.append({
                "doc_id": doc.get("doc_id", ""),
                "title": doc.get("title", ""),
                "pdf_url": public_pdf_url,
                "source": source,
                "matches": doc_matches_sorted
            })

    return sorted(results_by_doc, key=lambda d: d["matches"][0]["score"], reverse=True)[:req.top_k]


@app.post("/chatbot", response_model=ChatbotResponse)
async def chatbot_endpoint(query_data: ChatbotQuery):
    """
    Endpoint to get a chatbot response based on a query.
    The backend will read the current_doc.json itself.
    """
    print(f"Debug - Chatbot endpoint received query: {query_data.query}")
    response = get_chatbot_response(query_data.query)
    return response

@app.get("/summary", response_model=ChatbotResponse)
async def get_summary():
    """
    Get initial summary of the uploaded document(s)
    """
    try:
        print("Debug - Generating document summary")
        summary = get_initial_summary()
        return summary
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/upload/new")
async def upload_new(file: UploadFile = File(...)):
    """Handle single PDF upload for analysis"""
    # Clear newpdf directory first
    if NEWPDF_DIR.exists():
        for f in NEWPDF_DIR.iterdir():
            if f.is_file():
                f.unlink()
    
    NEWPDF_DIR.mkdir(exist_ok=True, parents=True)
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_path = NEWPDF_DIR / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    unique_id = hashlib.md5(f"{file.filename}{time.time()}".encode()).hexdigest()
    size_bytes = os.path.getsize(file_path)

    try:
        with fitz.open(file_path) as doc:
            num_pages = doc.page_count
    except Exception:
        num_pages = 0

    # Clear current_doc.json
    current_doc_path = OUTPUT_DIR / "current_doc.json"
    if current_doc_path.exists():
        current_doc_path.unlink()

    return {
        "message": "PDF uploaded for analysis",
        "file": {
            "id": unique_id,
            "name": file.filename,
            "url": f"http://localhost:8080/newpdf/{file.filename}",
            "sizeBytes": size_bytes,
            "pages": num_pages,
            "sections": [],
            "dateISO": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "ready"
        }
    }


@app.post("/process")
async def process_pdfs_endpoint():
    try:
        print("Debug - Starting PDF processing")
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        process_all_pdfs()
        print("Debug - PDF processing completed")
        global past_docs, current_docs
        past_docs = load_json(PAST_JSON_PATH)
        current_docs = load_json(CURRENT_JSON_PATH)
        # print("OUTPUT_DIR ->", OUTPUT_DIR.resolve())
        # print("PAST_JSON_PATH ->", PAST_JSON_PATH.resolve())
        # print("CURRENT_JSON_PATH ->", CURRENT_JSON_PATH.resolve())
        return {
            "message": "Processing complete",
            "output_files": ["output/output.json", "output/current_doc.json"]
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.delete("/delete/{filename}")
async def delete_pdf(filename: str):
    file_path = NEWPDF_DIR / filename
    if file_path.exists():
        file_path.unlink()
        return {"message": f"{filename} deleted."}
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.delete("/deletefolder")
async def cleanup_folders():
    FOLDERS = ["newpdf", "input", "output"]
    try:
        for folder_name in FOLDERS:
            folder_path = Path(folder_name)
            if folder_path.exists() and folder_path.is_dir():
                for item in folder_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
        return JSONResponse(content={"message": "Folders cleaned and recreated"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ----------------------------
# Attach Routers
# ----------------------------
app.include_router(insights_router)
app.include_router(podcast_router)
app.mount("/newpdf", StaticFiles(directory=NEWPDF_DIR), name="newpdf")
app.mount("/static", StaticFiles(directory="static"), name="static")
# app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
