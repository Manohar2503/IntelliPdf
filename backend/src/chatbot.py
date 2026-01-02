# src/chatbot.py
from typing import List, Dict, Optional
from pydantic import BaseModel
from pathlib import Path
import os
import json
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
from src.summarizer import DocumentSummarizer

# Load environment variables from .env file
load_dotenv()

# Initialize summarizer
doc_summarizer = DocumentSummarizer()

# IMPORTANT: make sure GEMINI_API_KEY is set in env or .env
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY is not set")
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in .env file or environment.")

print(f"Debug - GEMINI_API_KEY: {api_key[:10] + '...' if api_key else 'NOT SET'}")
genai.configure(api_key=api_key)

# Local embedding helper (your project already has this class in src.ranker)
try:
    from src.ranker import EmbeddingGenerator
    embedder = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
except Exception:
    embedder = None

class ImageReference(BaseModel):
    filename: str
    page: int
    path: str
    caption: Optional[str] = None
    relevance_score: float = 0.0
    ocr_text: Optional[str] = None
    ai_labels: Optional[List[Dict[str, float]]] = None

class ChatbotResponse(BaseModel):
    response: str
    sources: List[Dict] = []
    is_summary: bool = False
    relevant_images: List[ImageReference] = []

def get_initial_summary() -> ChatbotResponse:
    """
    Generate initial summary when a new document is loaded
    """
    print("Debug - Starting summary generation")
    docs = _load_current_docs()
    print(f"Debug - Loaded {len(docs)} documents")
    if not docs:
        return ChatbotResponse(
            response="No documents loaded yet.",
            is_summary=True
        )

    try:
        # Get all sections from all documents
        all_sections = []
        for doc in docs:
            sections = doc.get('sections', [])
            print(f"Debug - Document '{doc.get('name', 'unnamed')}' has {len(sections)} sections")
            all_sections.extend(sections)
        print(f"Debug - Total sections to summarize: {len(all_sections)}")

        # Generate summary
        summary_data = doc_summarizer.summarize_document(all_sections)
        initial_message = doc_summarizer.generate_initial_message(summary_data)
        print("\n=== Final Summary Message ===")
        print(initial_message)
        print("\n=============================\n")

        return ChatbotResponse(
            response=initial_message,
            is_summary=True
        )
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return ChatbotResponse(
            response="I've loaded the document but couldn't generate a summary. Feel free to ask specific questions!",
            is_summary=True
        )

# -------------------------
# Helpers
# -------------------------
def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def _load_current_docs() -> List[Dict]:
    """
    Loads output/current_doc.json and returns the 'documents' list
    """
    p = _project_root() / "output" / "current_doc.json"
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # support two shapes: {"documents": [...]} or just [...]
            if isinstance(data, dict):
                return data.get("documents", [])
            elif isinstance(data, list):
                return data
            else:
                return []
        except json.JSONDecodeError:
            return []

def _cosine_similarity(a, b) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if a.size == 0 or b.size == 0:
        return 0.0
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

def _keyword_fallback_search(query: str, docs: List[Dict], top_k: int = 3):
    """
    If embeddings are missing, perform a simple keyword matching fallback.
    Returns candidate sections with a simple integer score.
    """
    q_tokens = set([t for t in query.lower().split() if len(t) > 2])
    candidates = []
    for doc in docs:
        for sec in doc.get("sections", []):
            text = " ".join(sec.get("snippets", [])).strip() or sec.get("text", "")
            if not text:
                continue
            text_low = text.lower()
            score = sum(1 for t in q_tokens if t in text_low)
            if score > 0:
                candidates.append({
                    "doc_id": doc.get("doc_id"),
                    "title": doc.get("title"),
                    "section_heading": sec.get("heading"),
                    "page_number": sec.get("page_number"),
                    "top_snippet": sec.get("snippets", [sec.get("text", "")])[0] if sec.get("snippets") else sec.get("text", ""),
                    "score": float(score)
                })
    candidates_sorted = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return candidates_sorted[:top_k]

