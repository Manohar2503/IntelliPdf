import re
from typing import List
from .text_repair import TextRepair


class StructuralCleaner:
    """Cleans raw PDF/text input into semantic paragraph blocks."""

    def __init__(
        self,
        header_footer_regex: str = r"^\s*(?:\d{1,4}|page\s+\d+(?:\s+of\s+\d+)?)\s*$",
    ):
        self.header_footer_regex = re.compile(header_footer_regex, re.MULTILINE)

    def _remove_headers_footers(self, text: str) -> str:
        text = re.sub(self.header_footer_regex, "", text)
        text = re.sub(r"[-_=]{3,}", "\n", text)
        text = re.sub(r"^\s*(?:copyright|all rights reserved)\b.*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def _dedupe_lines(self, lines: List[str]) -> List[str]:
        seen = set()
        out = []

        for l in lines:
            s = l.strip()
            if not s:
                continue
            if s in seen:
                continue

            seen.add(s)
            out.append(s)

        return out
    def _is_garbage(self, line: str) -> bool:
        if not line.strip():
            return True
        return TextRepair.is_noise(line, threshold=0.55)
    def clean(self, raw_text: str) -> List[str]:
        if not raw_text:
            return []
        t = TextRepair.normalize_text(raw_text)
        t = self._remove_headers_footers(t)
        t = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", t)
        t = re.sub(r"\n{2,}", "\n\n", t)

        lines = [TextRepair.normalize_line(l) for l in t.splitlines()]
        lines = self._remove_garbage_lines(lines)
        lines = [l for l in lines if not self._is_garbage(l)]
        lines = self._dedupe_lines(lines)

        merged_lines = TextRepair.merge_broken_lines(lines)
        merged_text = "\n".join(merged_lines)
        sentences = TextRepair.split_sentences(merged_text)
        clean_sentences = TextRepair.clean_sentences(sentences)

        return TextRepair.paragraphize(clean_sentences, per_paragraph=3)

    def _remove_garbage_lines(self, lines: List[str]) -> List[str]:
        clean = []
        for line in lines:
            if not line or len(line) < 3:
                continue
            alpha = sum(ch.isalpha() for ch in line)
            total = len(line)
            alpha_ratio = alpha / max(total, 1)
            if alpha_ratio < 0.5:
                continue
            if re.search(r"[^\w\s.,;:!?()/%\-'\"]", line):
                continue
            if re.fullmatch(r"[0-9\s./-]+", line):
                continue
            clean.append(line)
        return clean
