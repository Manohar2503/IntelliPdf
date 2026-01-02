from fastapi import APIRouter
from typing import List, Dict
from pathlib import Path
import json
import os
from PIL import Image
from fastapi.responses import FileResponse
from fastapi import HTTPException

router = APIRouter()

def ensure_thumbnail_dir():
    """Ensure the thumbnails directory exists"""
    thumb_dir = Path("static/images/thumbnails")
    thumb_dir.mkdir(parents=True, exist_ok=True)
    return thumb_dir

def generate_thumbnail(image_path: Path, max_size: int = 300) -> Path:
    """Generate a thumbnail for an image if it doesn't exist"""
    try:
        # Create thumbnails directory if it doesn't exist
        thumb_dir = ensure_thumbnail_dir()
        
        # Generate thumbnail filename
        thumb_name = image_path.stem + "_thumb" + image_path.suffix
        thumb_path = thumb_dir / thumb_name
        
        # If thumbnail already exists, return its path
        if thumb_path.exists():
            return thumb_path
            
        # Open and resize image
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, 'white')
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate new dimensions maintaining aspect ratio
            ratio = max_size / max(img.size)
            if ratio < 1:
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumb_path, quality=85, optimize=True)
            return thumb_path
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return None

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
        
        # Check if this is a thumbnail request
        is_thumb = "_thumb." in filename
        if is_thumb:
            file_path = images_dir / "thumbnails" / filename
            if not file_path.exists():
                # Try to generate thumbnail from original
                original_name = filename.replace("_thumb.", ".")
                original_path = images_dir / original_name
                if original_path.exists():
                    thumb_path = generate_thumbnail(original_path)
                    if thumb_path:
                        file_path = thumb_path
        else:
            file_path = images_dir / filename

        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(path=str(file_path), filename=filename, media_type="image/*")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving image file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/generate-thumbnails")
async def generate_all_thumbnails():
    """Generate thumbnails for all images in the static/images directory"""
    try:
        images_dir = Path("static/images")
        if not images_dir.exists():
            raise HTTPException(status_code=404, detail="Images directory not found")
        
        # Ensure thumbnails directory exists
        ensure_thumbnail_dir()
        
        # Process all images
        processed = []
        errors = []
        
        for file_path in images_dir.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                try:
                    thumb_path = generate_thumbnail(file_path)
                    if thumb_path:
                        processed.append(file_path.name)
                    else:
                        errors.append(f"Failed to generate thumbnail for {file_path.name}")
                except Exception as e:
                    errors.append(f"Error processing {file_path.name}: {str(e)}")
        
        return {
            "success": True,
            "processed": processed,
            "errors": errors
        }
        
    except Exception as e:
        print(f"Error generating thumbnails: {e}")
        raise HTTPException(status_code=500, detail=str(e))
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