def find_relevant_sections_and_images(query: str, top_k: int = 3, min_score: float = 0.2):
    """
    Returns top_k relevant sections and related images using stored embeddings.
    Each returned item includes title, section_heading, page_number, top_snippet, score,
    and any images found in those sections.
    """
    docs = _load_current_docs()
    if not docs:
        return []

    # Try using stored embeddings first
    any_section_has_embedding = False
    for doc in docs:
        for sec in doc.get("sections", []):
            if sec.get("embedding"):
                any_section_has_embedding = True
                break
        if any_section_has_embedding:
            break

    candidates = []
    if any_section_has_embedding and embedder is not None:
        # compute query embedding (using your local embedder class)
        try:
            query_emb = np.array(embedder.embed_texts([query])[0], dtype=float)
        except Exception:
            query_emb = None

        if query_emb is not None:
            for doc in docs:
                for sec in doc.get("sections", []):
                    sec_emb = sec.get("embedding", [])
                    if not sec_emb:
                        continue
                    score = _cosine_similarity(query_emb, sec_emb)
                    # Find images from this page/section
                    section_images = []
                    for img in doc.get("images", []):
                        if img["page"] == sec.get("page_number"):
                            # If image has OCR text, also check relevance using that
                            img_score = score  # Base score from section relevance
                            if img.get("ocr_text"):
                                try:
                                    img_emb = embedder.embed_texts([img["ocr_text"]])[0]
                                    img_score = max(score, float(_cosine_similarity(query_emb, img_emb)))
                                except Exception:
                                    pass
                            
                            if img_score >= min_score:
                                section_images.append({
                                    "filename": img["filename"],
                                    "page": img["page"],
                                    "path": img["path"],
                                    "relevance_score": img_score,
                                    "ocr_text": img.get("ocr_text"),
                                    "ai_labels": img.get("ai_labels")
                                })
                    
                    candidates.append({
                        "doc_id": doc.get("doc_id"),
                        "title": doc.get("title"),
                        "section_heading": sec.get("heading"),
                        "page_number": sec.get("page_number"),
                        "top_snippet": sec.get("snippets", [sec.get("text", "")])[0] if sec.get("snippets") else sec.get("text", ""),
                        "score": float(score),
                        "images": section_images
                    })

            candidates_sorted = sorted(candidates, key=lambda x: x["score"], reverse=True)
            filtered = [c for c in candidates_sorted if c["score"] >= min_score]
            if filtered:
                return filtered[:top_k]
            # if none passed min_score, still return top_k by score
            return candidates_sorted[:top_k]

    # Fallback: keyword-based matching (no embeddings)
    return _keyword_fallback_search(query, docs, top_k=top_k)

def build_context_from_sections(sections: List[Dict], char_limit: int = 3000) -> str:
    """
    Build a context text from chosen sections. Keep within char_limit.
    """
    parts = []
    for s in sections:
        title = s.get("title", "")
        heading = s.get("section_heading", "") or ""
        page = s.get("page_number", "")
        snippet = str(s.get("top_snippet", "")).strip()
        parts.append(f"Source: {title} | Section: {heading} | Page: {page}\n{snippet}")
    text = "\n\n".join(parts)
    if len(text) > char_limit:
        return text[:char_limit]
    return text

def generate_answer_with_gemini(query: str, context: str) -> tuple[Optional[str], Optional[str]]:
    """
    Call Gemini (google.generativeai) to answer using the given context.
    """
    print(f"Debug - Generate answer for query: {query}")
    print(f"Debug - Context length: {len(context) if context else 0} characters")
    
    if not context:
        print("Debug - No context provided to Gemini")
        return None, "No context provided"

    system_instructions = (
        "You are an assistant that MUST answer using only the provided document excerpts (the Context). "
        "If the answer cannot be found in the Context, you should say 'I don't know' or 'The document does not contain that information.' "
        "Keep the answer concise and include short citations in square brackets like [Title - Section]. "
    )

    prompt = f"{system_instructions}\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    try:
        print("Debug - Calling Gemini API...")
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=400,
                temperature=0.0
            )
        )
        print("Debug - Gemini API call successful")

        # Enhanced response handling
        if response is None:
            print("Debug - Gemini returned None response")
            return None, "Gemini API returned no response"

        # Try different ways to get the text content
        answer_text = None
        
        # Method 1: Direct text attribute
        if hasattr(response, "text"):
            answer_text = response.text
        
        # Method 2: Response object text method
        elif hasattr(response, "response"):
            try:
                answer_text = response.response.text()
            except:
                pass

        # Method 3: Parts extraction (some versions return parts)
        elif hasattr(response, "parts"):
            try:
                answer_text = " ".join(part.text for part in response.parts)
            except:
                pass

        if answer_text:
            print("Debug - Successfully extracted answer text")
            return answer_text, None
        else:
            print("Debug - Could not extract text from response")
            return None, "Could not extract text from Gemini response"

    except Exception as e:
        error_message = str(e)
        print("Gemini generation error:", error_message)
        return None, error_message

