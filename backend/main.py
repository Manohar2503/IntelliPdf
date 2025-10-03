#!/usr/bin/env python3
"""
Bulk PDF Section & Snippet Extractor (Persona-free)
Adobe Challenge Backend - Main Entry
"""

import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime
import shutil
import re
from dotenv import load_dotenv # Import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware

load_dotenv() # Load environment variables from .env file

BASE_DIR = Path(__file__).resolve().parent
NEWPDF_DIR = Path("newpdf")
OUTPUT_DIR = Path("output")

from src.extract import PDFExtractor       # PDF section extractor
from src.ranker import EmbeddingGenerator  # Embedding generator
from src.chatbot import get_chatbot_response, ChatbotResponse


# --------------------------
# Helper: Generate Snippets
# --------------------------
def extract_snippets(section_text, max_snippets=3):
    """
    Simple snippet extractor: split into sentences,
    return up to `max_snippets` most informative sentences.
    """
    sentences = re.split(r'(?<=[.!?])\s+', section_text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]  # Filter short lines
    sentences_sorted = sorted(sentences, key=len, reverse=True)
    return sentences_sorted[:max_snippets]

# --------------------------
# Process PDFs and generate JSON
# --------------------------
def process_pdfs(pdf_paths, output_file):
    print(f"\n=== Processing PDFs for {output_file} ===")
    pdf_extractor = PDFExtractor()
    embed_gen = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
    
    output_path = OUTPUT_DIR / output_file
    all_docs_data = []

    # For SetForAnalysis (current_doc.json), we only keep the most recent PDF
    if output_file == "current_doc.json":
        # Take only the most recent PDF if multiple files are provided
        if pdf_paths:
            pdf_paths = [max(pdf_paths, key=lambda p: p.stat().st_mtime)]
        print(f"Processing single PDF for analysis: {pdf_paths[0].name if pdf_paths else 'none'}")
    else:
        # For output.json, load existing documents
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if isinstance(existing_data, dict) and 'documents' in existing_data:
                        all_docs_data = existing_data['documents']
                    elif isinstance(existing_data, list):
                        all_docs_data = existing_data
                except json.JSONDecodeError:
                    pass
        print(f"Starting with {len(all_docs_data)} existing documents")

    for pdf_path in pdf_paths:
        filename = pdf_path.name
        print(f"[INFO] Processing {filename}...")

        # Extract sections
        try:
            sections = pdf_extractor.extract_sections(str(pdf_path), filename) or []
        except Exception as e:
            print(f"[ERROR] Failed to extract sections for {filename}: {e}")
            sections = []

        doc_id = str(uuid.uuid4())
        doc_data = {
            "doc_id": doc_id,
            "file_path": str(pdf_path),
            "title": os.path.splitext(filename)[0],
            "sections": []
        }

        if sections:
            sections_with_embeddings = embed_gen.embed_sections(sections)
            for sec in sections_with_embeddings:
                section_id = str(uuid.uuid4())
                heading = sec.get("section_title", "").strip()
                content = sec.get("refined_text", sec.get("content", "")).strip()
                page_number = sec.get("page_number", 1)
                section_embedding = sec.get("embedding", [])

                snippets = extract_snippets(content, max_snippets=3)
                snippet_embeddings = embed_gen.embed_texts(snippets) if snippets else []

                doc_data["sections"].append({
                    "section_id": section_id,
                    "heading": heading,
                    "heading_level": "H1",
                    "page_number": page_number,
                    "content": content,
                    "snippets": [
                        {"text": s, "embedding": e}
                        for s, e in zip(snippets, snippet_embeddings)
                    ],
                    "embedding": section_embedding
                })
        else:
            print(f"[WARN] No sections found for {filename}")

        all_docs_data.append(doc_data)

    # Save the processed documents
    output_path = OUTPUT_DIR / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"documents": all_docs_data}, f, indent=2)
    print(f"Saved {len(all_docs_data)} documents to {output_file}")

    # Save output JSON
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    output_json = {
        "metadata": {
            "total_documents": len(all_docs_data),
            "processing_timestamp": datetime.now().isoformat()
        },
        "documents": all_docs_data
    }
    output_path = OUTPUT_DIR / output_file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False)
    print(f"[INFO] Processing complete. Output saved to {output_path}")

# --------------------------
# Main Entry
# --------------------------
def main():
    # NEWPDF_DIR = Path("newpdf")
    NEWPDF_DIR.mkdir(exist_ok=True, parents=True)

    pdf_files_new = [f for f in NEWPDF_DIR.iterdir() if f.suffix.lower() == ".pdf"]

    if pdf_files_new:
        process_pdfs(pdf_files_new, "current_doc.json")
    else:
        print("[INFO] No PDFs found in 'newpdf/'")


app = FastAPI()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:5173",  # Frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to load document content from current_doc.json
def load_current_document_content():
    current_doc_path = OUTPUT_DIR / "current_doc.json"
    if not current_doc_path.exists():
        return None

    with open(current_doc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Assuming 'documents' is a list and each document has 'sections'
    # and each section has 'content'. Concatenate all content.
    all_content = []
    for doc in data.get("documents", []):
        for section in doc.get("sections", []):
            all_content.append(section.get("content", ""))
    return "\n\n".join(all_content)

class ChatbotRequest(BaseModel):
    query: str

@app.post("/chatbot", response_model=ChatbotResponse)
async def chatbot_endpoint(request: ChatbotRequest):
    """Handle chatbot queries using the processed documents"""
    print(f"\\n=== Chatbot Query: {request.query} ===")
    try:
        response = get_chatbot_response(request.query)
        return response
    except Exception as e:
        print(f"Error processing chatbot query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chatbot/summary")
async def get_document_summary():
    document_content = load_current_document_content()
    if not document_content:
        raise HTTPException(status_code=404, detail="No active document content found for summary.")
    try:
        # Use the chatbot function to generate a summary
        summary_query = "Provide a concise summary of the document."
        response = get_chatbot_response(summary_query, document_content)
        return {"summary": response.response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    main()

# --------------------------
# Helper for FastAPI
# --------------------------
def process_all_pdfs():
    """
    Process PDF in 'newpdf/' directory.
    Only handles the current PDF for analysis.
    """
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    # Process PDF in newpdf directory
    pdf_files = [f for f in NEWPDF_DIR.iterdir() if f.suffix.lower() == ".pdf"]
    if pdf_files:
        # Clear the current_doc.json first
        current_doc_path = OUTPUT_DIR / "current_doc.json"
        if current_doc_path.exists():
            current_doc_path.unlink()

        print("\nProcessing PDF for analysis...")
        process_pdfs(pdf_files, "current_doc.json")
        print("PDF processing complete")
    else:
        print("[INFO] No PDF found in 'newpdf/' directory")
