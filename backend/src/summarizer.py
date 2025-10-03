"""
Enhanced document summarization module with support for large documents
"""

import os
from typing import List, Dict, Optional
from transformers import pipeline
import numpy as np
from nltk.tokenize import sent_tokenize
import nltk
def download_nltk_data():
    """Download required NLTK data"""
    try:
        # Try to find the punkt tokenizer
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading required NLTK data...")
        # Download punkt tokenizer data
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        print("NLTK data downloaded successfully")

# Download required NLTK data at module initialization
download_nltk_data()

class DocumentSummarizer:
    def __init__(
        self,
        model_name: str = "t5-small",  # Changed to t5-small which is much smaller (~242MB)
        max_chunk_length: int = 512,
        min_chunk_length: int = 50,
        overlap_length: int = 25
    ):
        """
        Initialize the document summarizer
        
        Args:
            model_name: The name of the summarization model to use
            max_chunk_length: Maximum token length for each chunk
            min_chunk_length: Minimum token length for each chunk
            overlap_length: Number of tokens to overlap between chunks
        """
        self.summarizer = pipeline("summarization", model=model_name)
        self.max_chunk_length = max_chunk_length
        self.min_chunk_length = min_chunk_length
        self.overlap_length = overlap_length

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split long text into smaller chunks with overlap"""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > self.max_chunk_length:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    # Keep last few sentences for overlap
                    overlap_sentences = current_chunk[-2:]  # Keep last 2 sentences
                    current_chunk = overlap_sentences + [sentence]
                    current_length = sum(len(s.split()) for s in current_chunk)
                else:
                    # If a single sentence is too long, split it
                    chunks.append(sentence[:self.max_chunk_length])
                    current_chunk = []
                    current_length = 0
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def _summarize_chunk(self, text: str, ratio: float = 0.3) -> str:
        """Summarize a single chunk of text"""
        try:
            max_length = max(int(len(text.split()) * ratio), self.min_chunk_length)
            min_length = min(self.min_chunk_length, max_length - 50)
            
            summary = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            summary_text = summary[0]["summary_text"]
            print(f"\nChunk Summary:\n{summary_text}\n")
            return summary_text
        except Exception as e:
            print(f"Error summarizing chunk: {str(e)}")
            return text[:self.max_chunk_length]  # Fallback to truncation

    def summarize_document(
        self,
        sections: List[Dict],
        hierarchical: bool = True
    ) -> Dict[str, str]:
        # Ensure NLTK data is available
        download_nltk_data()
        print("\n=== Starting Document Summarization ===\n")
        """
        Generate both detailed and concise summaries for a document
        
        Args:
            sections: List of document sections with text content
            hierarchical: Whether to generate hierarchical summaries
        
        Returns:
            Dict containing different types of summaries
        """
        # Combine all section texts
        full_text = ""
        section_summaries = []
        
        for section in sections:
            section_text = section.get("text", "").strip()
            if not section_text:
                continue
                
            # Generate section summary
            if hierarchical:
                section_summary = self._summarize_chunk(section_text)
                section_summaries.append({
                    "heading": section.get("heading", "Untitled Section"),
                    "summary": section_summary
                })
            
            full_text += section_text + " "

        # Split and summarize the full document
        chunks = self._split_into_chunks(full_text)
        chunk_summaries = []
        
        for chunk in chunks:
            if len(chunk.strip()) > self.min_chunk_length:
                summary = self._summarize_chunk(chunk)
                chunk_summaries.append(summary)

        # Create final summary from chunk summaries
        if chunk_summaries:
            final_summary = self._summarize_chunk(
                " ".join(chunk_summaries),
                ratio=0.5
            )
        else:
            final_summary = "Could not generate summary. Document may be empty or too short."

        return {
            "brief_summary": final_summary,
            "detailed_summary": " ".join(chunk_summaries),
            "section_summaries": section_summaries if hierarchical else []
        }

    def generate_initial_message(self, summary_data: Dict[str, str]) -> str:
        """Generate the initial chatbot message with document summary"""
        brief = summary_data["brief_summary"]
        sections = summary_data.get("section_summaries", [])
        
        message = "👋 I've analyzed the document. Here's a brief summary:\n\n"
        message += brief + "\n\n"
        
        if sections:
            message += "The document contains the following main sections:\n"
            for section in sections[:5]:  # Show top 5 sections
                message += f"• {section['heading']}\n"
            
            if len(sections) > 5:
                message += f"...and {len(sections) - 5} more sections.\n"
                
        message += "\nYou can ask me specific questions about any part of the document!"
        
        return message