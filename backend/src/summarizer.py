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
        # Download punkt tokenizer data
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)

# Download required NLTK data at module initialization
download_nltk_data()

class DocumentSummarizer:
    def __init__(
        self,
        model_name: str = "facebook/bart-large-cnn",  # Changed to BART for better summarization
        max_chunk_length: int = 1024,  # Increased chunk size
        min_chunk_length: int = 100,
        overlap_length: int = 50,
        compression_ratio: float = 0.2  # Added compression ratio for more concise summaries
    ):
        """
        Initialize the document summarizer
        
        Args:
            model_name: The name of the summarization model to use
            max_chunk_length: Maximum token length for each chunk
            min_chunk_length: Minimum token length for each chunk
            overlap_length: Number of tokens to overlap between chunks
            compression_ratio: Target ratio for summary length compared to original
        """
        self.summarizer = pipeline("summarization", model=model_name)
        self.max_chunk_length = max_chunk_length
        self.min_chunk_length = min_chunk_length
        self.overlap_length = overlap_length
        self.compression_ratio = compression_ratio

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

    def _format_as_bullets(self, text: str) -> str:
        """Format text as bullet points"""
        sentences = sent_tokenize(text)
        # Filter out very short sentences or incomplete ones
        valid_sentences = [s.strip() for s in sentences if len(s.split()) > 5 and s.strip().endswith(('.', '!', '?'))]
        
        # Convert sentences to bullet points
        bullet_points = []
        current_point = []
        
        for sentence in valid_sentences:
            current_point.append(sentence)
            if len(' '.join(current_point).split()) >= 20:  # Aim for reasonable bullet point length
                bullet_points.append('• ' + ' '.join(current_point))
                current_point = []
                
        if current_point:  # Add any remaining sentences
            bullet_points.append('• ' + ' '.join(current_point))
            
        return '\n'.join(bullet_points)

    def _summarize_chunk(self, text: str, ratio: float = None) -> str:
        """Summarize a single chunk of text"""
        try:
            ratio = ratio or self.compression_ratio
            text_length = len(text.split())
            max_length = max(int(text_length * ratio), self.min_chunk_length)
            min_length = min(self.min_chunk_length, max_length - 50)
            
            summary = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            summary_text = summary[0]["summary_text"]
            return summary_text
        except Exception as e:
            print(f"Summarization error: {str(e)}")
            return text[:self.max_chunk_length]  # Fallback to truncation

    def summarize_document(
        self,
        sections: List[Dict],
        hierarchical: bool = True
    ) -> Dict[str, str]:
        # Ensure NLTK data is available
        download_nltk_data()
        """
        Generate both detailed and concise summaries for a document
        
        Args:
            sections: List of document sections with text content
            hierarchical: Whether to generate hierarchical summaries
        
        Returns:
            Dict containing different types of summaries
        """
        print("\nStarting document summarization...")
        
        # Group sections by importance/type
        main_sections = []
        supplementary_sections = []
        
        for section in sections:
            section_text = section.get("content", "").strip()
            if not section_text:
                continue
                
            # Determine section importance by length and position
            if len(section_text.split()) > 200:  # Consider longer sections as main content
                main_sections.append(section)
            else:
                supplementary_sections.append(section)
        
        # Process main sections first
        main_summaries = []
        section_summaries = []
        all_text = ""
        
        print(f"\nProcessing {len(main_sections)} main sections...")
        for section in main_sections:
            section_text = section.get("content", "").strip()
            all_text += section_text + " "
            
            if hierarchical:
                # Create more concise section summaries
                section_summary = self._summarize_chunk(section_text, ratio=0.15)  # More aggressive summarization
                formatted_summary = self._format_as_bullets(section_summary)
                main_summaries.append(section_summary)
                section_summaries.append({
                    "heading": section.get("heading", "Untitled Section"),
                    "summary": formatted_summary
                })
        
        # Add supplementary sections if needed
        if supplementary_sections:
            print(f"\nProcessing {len(supplementary_sections)} supplementary sections...")
            for section in supplementary_sections:
                section_text = section.get("content", "").strip()
                if len(section_text.split()) > 50:  # Only include substantial sections
                    all_text += section_text + " "

        # Split and summarize the full document
        print("\nGenerating document-level summary...")
        chunks = self._split_into_chunks(all_text)
        chunk_summaries = []
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) > self.min_chunk_length:
                print(f"Processing chunk {i+1}/{len(chunks)}...")
                summary = self._summarize_chunk(chunk, ratio=0.2)  # More aggressive summarization
                chunk_summaries.append(summary)

        # Create final summary from chunk summaries
        if chunk_summaries:
            # First get a concise summary
            intermediate_summary = self._summarize_chunk(
                " ".join(chunk_summaries),
                ratio=0.3
            )
            # Then format as bullet points
            final_summary = self._format_as_bullets(intermediate_summary)
        else:
            final_summary = "Could not generate summary. Document may be empty or too short."

        # Create a more detailed summary but still in bullet points
        detailed_summary = self._format_as_bullets(" ".join(chunk_summaries)) if chunk_summaries else ""

        print("\nSummarization complete!")
        return {
            "brief_summary": final_summary,
            "detailed_summary": detailed_summary,
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
