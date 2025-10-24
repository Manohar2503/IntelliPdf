"""
Module for extracting and processing images from PDF documents with OCR and analysis capabilities
"""
import fitz
import os
from pathlib import Path
import hashlib
from typing import List, Dict, Tuple
from PIL import Image, ImageOps
import io
import pytesseract
import numpy as np
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
import cv2

class PDFImageExtractor:
    def __init__(self, output_dir: str = "static/images"):
        """
        Initialize the PDF image extractor with OCR and image analysis capabilities
        
        Args:
            output_dir: Directory to save extracted images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ResNet model for image classification
        self.model = ResNet50(weights='imagenet')
        
        # Create subdirectories for processed images
        (self.output_dir / "thumbnails").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)
        
    def _get_image_hash(self, image_data: bytes) -> str:
        """Generate a hash for image data to avoid duplicates"""
        return hashlib.md5(image_data).hexdigest()
    
    def _process_image(self, image: Image.Image) -> Dict[str, Image.Image]:
        """Process image to create variants"""
        try:
            # Create thumbnail
            thumbnail = ImageOps.contain(image, (300, 300))
            
            # Create processed version (enhanced)
            img_array = np.array(image)
            processed = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Basic enhancement
            processed = cv2.detailEnhance(processed)
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            processed = Image.fromarray(processed)
            
            return {
                "thumbnail": thumbnail,
                "processed": processed
            }
        except Exception as e:
            print(f"Error processing image: {e}")
            return {}

    def _save_image(self, image_data: bytes, extension: str) -> Tuple[str, Dict[str, str]]:
        """
        Save image data and its processed variants
        
        Returns:
            Tuple of (filename, dict of paths)
        """
        image_hash = self._get_image_hash(image_data)
        base_filename = f"{image_hash[:12]}"
        
        paths = {}
        
        # Save original
        original_filename = f"{base_filename}.{extension}"
        original_path = str(self.output_dir / original_filename)
        
        if not os.path.exists(original_path):
            # Save original
            with open(original_path, "wb") as f:
                f.write(image_data)
            
            # Process and save variants
            try:
                with Image.open(io.BytesIO(image_data)) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    variants = self._process_image(img)
                    
                    # Save thumbnail
                    if "thumbnail" in variants:
                        thumb_filename = f"{base_filename}_thumb.{extension}"
                        thumb_path = str(self.output_dir / "thumbnails" / thumb_filename)
                        variants["thumbnail"].save(thumb_path)
                        paths["thumbnail"] = thumb_path
                    
                    # Save processed
                    if "processed" in variants:
                        proc_filename = f"{base_filename}_processed.{extension}"
                        proc_path = str(self.output_dir / "processed" / proc_filename)
                        variants["processed"].save(proc_path)
                        paths["processed"] = proc_path
            except Exception as e:
                print(f"Error saving variants: {e}")
        
        paths["original"] = original_path
        return original_filename, paths
    
    def _get_image_info(self, image_data: bytes) -> Dict:
        """Get image metadata, OCR text, and AI analysis"""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Basic metadata
                info = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format.lower(),
                    "mode": img.mode,
                    "size_kb": len(image_data) // 1024
                }
                
                # Create numpy array for analysis
                img_array = np.array(img)
                
                # Perform OCR if image is large enough
                if img.width >= 100 and img.height >= 100:
                    try:
                        ocr_text = pytesseract.image_to_string(img)
                        info["ocr_text"] = ocr_text.strip()
                    except Exception as e:
                        print(f"OCR error: {e}")
                        info["ocr_text"] = ""
                
                # Perform image classification
                try:
                    # Convert to RGB if necessary
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    # Resize for ResNet
                    img_resized = img.resize((224, 224))
                    x = np.expand_dims(np.array(img_resized), axis=0)
                    x = preprocess_input(x)
                    
                    # Get predictions
                    preds = self.model.predict(x)
                    decoded = decode_predictions(preds, top=3)[0]
                    
                    # Format predictions
                    info["ai_labels"] = [
                        {"label": label, "confidence": float(score)}
                        for _, label, score in decoded
                    ]
                except Exception as e:
                    print(f"Classification error: {e}")
                    info["ai_labels"] = []
                
                return info
        except Exception as e:
            print(f"Error getting image info: {e}")
            return {}

    def extract_images(self, pdf_path: str, min_size_kb: int = 1) -> List[Dict]:
        """
        Extract images from PDF document
        
        Args:
            pdf_path: Path to PDF file
            min_size_kb: Minimum image size in KB to extract (filters out tiny images)
            
        Returns:
            List of dicts containing image information:
            {
                "page": page number,
                "filename": saved filename,
                "path": full path to saved file,
                "width": image width,
                "height": image height,
                "format": image format (jpeg, png, etc),
                "size_kb": file size in KB
            }
        """
        images = []
        pdf_doc = fitz.open(pdf_path)
        
        for page_num, page in enumerate(pdf_doc):
            # Get images from page
            image_list = page.get_images()
            
            for img_idx, img in enumerate(image_list):
                # Get reference to image in PDF
                xref = img[0]
                base_image = pdf_doc.extract_image(xref)
                
                if base_image:
                    image_data = base_image["image"]
                    
                    # Skip if image is too small
                    if len(image_data) < min_size_kb * 1024:
                        continue
                        
                    # Get image format
                    extension = base_image["ext"].lower()
                    
                    # Save image and get info
                    filename, full_path = self._save_image(image_data, extension)
                    image_info = self._get_image_info(image_data)
                    
                    # Add to results
                    images.append({
                        "page": page_num + 1,
                        "filename": filename,
                        "path": full_path,
                        "width": image_info.get("width"),
                        "height": image_info.get("height"),
                        "format": image_info.get("format", extension),
                        "size_kb": image_info.get("size_kb", len(image_data) // 1024)
                    })
        
        pdf_doc.close()
        return images

    def get_image_statistics(self, images: List[Dict]) -> Dict:
        """
        Get statistics about extracted images
        
        Returns:
            Dict with statistics about the images
        """
        if not images:
            return {
                "total_count": 0,
                "total_size_mb": 0,
                "by_format": {},
                "size_distribution": {
                    "small": 0,  # < 100KB
                    "medium": 0,  # 100KB - 1MB
                    "large": 0   # > 1MB
                }
            }
            
        # Calculate statistics
        stats = {
            "total_count": len(images),
            "total_size_mb": sum(img["size_kb"] for img in images) / 1024,
            "by_format": {},
            "size_distribution": {
                "small": 0,  # < 100KB
                "medium": 0,  # 100KB - 1MB
                "large": 0   # > 1MB
            }
        }
        
        # Count by format
        for img in images:
            fmt = img["format"]
            stats["by_format"][fmt] = stats["by_format"].get(fmt, 0) + 1
            
            # Size distribution
            size_kb = img["size_kb"]
            if size_kb < 100:
                stats["size_distribution"]["small"] += 1
            elif size_kb < 1024:
                stats["size_distribution"]["medium"] += 1
            else:
                stats["size_distribution"]["large"] += 1
                
        return stats