"""
Research-Grade PDF Image Extractor with OCR + AI Labels
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
import re


class PDFImageExtractor:
    def __init__(self, output_dir: str = "static/images"):
        print("PDFImageExtractor loaded from:", __file__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model = ResNet50(weights="imagenet")

        (self.output_dir / "thumbnails").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    # -------------------------------------------------
    # Utilities
    # -------------------------------------------------
    def get_image_statistics(self, images: List[Dict]) -> Dict:
        if not images:
            return {
            "total_count": 0,
            "total_size_mb": 0,
            "by_format": {},
            "size_distribution": {}
        }
        stats = {
        "total_count": len(images),
        "total_size_mb": sum(img["size_kb"] for img in images) / 1024,
        "by_format": {},
        "size_distribution": {
            "small": 0,
            "medium": 0,
            "large": 0
        }
    }
        for img in images:
            fmt = img.get("format", "unknown")
            stats["by_format"][fmt] = stats["by_format"].get(fmt, 0) + 1

        size_kb = img.get("size_kb", 0)

        if size_kb < 100:
            stats["size_distribution"]["small"] += 1
        elif size_kb < 1024:
            stats["size_distribution"]["medium"] += 1
        else:
            stats["size_distribution"]["large"] += 1
            return stats

    def _get_image_hash(self, image_data: bytes) -> str:
        return hashlib.md5(image_data).hexdigest()

    def _normalize_ocr_text(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # -------------------------------------------------
    # OCR Preprocessing (IMPORTANT)
    # -------------------------------------------------

    def _preprocess_for_ocr(self, img: Image.Image):

        img_np = np.array(img)

        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        gray = cv2.medianBlur(gray, 3)

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            2,
        )

        return thresh

    # -------------------------------------------------
    # Image Processing
    # -------------------------------------------------

    def _process_image(self, image: Image.Image) -> Dict[str, Image.Image]:

        try:
            thumbnail = ImageOps.contain(image, (300, 300))

            img_array = np.array(image)
            processed = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            processed = cv2.detailEnhance(processed)
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)

            processed = Image.fromarray(processed)

            return {
                "thumbnail": thumbnail,
                "processed": processed,
            }

        except Exception as e:
            print("Image processing error:", e)
            return {}

    # -------------------------------------------------
    # Save Image
    # -------------------------------------------------

    def _save_image(self, image_data: bytes, extension: str) -> Tuple[str, Dict[str, str]]:

        image_hash = self._get_image_hash(image_data)
        base_filename = f"{image_hash[:12]}"

        paths = {}

        original_filename = f"{base_filename}.{extension}"
        original_path = str(self.output_dir / original_filename)

        if not os.path.exists(original_path):

            with open(original_path, "wb") as f:
                f.write(image_data)

            try:
                with Image.open(io.BytesIO(image_data)) as img:

                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    variants = self._process_image(img)

                    if "thumbnail" in variants:
                        thumb_filename = f"{base_filename}_thumb.{extension}"
                        thumb_path = str(
                            self.output_dir / "thumbnails" / thumb_filename
                        )
                        variants["thumbnail"].save(thumb_path)
                        paths["thumbnail"] = thumb_path

                    if "processed" in variants:
                        proc_filename = f"{base_filename}_processed.{extension}"
                        proc_path = str(
                            self.output_dir / "processed" / proc_filename
                        )
                        variants["processed"].save(proc_path)
                        paths["processed"] = proc_path

            except Exception as e:
                print("Variant save error:", e)

        paths["original"] = original_path

        return original_filename, paths

    # -------------------------------------------------
    # Image Info + OCR + Classification
    # -------------------------------------------------

    def _get_image_info(self, image_data: bytes) -> Dict:

        try:
            with Image.open(io.BytesIO(image_data)) as img:

                info = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format.lower() if img.format else "unknown",
                    "mode": img.mode,
                    "size_kb": len(image_data) // 1024,
                }

                if img.mode != "RGB":
                    img = img.convert("RGB")

                # ---------------- OCR ----------------
                if img.width * img.height > 50000:

                    try:
                        processed = self._preprocess_for_ocr(img)
                        processed = Image.fromarray(processed)

                        ocr_text = pytesseract.image_to_string(
                            processed,
                            lang="eng",
                            config="--oem 3 --psm 6",
                        )

                        ocr_text = self._normalize_ocr_text(ocr_text)

                        if len(ocr_text.split()) < 5:
                            ocr_text = ""

                        info["ocr_text"] = ocr_text

                    except Exception as e:
                        print("OCR error:", e)
                        info["ocr_text"] = ""

                else:
                    info["ocr_text"] = ""

                # ---------------- Classification ----------------
                try:
                    img_resized = img.resize((224, 224))

                    x = np.expand_dims(np.array(img_resized), axis=0)
                    x = preprocess_input(x)

                    preds = self.model.predict(x, verbose=0)
                    decoded = decode_predictions(preds, top=3)[0]

                    info["ai_labels"] = [
                        {"label": label, "confidence": float(score)}
                        for _, label, score in decoded
                    ]

                except Exception as e:
                    print("Classification error:", e)
                    info["ai_labels"] = []

                return info

        except Exception as e:
            print("Image info error:", e)
            return {}

    # -------------------------------------------------
    # Extract Images
    # -------------------------------------------------

    def extract_images(self, pdf_path: str, min_size_kb: int = 1) -> List[Dict]:

        images = []

        pdf_doc = fitz.open(pdf_path)

        for page_num, page in enumerate(pdf_doc):

            image_list = page.get_images()

            for img in image_list:

                xref = img[0]
                base_image = pdf_doc.extract_image(xref)

                if not base_image:
                    continue

                image_data = base_image["image"]

                if len(image_data) < min_size_kb * 1024:
                    continue

                extension = base_image["ext"].lower()

                filename, paths = self._save_image(image_data, extension)

                image_info = self._get_image_info(image_data)

                images.append(
                    {
                        "page": page_num + 1,
                        "filename": filename,
                        "path": paths.get("original"),
                        "width": image_info.get("width"),
                        "height": image_info.get("height"),
                        "format": image_info.get("format", extension),
                        "size_kb": image_info.get(
                            "size_kb", len(image_data) // 1024
                        ),
                        "ocr_text": image_info.get("ocr_text", ""),
                        "ai_labels": image_info.get("ai_labels", []),
                    }
                )

        pdf_doc.close()

        return images
    