# =====================
# Backend Stage
# =====================
FROM python:3.10-slim AS backend
WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ curl && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements_doc_intel.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download SentenceTransformer model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy backend code into /app/backend
COPY backend/ ./backend/

# Create input/output dirs
RUN mkdir -p /app/input /app/output /app/newpdf

ENV PYTHONPATH=/app
ENV TOKENIZERS_PARALLELISM=false

# =====================
# Frontend Stage
# =====================
FROM node:18 AS frontend
WORKDIR /frontend

COPY frontend/ ./
RUN npm install && npm run build

# =====================
# Final Stage
# =====================
FROM backend AS final

COPY --from=frontend /frontend/dist /app/frontend

WORKDIR /app
EXPOSE 8080

# Run backend
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080"]
