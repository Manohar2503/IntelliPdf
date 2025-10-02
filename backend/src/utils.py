"""
Utility functions for the document intelligence system
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

def setup_logging() -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_input_config(config_path: Path) -> Dict[str, Any]:
    """Load and validate input configuration"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ['persona', 'job_to_be_done', 'documents']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate persona structure
        if 'role' not in config['persona']:
            raise ValueError("Persona must have a 'role' field")
        
        # Validate job_to_be_done structure
        if 'task' not in config['job_to_be_done']:
            raise ValueError("job_to_be_done must have a 'task' field")
        
        # Validate documents structure
        if not isinstance(config['documents'], list) or not config['documents']:
            raise ValueError("Documents must be a non-empty list")
        
        for doc in config['documents']:
            if 'filename' not in doc:
                raise ValueError("Each document must have a 'filename' field")
        
        return config
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Input configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {str(e)}")

def validate_output_format(output_data: Dict[str, Any]) -> bool:
    """Validate that output matches expected format"""
    required_fields = ['metadata', 'extracted_sections', 'subsection_analysis']
    
    for field in required_fields:
        if field not in output_data:
            return False
    
    # Validate metadata structure
    metadata = output_data['metadata']
    metadata_fields = ['input_documents', 'persona', 'job_to_be_done', 'processing_timestamp']
    for field in metadata_fields:
        if field not in metadata:
            return False
    
    # Validate extracted_sections structure
    for section in output_data['extracted_sections']:
        section_fields = ['document', 'section_title', 'importance_rank', 'page_number']
        for field in section_fields:
            if field not in section:
                return False
    
    # Validate subsection_analysis structure
    for subsection in output_data['subsection_analysis']:
        subsection_fields = ['document', 'refined_text', 'page_number']
        for field in subsection_fields:
            if field not in subsection:
                return False
    
    return True

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to maximum length while preserving word boundaries"""
    if len(text) <= max_length:
        return text
    
    # Find the last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we found a space reasonably close to the end
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."