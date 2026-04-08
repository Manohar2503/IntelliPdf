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
import math
from typing import Optional
import numpy as np

import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline

from src import images

# Import the hybrid semantic pipeline. Try package path first (when running as 'src' package),
# then fall back to local import if necessary. This ensures imports work with uvicorn from `backend/`.
try:
    from src.semantic_pipeline.pipeline import HybridSummarizationPipeline
    HYBRID_PIPELINE_AVAILABLE = True
    print("[INFO] ✅ HybridSummarizationPipeline imported from src.semantic_pipeline")
except Exception as e_src:
    # Fallback: try local package name (useful for direct script runs)
    try:
        from semantic_pipeline.pipeline import HybridSummarizationPipeline
        HYBRID_PIPELINE_AVAILABLE = True
        print("[INFO] ✅ HybridSummarizationPipeline imported from semantic_pipeline (fallback)")
    except Exception as e_local:
        HYBRID_PIPELINE_AVAILABLE = False
        print(f"[ERROR] Failed to import HybridSummarizationPipeline (src: {e_src}; fallback: {e_local})")
        import traceback
        traceback.print_exc()

# ---------------------------
# NLTK Setup
# ---------------------------
def download_nltk_data():
    try:
        nltk.data.find("tokenizers/punkt")
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("punkt", quiet=True)
        nltk.download("stopwords", quiet=True)

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
        max_chunks: int = 10,  # ✅ limit chunks so it won't take forever
        cache_path: str = "output/summary_cache.json",
        use_extractive_guidance: bool = True,
        extract_top_k: int = 6,
        # Ensemble / semantic options
        use_ensemble: bool = False,
        abstractive_model_name: Optional[str] = "google/pegasus-xsum",
        use_semantic_scoring: bool = True,
        semantic_top_k: int = 6,
        # Hybrid pipeline option
        use_hybrid_pipeline: bool = False,
    ):
        self.model_name = model_name
        self.max_chunk_words = max_chunk_words
        self.min_chunk_words = min_chunk_words
        self.max_chunks = max_chunks
        self.cache_path = Path(cache_path)
        self.use_extractive_guidance = use_extractive_guidance
        self.extract_top_k = extract_top_k
        self.use_ensemble = use_ensemble
        self.abstractive_model_name = abstractive_model_name
        self.use_semantic_scoring = use_semantic_scoring
        self.semantic_top_k = semantic_top_k
        self.use_hybrid_pipeline = use_hybrid_pipeline and HYBRID_PIPELINE_AVAILABLE

        # ✅ Initialize hybrid pipeline if enabled
        self.hybrid_pipeline = None
        if self.use_hybrid_pipeline:
            try:
                self.hybrid_pipeline = HybridSummarizationPipeline()
            except Exception as e:
                print(f"Warning: could not initialize hybrid pipeline: {e}")
                self.use_hybrid_pipeline = False

        # ✅ load model once
        self.summarizer = pipeline("summarization", model=self.model_name)

        # ✅ stopwords for simple keyphrase / extractive scoring
        try:
            self.stopwords = set(nltk.corpus.stopwords.words("english"))
        except Exception:
            self.stopwords = set()

        # optional embedding model for semantic scoring
        self.embedding_model = None
        try:
            from sentence_transformers import SentenceTransformer

            # lightweight model suggestion; user can change if installed
            try:
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.embedding_model = None
        except Exception:
            self.embedding_model = None

        # optional additional abstractive model for ensemble
        self.abstractive_summarizer = None
        if self.use_ensemble and self.abstractive_model_name:
            try:
                # Only load if different from primary to avoid duplicate loads
                if self.abstractive_model_name != self.model_name:
                    self.abstractive_summarizer = pipeline(
                        "summarization", model=self.abstractive_model_name
                    )
                else:
                    self.abstractive_summarizer = self.summarizer
            except Exception:
                self.abstractive_summarizer = None

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

        # metadata/header prefixes
        if re.match(r"^\s*(subject|ref|reference|file|date|no)\s*[:\-]", l):
            return True

        # common document id/date patterns
        if re.search(r"\b\d{1,4}[-/]\d{1,4}(?:[-/]\d{2,4})?(?:\([a-z0-9\-]+\))?\b", l):
            if len(l.split()) <= 10:
                return True
        if re.search(r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})\b", l):
            if len(l.split()) <= 10:
                return True

        # lines dominated by digits/symbols
        total = max(1, len(l))
        digits = sum(ch.isdigit() for ch in l)
        symbols = sum(not (ch.isalnum() or ch.isspace()) for ch in l)
        if (digits + symbols) / total > 0.45:
            return True

        # ✅ common PDF header/footer noise keywords (more specific patterns)
        # Only filter lines that are JUST these keywords, not content about them
        exact_noise_patterns = [
            "asst. professor",
            "assistant professor",
            "dept of",
            "department of",
            "college of",
            "university of",
        ]
        
        # Check for exact patterns (case-insensitive)
        for pattern in exact_noise_patterns:
            if l == pattern or l.startswith(pattern + ":") or l.startswith(pattern + " "):
                return True
        
        # Filter lines that are ONLY author/dept info (short lines with specific keywords)
        if len(l.split()) <= 5:  # Short line
            if any(keyword in l for keyword in ["asst.", "professor", "dept", "department", "civil engineering", "college", "university"]):
                # But NOT if it's a content line starting with these keywords (like "Building" sections)
                if len(l) > 50:  # If it's longer, likely content
                    return False
                if l.startswith(("building", "unit", "chapter", "section", "part", "module")):
                    return False  # Keep content sections
                return True

        # garbage OCR patterns
        if "www." in l or "http" in l:
            return True

        return False

    def _is_noisy_sentence(self, sentence: str) -> bool:
        s = (sentence or "").strip()
        if not s:
            return True
        if len(s.split()) < 6:
            return True
        if self._is_noise_line(s):
            return True
        if re.search(r"(.)\1{4,}", s):
            return True
        alpha_words = [w for w in re.findall(r"\b\w+\b", s) if re.search(r"[A-Za-z]", w)]
        if alpha_words:
            upper = sum(1 for w in alpha_words if len(w) >= 3 and w.isupper())
            if upper / len(alpha_words) > 0.6:
                return True
        if re.search(r"[^\w\s.,;:!?()/%'\"-]{2,}", s):
            return True
        return False

    def _clean_summary_text(self, text: str) -> str:
        try:
            sentences = sent_tokenize(text or "")
        except Exception:
            sentences = re.split(r"(?<=[.!?])\s+", text or "")

        cleaned = []
        seen = set()
        for s in sentences:
            s = re.sub(r"\s+", " ", s).strip()
            if not s or self._is_noisy_sentence(s):
                continue
            if s[-1] not in ".!?":
                s += "."
            if s:
                s = s[0].upper() + s[1:]
            key = re.sub(r"\W+", " ", s.lower()).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            cleaned.append(s)
        return " ".join(cleaned).strip()
    def _combine_text_and_ocr(self, sections, images=None):
        text_parts = []
        for sec in sections:
            content = sec.get("content", "")
            if content:
                text_parts.append(content)
        if images:
            for img in images:
                ocr = img.get("ocr_text", "")
                if ocr and len(ocr) > 20:
                    text_parts.append(ocr)
        return "\n".join(text_parts)

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
    # Extractive helpers
    # ---------------------------
    def _score_and_select_sentences(self, text: str, top_k: int = 6) -> List[str]:
        """
        Score sentences by simple term-frequency importance and return
        the top_k sentences in their original order.
        """
        sents = sent_tokenize(text)
        if not sents:
            return []

        # build term frequencies (normalized words)
        words = []
        for s in sents:
            for w in re.findall(r"\w+", s.lower()):
                if w in self.stopwords or len(w) < 3:
                    continue
                words.append(w)

        tf = Counter(words)
        if not tf:
            return sents[:top_k]

        # score each sentence
        sent_scores = []
        for i, s in enumerate(sents):
            score = 0.0
            for w in re.findall(r"\w+", s.lower()):
                score += tf.get(w, 0)

            # length and position heuristics
            length = len(s.split())
            score = score * (1 + math.log(1 + length))
            pos_weight = 1.0 / (1 + i * 0.1)
            score *= pos_weight

            sent_scores.append((i, score, s))

        # pick top_k by score
        sent_scores.sort(key=lambda x: x[1], reverse=True)
        selected = sorted(sent_scores[:top_k], key=lambda x: x[0])
        return [s for _, __, s in selected]

    def _extract_keyphrases(self, text: str, top_n: int = 6) -> List[str]:
        """
        Simple keyphrase extraction using term-frequency (stopwords removed).
        Returns top_n words/phrases.
        """
        words = [w.lower() for w in re.findall(r"\w+", text) if w.lower() not in self.stopwords and len(w) > 3]
        if not words:
            return []

        ctr = Counter(words)
        return [w for w, _ in ctr.most_common(top_n)]

    # ---------------------------
    # Semantic / embedding helpers
    # ---------------------------
    def _embed_chunks(self, chunks: List[str]):
        """Return numpy embeddings for chunks or None if model missing."""
        if not self.embedding_model:
            return None
        try:
            emb = self.embedding_model.encode(chunks, convert_to_numpy=True)
            return emb
        except Exception:
            return None

    def _select_semantic_chunks(self, chunks: List[str], top_k: int = 4) -> List[str]:
        """
        Select top_k chunks by cosine similarity to document centroid embedding.
        Falls back to extractive TF scoring if embedding model not available.
        """
        if not chunks:
            return []

        emb = self._embed_chunks(chunks)
        if emb is None:
            # fallback: select highest-scoring sentences from whole text
            joined = "\n".join(chunks)
            return self._score_and_select_sentences(joined, top_k=top_k)

        # centroid
        centroid = np.mean(emb, axis=0, keepdims=True)
        # cosine similarities
        sims = (emb @ centroid.T).squeeze() / (
            np.linalg.norm(emb, axis=1) * np.linalg.norm(centroid)
        )
        order = np.argsort(-sims)[:top_k]
        selected = [chunks[i] for i in sorted(order)]
        return selected

    # ---------------------------
    # Chunking for Fast Mode
    # ---------------------------
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into logical chunks for summarization.
        ✅ Respects paragraph boundaries
        ✅ Respects max_chunk_words limit
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_words = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_words = len(para.split())

            # If single paragraph is too long, split it
            if para_words > self.max_chunk_words:
                # Save current chunk
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_words = 0

                # Split long paragraph into sentences
                sents = sent_tokenize(para)
                chunk_sents = []
                chunk_words = 0

                for sent in sents:
                    sent_words = len(sent.split())
                    if chunk_words + sent_words > self.max_chunk_words:
                        if chunk_sents:
                            chunks.append(" ".join(chunk_sents))
                            chunk_sents = []
                            chunk_words = 0
                    chunk_sents.append(sent)
                    chunk_words += sent_words

                if chunk_sents:
                    chunks.append(" ".join(chunk_sents))

            else:
                # Add to current chunk
                if current_words + para_words > self.max_chunk_words:
                    if current_chunk:
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = []
                        current_words = 0

                current_chunk.append(para)
                current_words += para_words

        # Add final chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        # Limit number of chunks
        return chunks[: self.max_chunks]

    def _summarize_chunk(self, chunk: str) -> str:
        """
        Summarize a single chunk using abstractive model.
        Wrapper around _summarize_text for compatibility.
        """
        return self._summarize_text(chunk)

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
        words = len(text.split())
        if words < self.min_chunk_words:
            return text.strip()
        max_len = min(140, max(60, int(words * 0.35)))
        min_len = min(50, max_len - 10)
        input_text = text
        out = self.summarizer(
        input_text,
        max_length=max_len,
        min_length=min_len,
        do_sample=False,
        truncation=True,
    )

        summary = out[0]["summary_text"].strip()

        return summary

    # ---------------------------
    # Main Summarize Function
    # ---------------------------
    def enable_hybrid_pipeline(self):
        """Enable hybrid pipeline mode dynamically"""
        if HYBRID_PIPELINE_AVAILABLE:
            try:
                self.hybrid_pipeline = HybridSummarizationPipeline()
                self.use_hybrid_pipeline = True
                return {"success": True, "message": "Hybrid pipeline enabled"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Hybrid pipeline not available"}

    def disable_hybrid_pipeline(self):
        """Disable hybrid pipeline mode, revert to fast mode"""
        self.use_hybrid_pipeline = False
        self.hybrid_pipeline = None
        return {"success": True, "message": "Hybrid pipeline disabled, using fast mode"}

    def get_hybrid_pipeline_status(self) -> Dict:
        """Get current hybrid pipeline status"""
        return {
            "available": HYBRID_PIPELINE_AVAILABLE,
            "enabled": self.use_hybrid_pipeline,
            "initialized": self.hybrid_pipeline is not None,
        }

    def _summarize_with_hybrid_pipeline(self, full_text: str) -> Dict:
        if not self.hybrid_pipeline:
            raise RuntimeError("Hybrid pipeline not initialized")
        try:
            
            print(f"[DEBUG] Input text length: {len(full_text)} chars")
            extractive = " ".join(
            self._score_and_select_sentences(full_text, top_k=10)
        )
            result = self.hybrid_pipeline.run(full_text)
            final_summary = result.get("final_summary", "")
            extractive = self._clean_summary_text(extractive)
            final_summary = self._clean_summary_text(final_summary)
            final_summary = f"{extractive} {final_summary}".strip()
            final_summary = self._clean_summary_text(final_summary)
            final_summary = self._expand_summary(final_summary, 260)
            final_summary = self._clean_summary_text(final_summary)
            print(f"[DEBUG] Final summary length: {len(final_summary)} chars")
            return {
            "brief_summary": final_summary,
            "detailed_summary": final_summary,
            "section_summaries": [],
            "metrics": result.get("metrics", {}),
        }
        except Exception as e:
            print(f"[ERROR] Hybrid pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            raise


    def summarize_document(self, sections: List[Dict]) -> Dict[str, str]:
        """
        Main summarization method - routes to hybrid or fast mode
        """
        print(f"[DEBUG] summarize_document called with {len(sections)} sections")
        images_data = []
        for sec in sections:
            imgs = sec.get("images", [])
            if imgs:
                images_data.extend(imgs)
        combined = self._combine_text_and_ocr(sections, images_data)
        full_text = self._clean_full_text(combined)

        print(f"[DEBUG] Combined text length (with OCR): {len(full_text)} chars")


        if not full_text:
            print("[WARN] Full text is empty after cleaning")
            return {
                "brief_summary": "Empty document.",
                "detailed_summary": "",
                "section_summaries": [],
            }

        # Use hybrid pipeline if enabled
        print(f"[DEBUG] use_hybrid_pipeline={self.use_hybrid_pipeline}, hybrid_pipeline exists={self.hybrid_pipeline is not None}")
        if self.use_hybrid_pipeline and self.hybrid_pipeline:
            try:
                print("[INFO] Using HYBRID pipeline mode")
                return self._summarize_with_hybrid_pipeline(full_text)
            except Exception as e:
                print(f"[WARN] Hybrid pipeline failed ({e}), falling back to fast mode")
                self.use_hybrid_pipeline = False

        # ✅ FAST MODE: Original summarization logic
        print("Running FAST summarization mode...")
        cache = self._load_cache()
        cache_key = self._make_cache_key(full_text)

        if cache_key in cache:
            return cache[cache_key]

        words = len(full_text.split())
        brief_summary = ""
        section_summaries = []

        # Clean and chunk
        chunks = self._chunk_text(full_text)
        summaries = []

        for chunk in chunks:
            summary = self._summarize_chunk(chunk)
            if summary:
                summaries.append(summary)

        if summaries:
            brief_summary = " ".join(summaries)

        result = {
            "brief_summary": brief_summary,
            "detailed_summary": brief_summary,
            "section_summaries": section_summaries,
        }

        cache[cache_key] = result
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
    def _expand_summary(self, text: str, target_words: int = 240) -> str:
        from nltk.tokenize import sent_tokenize
        words = text.split()
        if len(words) >= target_words:
            return text
        sentences = sent_tokenize(text)
        if not sentences:
            return text
        expanded = sentences.copy()
        idx = 0
        while len(" ".join(expanded).split()) < target_words:
            expanded.append(sentences[idx % len(sentences)])
            idx += 1
        return " ".join(expanded)
