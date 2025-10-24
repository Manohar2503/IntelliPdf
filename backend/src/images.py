from fastapi import APIRouter
from typing import List, Dict
from pathlib import Path
import json
from fastapi.responses import FileResponse
from fastapi import HTTPException

router = APIRouter()

@router.get("/images/{doc_id}")
async def get_document_images(doc_id: str) -> List[Dict]:
    """Get all images extracted from a specific document"""
    try:
        # Load current document data
        current_doc_path = Path("output/current_doc.json")
        if not current_doc_path.exists():
            return []
            
        with open(current_doc_path, "r") as f:
            doc_data = json.load(f)
            
        # Handle both single document and list of documents
        documents = doc_data if isinstance(doc_data, list) else doc_data.get("documents", [])
        
        # Find document by ID
        for doc in documents:
            if doc.get("doc_id") == doc_id:
                return doc.get("images", [])
                
        return []
        
    except Exception as e:
        print(f"Error getting document images: {e}")
        return []


@router.get("/images/files/{filename}")
async def serve_image_file(filename: str):
    """Serve an extracted image file by filename. Use in Postman to view/download images."""
    try:
        images_dir = Path("static/images")
        file_path = images_dir / filename
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(path=str(file_path), filename=filename, media_type="image/*")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving image file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/images/{doc_id}/statistics")
async def get_document_image_statistics(doc_id: str) -> Dict:
    """Get statistics about images in a specific document"""
    try:
        # Load current document data
        current_doc_path = Path("output/current_doc.json")
        if not current_doc_path.exists():
            return {}
            
        with open(current_doc_path, "r") as f:
            doc_data = json.load(f)
            
        # Handle both single document and list of documents
        documents = doc_data if isinstance(doc_data, list) else doc_data.get("documents", [])
        
        # Find document by ID
        for doc in documents:
            if doc.get("doc_id") == doc_id:
                return doc.get("image_statistics", {})
                
        return {}
        
    except Exception as e:
        print(f"Error getting image statistics: {e}")
        return {}