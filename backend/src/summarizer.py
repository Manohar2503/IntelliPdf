"""
FAST Document Summarization Module (CPU friendly + caching)
✅ Student 1-Minute Recap Mode
✅ Removes noisy header/footer lines (names, dept, unit labels)
✅ Removes repeated lines & duplicate bullets
"""

import json
import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import List, Dict

import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline

# ---------------------------
# NLTK Setup
# ---------------------------
def download_nltk_data():
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)

download_nltk_data()


# ---------------------------
# Summarizer Class
# ---------------------------
class DocumentSummarizer:
    def __init__(
        self,
        model_name: str = "sshleifer/distilbart-cnn-12-6",  # ✅ FAST model
        max_chunk_words: int = 450,  # ✅ small chunk => faster
        min_chunk_words: int = 80,
        max_chunks: int = 6,  # ✅ limit chunks so it won't take forever
        cache_path: str = "output/summary_cache.json",
    ):
        self.model_name = model_name
        self.max_chunk_words = max_chunk_words
        self.min_chunk_words = min_chunk_words
        self.max_chunks = max_chunks
        self.cache_path = Path(cache_path)

        # ✅ load model once
        self.summarizer = pipeline("summarization", model=self.model_name)

    # ---------------------------
    # Cache Helpers
    # ---------------------------
    def _make_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _load_cache(self) -> Dict:
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_cache(self, cache: Dict):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    # ---------------------------
    # Cleaning Helpers (IMPORTANT)
    # ---------------------------
    def _normalize_line(self, line: str) -> str:
        line = line.strip()
        line = re.sub(r"\s+", " ", line)
        line = re.sub(r"^[•\-–—]+", "", line).strip()
        return line.lower()

    def _is_noise_line(self, line: str) -> bool:
        """
        Filter out repeated headers, footers, author names, dept, unit labels, etc.
        """
        l = line.lower().strip()

        if not l:
            return True

        # too short
        if len(l) < 4:
            return True

        # mostly numbers/symbols
        if re.fullmatch(r"[\d\W_]+", l):
            return True

        # ✅ common PDF header/footer noise keywords
        noise_patterns = [
            "asst.", "assistant professor",
            "dept", "department",
            "civil engineering",
            "college",
            "university",
            "unit-", "unit -", "unit iii", "unit-iii",
            "mirza", "mahaboob", "baig",
            "page", "copyright",
        ]

        if any(p in l for p in noise_patterns):
            return True

        # garbage OCR patterns
        if "www." in l or "http" in l:
            return True

        return False

    def _clean_full_text(self, text: str) -> str:
        """
        Remove noisy lines & repeated lines.
        This is the MAIN improvement that fixes bad summaries.
        """
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        # 1) remove obvious noise
        filtered = [ln for ln in lines if not self._is_noise_line(ln)]
        if not filtered:
            return ""

        # 2) remove repeated lines (likely header/footer)
        normalized = [self._normalize_line(ln) for ln in filtered]
        counts = Counter(normalized)

        cleaned_lines = []
        for ln in filtered:
            n = self._normalize_line(ln)
            # if line repeats many times => header/footer
            if counts[n] >= 4:  # ✅ tune: 3/4/5 based on PDFs
                continue
            cleaned_lines.append(ln)

        # 3) final join
        return "\n".join(cleaned_lines).strip()

    def _clean_headings(self, headings: List[str]) -> List[str]:
        """
        Remove junk headings & duplicates.
        """
        cleaned = []
        seen = set()

        for h in headings:
            hh = (h or "").strip()
            if not hh:
                continue

            if self._is_noise_line(hh):
                continue

            # remove very long heading-like fragments
            if len(hh.split()) > 12:
                continue

            key = self._normalize_line(hh)
            if key in seen:
                continue
            seen.add(key)

            cleaned.append(hh)

        return cleaned

    # ---------------------------
    # Chunking
    # ---------------------------
    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Split text into word-limited chunks using sentence boundaries.
        """
        sentences = sent_tokenize(text)
        chunks = []
        current = []
        word_count = 0

        for s in sentences:
            w = len(s.split())
            if word_count + w > self.max_chunk_words:
                if current:
                    chunks.append(" ".join(current).strip())
                current = [s]
                word_count = w
            else:
                current.append(s)
                word_count += w

        if current:
            chunks.append(" ".join(current).strip())

        return chunks[: self.max_chunks]

    # ---------------------------
    # Output Formatting
    # ---------------------------
    def _format_as_bullets(self, text: str, max_bullets: int = 6) -> str:
        """
        Convert summary into student-friendly bullets.
        Removes duplicate bullets.
        """
        sents = sent_tokenize(text)
        sents = [s.strip() for s in sents if len(s.split()) >= 6]

        bullets = []
        seen = set()

        for s in sents:
            key = self._normalize_line(s)
            if key in seen:
                continue
            seen.add(key)

            bullets.append(f"• {s}")
            if len(bullets) >= max_bullets:
                break

        return "\n".join(bullets) if bullets else text.strip()

    # ---------------------------
    # Summarization Core
    # ---------------------------
    def _summarize_text(self, text: str) -> str:
        """
        Summarize a text chunk.
        """
        words = len(text.split())
        if words < self.min_chunk_words:
            return text.strip()

        # ✅ dynamic max/min based on chunk length
        max_len = min(140, max(60, int(words * 0.35)))
        min_len = min(50, max_len - 10)

        out = self.summarizer(
            text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False,
            truncation=True,
        )
        return out[0]["summary_text"].strip()

    # ---------------------------
    # Main Summarize Function
    # ---------------------------
    def summarize_document(self, sections: List[Dict]) -> Dict[str, str]:
        """
        sections: list of sections from current_doc.json
        Each section has: heading, page_number, content, embedding
        """
        all_text_parts = []
        headings = []

        # collect text + headings
        for sec in sections:
            content = (sec.get("content") or "").strip()
            heading = (sec.get("heading") or "").strip()

            if content:
                all_text_parts.append(content)
            if heading:
                headings.append(heading)

        # join with newlines so cleaning works better
        full_text = "\n".join(all_text_parts).strip()
        full_text = self._clean_full_text(full_text)

        if not full_text:
            return {
                "brief_summary": "Document is empty or no useful text found.",
                "detailed_summary": "",
                "section_summaries": [],
            }

        # ✅ Cache check
        cache = self._load_cache()
        key = self._make_cache_key(full_text)

        if key in cache:
            return cache[key]

        # ✅ Clean headings too
        headings = self._clean_headings(headings)

        # ✅ Summarize chunks
        chunks = self._split_into_chunks(full_text)
        chunk_summaries = []

        for chunk in chunks:
            chunk_summaries.append(self._summarize_text(chunk))

        # ✅ Final summaries (Student recap mode)
        combined = " ".join(chunk_summaries).strip()

        brief_summary_text = self._summarize_text(combined) if combined else ""
        brief_summary = self._format_as_bullets(brief_summary_text, max_bullets=6)

        detailed_summary = self._format_as_bullets(combined, max_bullets=12)

        # ✅ keep section list only (clean headings)
        section_list = []
        for h in headings[:6]:
            section_list.append({"heading": h})

        result = {
            "brief_summary": brief_summary,
            "detailed_summary": detailed_summary,
            "section_summaries": section_list,
        }

        # ✅ Save cache
        cache[key] = result
        self._save_cache(cache)

        return result

    # ---------------------------
    # Frontend Initial Message
    # ---------------------------
    def generate_initial_message(self, summary_data: Dict[str, str]) -> str:
        brief = summary_data.get("brief_summary", "")
        sections = summary_data.get("section_summaries", [])

        msg = "🎓 **1-Minute PDF Recap Ready!**\n\n"
        msg += "**Main Points:**\n"
        msg += brief + "\n\n"

        if sections:
            msg += "**Topics Covered:**\n"
            for s in sections:
                msg += f"• {s['heading']}\n"

        msg += "\n✅ Now ask any question from this PDF!"
        return msg
