from typing import List, Dict
import re


class OutputGenerator:
    """Converts final summary text into a structured, student-friendly recap."""

    def __init__(self):
        pass

    def _split_into_topics(self, text: str) -> List[str]:
        # Heuristic: split by headings-looking lines (colon or capitalized short lines)
        parts = re.split(r"\n{1,}|(?<=:)\s+", text)
        return [p.strip() for p in parts if p.strip()]

    def generate(self, final_summary: str, headings: List[str] = None) -> Dict:
        topics = self._split_into_topics(final_summary)
        bullets = []
        for t in topics:
            # split into shorter bullet sentences
            items = [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]
            bullets.append(items)

        structured = {
            "recap": [
                {"heading": (headings[i] if headings and i < len(headings) else f"Topic {i+1}"), "bullets": bullets[i]}
                for i in range(len(bullets))
            ]
        }
        return structured
