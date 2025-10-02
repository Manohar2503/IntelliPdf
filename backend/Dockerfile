FROM python:3.10-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for caching
COPY requirements_doc_intel.txt .

# Install dependencies (cached unless requirements change)
RUN pip install --no-cache-dir -r requirements_doc_intel.txt

# Pre-download sentence-transformers model (cached unless above changes)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code LAST
COPY app.py .        
COPY main.py /app/
COPY src/ ./src/

# Create required directories
RUN mkdir -p /app/input /app/output /app/newpdf

ENV PYTHONPATH=/app
ENV TOKENIZERS_PARALLELISM=false

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
