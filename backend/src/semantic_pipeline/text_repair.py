import re
import unicodedata
from typing import Iterable, List


class TextRepair:
    """Domain-agnostic text normalization and sentence quality heuristics."""

    _terminal_punct = (".", "!", "?")
    _weak_endings = {
        "and", "or", "to", "of", "in", "for", "the", "a", "an",
        "with", "by", "on", "at", "from", "that", "this", "these",
        "those", "is", "are", "was", "were", "be", "as",
    }

    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\u00A0", " ")
        text = re.sub(r"[\u2000-\u200F\u202A-\u202E]", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)
        text = re.sub(r"([,.;:!?])([^\s])", r"\1 \2", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def normalize_line(line: str) -> str:
        if not line:
            return ""

        line = TextRepair.normalize_text(line)
        line = re.sub(r"[^\w\s.,;:!?()\-/%'\"]", " ", line)
        line = re.sub(r"\s+", " ", line).strip()
        return line

    @staticmethod
    def merge_broken_lines(lines: Iterable[str]) -> List[str]:
        merged: List[str] = []
        buffer = ""

        for raw_line in lines:
            line = TextRepair.normalize_line(raw_line)

            if not line:
                if buffer:
                    merged.append(buffer.strip())
                    buffer = ""
                continue

            if not buffer:
                buffer = line
                continue

            if TextRepair._should_join(buffer, line):
                if buffer.endswith("-"):
                    buffer = buffer[:-1] + line.lstrip()
                else:
                    buffer = f"{buffer} {line}".strip()
            else:
                merged.append(buffer.strip())
                buffer = line

        if buffer:
            merged.append(buffer.strip())

        return merged

    @staticmethod
    def split_sentences(text: str) -> List[str]:
        text = TextRepair.normalize_text(text)
        if not text:
            return []

        parts = re.split(r"(?<=[.!?])\s+", text)
        out: List[str] = []
        for part in parts:
            s = TextRepair.normalize_line(part)
            if not s:
                continue
            if s[-1] not in TextRepair._terminal_punct:
                tokens = s.split()
                if len(tokens) < 10:
                    continue
                last = tokens[-1].strip(".,;:!?").lower()
                if len(last) <= 3 or last in TextRepair._weak_endings:
                    continue
                s = f"{s}."
            out.append(s)
        return out

    @staticmethod
    def sentence_quality(sentence: str) -> float:
        s = sentence.strip()
        if not s:
            return 0.0

        total = len(s)
        alpha = sum(ch.isalpha() for ch in s)
        digits = sum(ch.isdigit() for ch in s)
        symbols = sum(not (ch.isalnum() or ch.isspace() or ch in ".,;:!?()-%/'\"") for ch in s)
        tokens = s.split()

        if len(tokens) < 4:
            return 0.0

        alpha_ratio = alpha / max(total, 1)
        symbol_ratio = symbols / max(total, 1)
        short_ratio = sum(len(t) <= 2 for t in tokens) / max(len(tokens), 1)
        single_char_ratio = sum(len(t) == 1 for t in tokens) / max(len(tokens), 1)
        digit_ratio = digits / max(total, 1)
        alpha_tokens = [t for t in tokens if re.fullmatch(r"[A-Za-z]+", t)]
        low_vowel_ratio = 0.0
        dense_consonant_ratio = 0.0
        if alpha_tokens:
            low_vowel_count = sum(
                1 for t in alpha_tokens
                if len(t) >= 5 and len(re.findall(r"[aeiouAEIOU]", t)) / len(t) < 0.2
            )
            low_vowel_ratio = low_vowel_count / len(alpha_tokens)
            dense_consonants = sum(
                1 for t in alpha_tokens
                if len(t) >= 6 and re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", t.lower())
            )
            dense_consonant_ratio = dense_consonants / len(alpha_tokens)

        score = 1.0
        score -= max(0.0, 0.6 - alpha_ratio) * 1.5
        score -= max(0.0, symbol_ratio - 0.05) * 3.0
        score -= max(0.0, short_ratio - 0.4) * 2.0
        score -= max(0.0, single_char_ratio - 0.05) * 4.0
        score -= max(0.0, digit_ratio - 0.25) * 1.0
        score -= max(0.0, low_vowel_ratio - 0.35) * 1.8
        score -= max(0.0, dense_consonant_ratio - 0.15) * 2.0

        if re.search(r"\b[a-zA-Z](?:\s+[a-zA-Z]){2,}\b", s):
            score -= 0.6

        if re.search(r"(.)\1{4,}", s):
            score -= 0.5

        if s[-1] not in TextRepair._terminal_punct:
            score -= 0.25

        return max(0.0, min(1.0, score))

    @staticmethod
    def is_noise(sentence: str, threshold: float = 0.45) -> bool:
        return TextRepair.sentence_quality(sentence) < threshold

    @staticmethod
    def clean_sentences(sentences: Iterable[str], threshold: float = 0.52) -> List[str]:
        cleaned: List[str] = []
        seen = set()

        for raw in sentences:
            s = TextRepair.normalize_line(raw)
            if not s:
                continue

            if s[-1] not in TextRepair._terminal_punct:
                if len(s.split()) < 10:
                    continue
                s = f"{s}."

            if TextRepair.is_noise(s, threshold=threshold):
                continue

            key = re.sub(r"\W+", " ", s.lower()).strip()
            if not key or key in seen:
                continue

            seen.add(key)
            cleaned.append(s)

        return cleaned

    @staticmethod
    def ensure_complete_sentences(text: str) -> str:
        sentences = TextRepair.clean_sentences(TextRepair.split_sentences(text))
        return " ".join(sentences).strip()

    @staticmethod
    def paragraphize(sentences: List[str], per_paragraph: int = 3) -> List[str]:
        if not sentences:
            return []
        chunks = []
        for i in range(0, len(sentences), max(1, per_paragraph)):
            chunks.append(" ".join(sentences[i:i + per_paragraph]).strip())
        return [c for c in chunks if c]

    @staticmethod
    def _should_join(prev: str, current: str) -> bool:
        prev = prev.strip()
        current = current.strip()
        if not prev or not current:
            return False

        if prev.endswith("-"):
            return True

        if prev.endswith((",", ";", ":", "(", "/")):
            return True

        if prev.endswith(TextRepair._terminal_punct):
            return False

        if current and current[0].islower():
            return True

        if len(current.split()) <= 3:
            return True

        return True
