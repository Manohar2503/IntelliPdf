from typing import List, Dict
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor
from .text_repair import TextRepair


class AbstractiveSummarizer:

    def __init__(
        self,
        distilbart_model: str = "sshleifer/distilbart-cnn-12-6",
        pegasus_model: str = "google/pegasus-xsum",
    ):
        self.distilbart_model = distilbart_model
        self.pegasus_model = pegasus_model

        self._distilbart = None
        self._pegasus = None

    def _get_distilbart(self):
        if self._distilbart is None:
            self._distilbart = pipeline(
                "summarization",
                model=self.distilbart_model,
                device=-1,
            )
        return self._distilbart

    def _get_pegasus(self):
        if self._pegasus is None:
            self._pegasus = pipeline(
                "summarization",
                model=self.pegasus_model,
                device=-1,
            )
        return self._pegasus

    def _clean_text(self, text: str) -> str:
        lines = [TextRepair.normalize_line(line) for line in text.split("\n")]
        lines = [line for line in lines if line and not TextRepair.is_noise(line, threshold=0.55)]
        merged = TextRepair.merge_broken_lines(lines)
        cleaned = TextRepair.ensure_complete_sentences(" ".join(merged))
        return cleaned

    def _repair_summary(self, text: str) -> str:
        text = TextRepair.normalize_text(text)
        sentences = TextRepair.clean_sentences(TextRepair.split_sentences(text))
        return " ".join(sentences).strip()

    def _get_lengths(self, text: str):

        words = len(text.split())
        sentences = max(1, len(TextRepair.split_sentences(text)))

        max_len = int(words * 0.5)
        min_len = int(words * 0.25)

        max_len = max(48, min(max_len, 220))
        min_len = max(20, min(min_len, max_len - 12))
        min_len = max(min_len, min(35, sentences * 8))

        return max_len, min_len

    def _safe_fallback(self, text: str, max_words: int = 120) -> str:
        sents = TextRepair.clean_sentences(TextRepair.split_sentences(text))
        if not sents:
            return ""
        out = []
        count = 0
        for sent in sents:
            sent_len = len(sent.split())
            if count + sent_len > max_words and out:
                break
            out.append(sent)
            count += sent_len
        return " ".join(out).strip()

    def summarize_chunk(self, text: str, use_pegasus: bool = False) -> Dict[str, str]:

        results = {}

        text = self._clean_text(text)

        if len(text.split()) < 45:
            results["distilbart"] = self._safe_fallback(text, max_words=90)
            return results

        max_len, min_len = self._get_lengths(text)

        model = self._get_distilbart()

        out = model(
            text,
            max_length=max_len,
            min_length=min_len,
            num_beams=4,
            length_penalty=1.0,
            repetition_penalty=1.15,
            early_stopping=True,
            do_sample=False,
            truncation=True,
        )

        summary = out[0]["summary_text"].strip()
        summary = self._repair_summary(summary)
        if len(summary.split()) < 12:
            summary = self._safe_fallback(text, max_words=max_len)

        results["distilbart"] = summary

        if use_pegasus:

            model2 = self._get_pegasus()

            out2 = model2(
                text,
                max_length=max_len,
                min_length=min_len,
                num_beams=4,
                length_penalty=1.0,
                repetition_penalty=1.1,
                early_stopping=True,
                do_sample=False,
                truncation=True,
            )

            summary2 = out2[0]["summary_text"].strip()
            summary2 = self._repair_summary(summary2)
            if len(summary2.split()) < 12:
                summary2 = self._safe_fallback(text, max_words=max_len)

            results["pegasus"] = summary2

        return results

    def summarize_parallel(
        self,
        chunks: List[str],
        use_pegasus: bool = False,
        max_workers: int = 2
    ) -> List[Dict[str, str]]:

        if not chunks:
            return []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            futures = [
                executor.submit(
                    self.summarize_chunk,
                    chunk,
                    use_pegasus
                )
                for chunk in chunks
            ]

            return [f.result() for f in futures]