# -------------------------
# Public entry point
# -------------------------
def get_chatbot_response(query: str, top_k: int = 3) -> ChatbotResponse:
    """
    Main function the FastAPI endpoint should call.
    - finds top sections and images for query
    - calls Gemini with the chosen context
    - returns ChatbotResponse with text and relevant images
    """
    print("\n=== Processing Chatbot Query ===")
    print(f"Query: {query}")
    
    if not query or not isinstance(query, str):
        print("Invalid query:", query)
        return ChatbotResponse(
            response="Invalid query. Please provide a valid question.",
            sources=[],
            relevant_images=[]
        )
    
    try:
        # Load and verify documents
        docs = _load_current_docs()
        print(f"Found {len(docs)} documents in current_doc.json")
        
        if not docs:
            print("No documents found in current_doc.json")
            return ChatbotResponse(
                response="No documents are loaded. Please upload a document first.",
                sources=[],
                relevant_images=[]
            )
            
        for doc in docs:
            print(f"Document: {doc.get('name', 'unnamed')} - {len(doc.get('sections', []))} sections")
    except Exception as e:
        print(f"Error loading documents: {str(e)}")
        return ChatbotResponse(
            response="Error loading documents. Please try again.",
            sources=[],
            relevant_images=[]
        )
    
    try:
        sections = find_relevant_sections_and_images(query, top_k=top_k)
        print(f"Debug - Found {len(sections)} relevant sections")
        
        if not sections:
            return ChatbotResponse(
                response="I couldn't find any relevant information in the document.",
                sources=[],
                relevant_images=[]
            )

        # Collect relevant images from sections
        relevant_images = []
        for section in sections:
            for img in section.get("images", []):
                try:
                    # Handle path being either a string or a dict with 'thumbnail' key
                    # Get the base filename and ensure it exists in static/images
                    base_filename = os.path.basename(original_path)
                    extension = os.path.splitext(base_filename)[1]
                    
                    # Generate thumbnail name
                    thumb_filename = f"{os.path.splitext(base_filename)[0]}_thumb{extension}"
                    
                    # Ensure directories exist
                    static_dir = os.path.join(_project_root(), "static")
                    images_dir = os.path.join(static_dir, "images")
                    thumbnails_dir = os.path.join(images_dir, "thumbnails")
                    
                    os.makedirs(static_dir, exist_ok=True)
                    os.makedirs(images_dir, exist_ok=True)
                    os.makedirs(thumbnails_dir, exist_ok=True)
                    
                    # Full path to the original and thumbnail
                    original_full_path = os.path.join(images_dir, base_filename)
                    thumb_full_path = os.path.join(thumbnails_dir, thumb_filename)
                    
                    print(f"Original image path: {original_full_path}")
                    print(f"Thumbnail path: {thumb_full_path}")
                    
                    # If thumbnail doesn't exist, try to generate it
                    if not os.path.exists(thumb_full_path) and os.path.exists(original_full_path):
                        try:
                            from PIL import Image
                            with Image.open(original_full_path) as img:
                                # Convert RGBA to RGB if necessary
                                if img.mode in ('RGBA', 'LA'):
                                    background = Image.new('RGB', img.size, 'white')
                                    background.paste(img, mask=img.split()[-1])
                                    img = background
                                elif img.mode != 'RGB':
                                    img = img.convert('RGB')
                                
                                # Calculate new dimensions
                                max_size = 300
                                ratio = max_size / max(img.size)
                                if ratio < 1:
                                    new_size = tuple(int(dim * ratio) for dim in img.size)
                                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                                
                                # Save thumbnail
                                img.save(thumb_full_path, quality=85, optimize=True)
                                print(f"Generated thumbnail: {thumb_full_path}")
                        except Exception as e:
                            print(f"Error generating thumbnail for {base_filename}: {str(e)}")
                    
                    # Use thumbnails path if it exists, otherwise use original
                    if os.path.exists(thumb_full_path):
                        img_path = f'/static/images/thumbnails/{thumb_filename}'
                        print(f"Using thumbnail path: {img_path}")
                    else:
                        img_path = f'/static/images/{base_filename}'
                        print(f"Using original path: {img_path}")
                    relevant_images.append(ImageReference(
                        filename=img["filename"],
                        page=img["page"],
                        path=img_path,
                        relevance_score=img["relevance_score"],
                        ocr_text=img.get("ocr_text"),
                        ai_labels=img.get("ai_labels"),
                        caption=f"Image from page {img['page']}" + (f" - {img.get('ocr_text')[:100]}..." if img.get('ocr_text') else "")
                    ))
                except Exception as e:
                    print(f"Error processing image: {str(e)}")
                    continue

        print(f"\nFound {len(sections)} relevant sections:")
        for section in sections:
            print(f"- {section.get('title')} | {section.get('section_heading')} | Score: {section.get('score')}")
        
        context = build_context_from_sections(sections)
        print(f"\nBuilt context with {len(context)} characters")
        
        print("\nGenerating answer with Gemini...")
        answer, error_message = generate_answer_with_gemini(query, context)
        if answer is None:
            # Gemini failed — return an informative message with sources for debugging
            response_text = f"Sorry — I couldn't get an answer from Gemini right now. Error: {error_message}" if error_message else "Sorry — I couldn't get an answer from Gemini right now."
            return ChatbotResponse(response=response_text, sources=sections)

        # Remove any heavy objects (like full embeddings) from sources before returning
        cleaned_sources = []
        for s in sections:
            cleaned = {k: v for k, v in s.items() if k != "embedding"}
            cleaned_sources.append(cleaned)

        # Sort images by relevance score and take top 3
        sorted_images = sorted(relevant_images, key=lambda x: x.relevance_score, reverse=True)[:3]
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return ChatbotResponse(
            response=f"An error occurred while processing your query: {str(e)}",
            sources=[],
            relevant_images=[]
        )
    
    # Final response assembly
    if not answer:
        return ChatbotResponse(
            response="I apologize, but I couldn't generate a proper response at this time. Please try again.",
            sources=cleaned_sources,
            relevant_images=sorted_images
        )

    return ChatbotResponse(
        response=answer.strip(), 
        sources=cleaned_sources, 
        relevant_images=sorted_images
    )
