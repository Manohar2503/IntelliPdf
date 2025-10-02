# Persona-Driven Document Intelligence System

## Adobe "Connecting the Dots" Challenge - Round 1B

This system extracts and ranks relevant sections from PDF documents based on a specific persona and their job-to-be-done.

## Features

- **Offline Processing**: Runs completely offline with no internet access required
- **Fast Performance**: Processes 3-10 PDFs in under 60 seconds
- **CPU-Only**: Works without GPU requirements
- **Lightweight Model**: Uses sentence-transformers model under 1GB
- **Docker Support**: Containerized for AMD64 platform

## Architecture

- **PDF Extraction**: Uses PyMuPDF for fast text extraction and section identification
- **Relevance Ranking**: Uses sentence-transformers (all-MiniLM-L6-v2) for semantic similarity
- **Output Formatting**: Generates structured JSON with metadata, sections, and analysis

## Input Format

Place these files in `/app/input/`:
- `input.json`: Configuration file with persona, job, and document list
- PDF files as specified in the documents array

Example `input.json`:
```json
{
    "persona": {
        "role": "Travel Planner"
    },
    "job_to_be_done": {
        "task": "Plan a trip of 4 days for a group of 10 college friends."
    },
    "documents": [
        {
            "filename": "South of France - Cities.pdf",
            "title": "South of France - Cities"
        }
    ]
}
```

## Output Format

Generated in `/app/output/output.json`:
- **metadata**: Input documents, persona, job, and timestamp
- **extracted_sections**: Top 5 ranked sections with importance ranks
- **subsection_analysis**: Detailed refined text for key sections

## Usage

### Direct Execution
```bash
python main.py
```

### Docker Execution
```bash
# Build the image
docker build -t document-intelligence .

# Run the container
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  document-intelligence
```

## Technical Specifications

- **Model Size**: ~80MB (sentence-transformers all-MiniLM-L6-v2)
- **Processing Time**: <60 seconds for 3-5 documents
- **Memory Usage**: <2GB RAM
- **Platform**: linux/amd64

## Dependencies

- PyMuPDF (PDF processing)
- sentence-transformers (semantic similarity)
- scikit-learn (cosine similarity)
- torch (neural network backend)

See `requirements_doc_intel.txt` for complete list.

## Project Structure

```
/app/
├── main.py              # Entry point
├── src/
│   ├── extract.py       # PDF extraction logic
│   ├── ranker.py        # Relevance ranking
│   └── utils.py         # Utility functions
├── input/               # Input PDFs and config
├── output/              # Generated results
├── Dockerfile           # Container configuration
└── README.md           # This file
```

## Performance

- **Accuracy**: Targets specific sections relevant to persona and job
- **Speed**: Optimized for sub-60-second processing
- **Reliability**: Handles various PDF formats and structures
- **Scalability**: Processes 3-10 documents efficiently
