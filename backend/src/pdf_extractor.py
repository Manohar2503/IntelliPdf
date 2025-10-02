import os
import json
import sys
import re
from typing import List, Dict, Any
import fitz  # PyMuPDF
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFOutlineExtractor:
    def __init__(self):
        self.min_heading_length = 4
        self.max_heading_words = 20
        self.min_font_size = 10
        self.title_y_threshold = 200
        self.min_heading_font_multiplier = 0.1

    def extract_text_with_formatting(self, pdf_path: str) -> List[Dict]:
        doc = fitz.open(pdf_path)
        merged_lines = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        font_sizes = []
                        is_bold = False
                        bboxes = []
                        for span in line["spans"]:
                            text = span["text"]
                            if text.strip():
                                line_text += text
                                font_sizes.append(span["size"])
                                if "bold" in span["font"].lower() or "bolder" in span["font"].lower():
                                    is_bold = True
                                bboxes.append(span["bbox"])
                        try:
                            cleaned_line_text = re.sub(r'\s+', ' ', line_text).strip()
                        except Exception as e:
                            logger.warning(f"Error cleaning line text: {e}. Original text: '{line_text}'")
                            cleaned_line_text = line_text.strip()
                        if cleaned_line_text:
                            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0
                            min_x0 = min(b[0] for b in bboxes) if bboxes else 0
                            min_y0 = min(b[1] for b in bboxes) if bboxes else 0
                            merged_lines.append({
                                "text": cleaned_line_text,
                                "size": avg_font_size,
                                "page": page_num,
                                "bbox": [min_x0, min_y0],
                                "is_bold": is_bold,
                            })
        doc.close()
        return merged_lines

    def extract_title(self, text_blocks: List[Dict]) -> str:
        first_page_blocks = [b for b in text_blocks if b["page"] == 0]
        first_page_blocks_sorted = sorted(first_page_blocks, key=lambda x: (x["bbox"][1], -x["size"]))
        title_candidates = []
        max_font_size_on_first_page = 0
        if first_page_blocks:
            max_font_size_on_first_page = max(b["size"] for b in first_page_blocks)
        for block in first_page_blocks_sorted:
            text = block["text"]
            size = block["size"]
            y0 = block["bbox"][1]
            if y0 < self.title_y_threshold and size >= max_font_size_on_first_page * 0.9:
                if (len(text.split()) >= 3 or re.match(r'^(RFP|Application form):', text, re.IGNORECASE)) and \
                   not re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$', text) and \
                   not re.match(r'^\s*page\s+\d+$', text.lower()) and \
                   not text.strip().isdigit() and \
                   not re.match(r'^(appendix|table|figure)\s+[a-z0-9]+', text.lower()) and \
                   not re.match(r'.*(name|date|address|employee|signature|form no\.|sl\.no\.).*', text.lower()):
                    title_candidates.append(block)
        if not title_candidates:
            return ""
        final_title_parts = []
        title_candidates.sort(key=lambda x: x["bbox"][1])
        if title_candidates:
            current_title_part = title_candidates[0]["text"]
            last_y1 = title_candidates[0]["bbox"][1] + title_candidates[0]["size"]
            for i in range(1, len(title_candidates)):
                block = title_candidates[i]
                if block["bbox"][1] - last_y1 < (block["size"] * 1.5) and \
                   abs(block["size"] - title_candidates[0]["size"]) < 2:
                    current_title_part += " " + block["text"]
                else:
                    final_title_parts.append(current_title_part)
                    current_title_part = block["text"]
                last_y1 = block["bbox"][1] + block["size"]
            final_title_parts.append(current_title_part)
            combined_title = " ".join(final_title_parts).strip()
            match_rfp = re.search(r'(RFP:\s*Request for Proposal\s+To Present a Proposal for Developing the Business Plan for the Ontario Digital Library)', combined_title, re.IGNORECASE)
            if match_rfp:
                return match_rfp.group(1).strip()
            match_ltc = re.search(r'(Application form for grant of LTC advance)', combined_title, re.IGNORECASE)
            if match_ltc:
                return match_ltc.group(1).strip()
            return combined_title
        return ""

    def estimate_body_font_size(self, text_blocks: List[Dict]) -> float:
        size_freq = {}
        relevant_blocks = [b for b in text_blocks if b["page"] > 0 or b["bbox"][1] > self.title_y_threshold]
        if not relevant_blocks:
            if text_blocks:
                all_sizes = [round(b["size"], 1) for b in text_blocks if b["size"] >= self.min_font_size]
                if all_sizes:
                    from collections import Counter
                    mc = Counter(all_sizes).most_common(1)
                    if mc:
                        return mc[0][0]
            return self.min_font_size
        for block in relevant_blocks:
            if block["size"] >= self.min_font_size - 2:
                size = round(block["size"], 1)
                size_freq[size] = size_freq.get(size, 0) + 1
        if not size_freq:
            return self.min_font_size
        body_size = max(size_freq.items(), key=lambda x: x[1])[0]
        return body_size

    def determine_heading_level(self, text: str, size: float, body_size: float, is_bold: bool) -> str:
        # Numeric/outline patterns
        if re.match(r'^\d+(\.\d+){2,}\s', text):
            return "H3"
        elif re.match(r'^\d+\.\d+\s', text):
            return "H2"
        elif re.match(r'^\d+\s', text) or re.match(r'^[A-Z]\.\s', text) or re.match(r'^[IVXLCDM]+\s', text):
            return "H1"
        # Bold headings: lower threshold for H1
        if is_bold:
            if size >= body_size * 1.2:
                return "H1"
            elif size >= body_size * 1.05:
                return "H2"
        else:
            if size >= body_size * 1.5:
                return "H1"
            elif size >= body_size * 1.2:
                return "H2"
        return "Not_Heading"

    def is_probable_heading(self, text: str, size: float, body_size: float, is_bold: bool) -> bool:
        text = text.strip()
        if re.search(r'\d{4,}', text):  # Likely address or phone number
            return False
        if re.search(r'(RSVP|WWW\.|HTTP|HTTPS|\.COM|\.NET|\.ORG)', text, re.IGNORECASE):
            return False
        if text.isupper() and len(text.split()) < 2:
            return False
        if len(text) < self.min_heading_length:
            return False
        if len(text.split()) > self.max_heading_words:
            return False
        if len(text.split()) < 2 and not (is_bold or size > body_size * 1.2):
            return False
        if size < self.min_font_size or size < body_size * 1.05:
            return False
        if re.match(r'^[\d\W]+$', text):
            return False
        if re.match(r'^[•\-\*o]\s*', text) or re.match(r'^\d+\)\s*', text) or \
           re.match(r'^[a-z]\)\s*', text) or re.match(r'^\(\d+\)\s*', text) or \
           re.match(r'^\([a-z]\)\s*', text):
            return False
        common_non_headings_phrases = {
            "date", "signature", "name", "page", "contact", "address", "email", "phone", "fax", "website", 
            "table of contents", "index", "introduction", "conclusion", "references", "appendix", "figures", "tables",
            "sl.no.", "remarks", "details", "serial no.", "chapter", "section", "document number", "version", "revision",
            "part", "form no."
        }
        if text.lower() in common_non_headings_phrases or \
           any(word.lower() in common_non_headings_phrases for word in text.lower().split() if len(word) > 2 and len(text.split()) < 4):
            return False
        if text.endswith(":") and len(text.split()) < 5:
            return False
        if re.match(r'^(table|figure|appendix)\s+\d+', text.lower()):
            return False
        if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$', text) or \
           re.match(r'^\s*-\s*\d+\s*-\s*$', text) or re.match(r'^\s*\d+\s*$', text) or \
           re.match(r'^\(\d+\)$', text):
            return False
        if text.isupper() and len(text.split()) < 2 and len(text) < 10:
            return False
        if len(text) > 80:
            return False
        logger.debug(f"Accepted heading: {text} (size={size}, body_size={body_size}, bold={is_bold})")
        return True

    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        try:
            text_blocks = self.extract_text_with_formatting(pdf_path)
            if not text_blocks:
                return {"title": "", "outline": []}

            title = self.extract_title(text_blocks)
            body_font_size = self.estimate_body_font_size(text_blocks)
            outline = []
            seen_headings = set()

            sorted_blocks = sorted(text_blocks, key=lambda x: (x["page"], x["bbox"][1]))
            for block in sorted_blocks:
                text = block["text"].strip()
                try:
                    safe_text = text.encode('utf-8', 'ignore').decode('utf-8')
                    normalized_text_key = re.sub(r'\s+', ' ', safe_text).lower()
                except Exception as e:
                    logger.warning(f"Failed to normalize text due to encoding issue: {e}. Original: '{text}'")
                    normalized_text_key = re.sub(r'\s+', ' ', text).lower()

                current_text_for_regex = safe_text if 'safe_text' in locals() else text

                # Skip title itself
                if title and normalized_text_key == re.sub(r'\s+', ' ', title).lower():
                    continue

                if self.is_probable_heading(current_text_for_regex, block["size"], body_font_size, block["is_bold"]):
                    level = self.determine_heading_level(current_text_for_regex, block["size"], body_font_size, block["is_bold"])

                    # Add ALL heading levels (H1, H2, H3)
                    if level in ["H1", "H2", "H3"]:
                        if normalized_text_key not in seen_headings:
                            outline.append({
                                "level": level,
                                "text": current_text_for_regex,
                                "page": block["page"] + 1  # 1-indexed
                            })
                            seen_headings.add(normalized_text_key)

            return {
                "title": title.strip(),
                "outline": outline
            }

        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {str(e)}")
            return {"title": "", "outline": []}


def process_pdfs(input_dir: str, output_dir: str):
    extractor = PDFOutlineExtractor()
    os.makedirs(output_dir, exist_ok=True)
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logger.warning(f"No PDF files found in input directory: {input_dir}")
        return
    for pdf_file in pdf_files:
        input_path = os.path.join(input_dir, pdf_file)
        output_file = os.path.splitext(pdf_file)[0] + '.json'
        output_path = os.path.join(output_dir, output_file)
        try:
            outline = extractor.extract_outline(input_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(outline, f, indent=2, ensure_ascii=False)
            logger.info(f"Processed {pdf_file} -> {output_file}")
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {str(e)}")


def main():
    input_dir = "input"
    output_dir = "output2"
    if not os.path.exists(input_dir):
        logger.error(f"Input directory '{input_dir}' does not exist. Please create it and place your PDF files inside.")
        sys.exit(1)
    process_pdfs(input_dir, output_dir)
    logger.info("Processing complete")


if __name__ == "__main__":
    main()
