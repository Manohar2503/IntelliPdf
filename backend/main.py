#!/usr/bin/env python3
"""
PDF Processing (Sections + Snippets + Embeddings)
✅ No FastAPI here
✅ Used by app.py
"""

import os
import json
import uuid
import re
from pathlib import Path
from datetime import datetime

from src.extract import PDFExtractor
from src.ranker import EmbeddingGenerator
from src.image_extractor import PDFImageExtractor


def extract_snippets(section_text, max_snippets=3):
    sentences = re.split(r"(?<=[.!?])\s+", section_text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    sentences_sorted = sorted(sentences, key=len, reverse=True)
    return sentences_sorted[:max_snippets]


def process_pdfs(pdf_paths, output_path: Path):
    pdf_extractor = PDFExtractor()
    embed_gen = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
    image_extractor = PDFImageExtractor(output_dir="static/images")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_docs_data = []

    # ✅ keep latest pdf only
    if pdf_paths:
        pdf_paths = [max(pdf_paths, key=lambda p: p.stat().st_mtime)]

    for pdf_path in pdf_paths:
        filename = pdf_path.name

        try:
            sections = pdf_extractor.extract_sections(str(pdf_path), filename) or []
        except Exception:
            sections = []

        doc_id = str(uuid.uuid4())

        images = image_extractor.extract_images(str(pdf_path), min_size_kb=5)
        image_stats = image_extractor.get_image_statistics(images)

        doc_data = {
            "doc_id": doc_id,
            "file_path": str(pdf_path),
            "title": os.path.splitext(filename)[0],
            "sections": [],
            "images": images,
            "image_statistics": image_stats,
        }

        # ✅ Add stats here (safe defaults)
        doc_data["stats"] = {
            "total_sections": 0,
            "total_images": len(images),
            "total_snippets": 0
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

                doc_data["sections"].append(
                    {
                        "section_id": section_id,
                        "heading": heading,
                        "heading_level": "H1",
                        "page_number": page_number,
                        "content": content,
                        "snippets": [
                            {"text": s, "embedding": e}
                            for s, e in zip(snippets, snippet_embeddings)
                        ],
                        "embedding": section_embedding,
                    }
                )

        # ✅ Update stats AFTER section generation
        doc_data["stats"]["total_sections"] = len(doc_data["sections"])
        doc_data["stats"]["total_snippets"] = sum(
            len(sec.get("snippets", [])) for sec in doc_data["sections"]
        )

        all_docs_data.append(doc_data)

    output_json = {
        "metadata": {
            "total_documents": len(all_docs_data),
            "processing_timestamp": datetime.now().isoformat(),
        },
        "documents": all_docs_data,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False)



def process_all_pdfs(pdf_dir: Path, output_current_path: Path):
   
    pdf_dir = Path(pdf_dir)
    output_current_path = Path(output_current_path)
    output_current_path.parent.mkdir(parents=True, exist_ok=True)

    pdf_files = [f for f in pdf_dir.iterdir() if f.suffix.lower() == ".pdf"]
    if not pdf_files:
        return

    latest_pdf = max(pdf_files, key=lambda p: p.stat().st_mtime)
    process_pdfs([latest_pdf], output_current_path)
