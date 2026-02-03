# IntelliPDF - System Design Document

## Table of Contents
1. [High-Level System Architecture](#high-level-system-architecture)
2. [Component Breakdown](#component-breakdown)
3. [Data Flow](#data-flow)
4. [API Design](#api-design)
5. [Database Design](#database-design)
6. [Technology Stack](#technology-stack)
7. [Scalability Considerations](#scalability-considerations)
8. [Security Considerations](#security-considerations)

## High-Level System Architecture

### System Overview

IntelliPDF follows a **3-tier architecture** with clear separation between presentation, business logic, and data layers. The system is designed as a **session-based, single-user application** with AI-powered document processing capabilities.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT TIER                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   React SPA     │  │  Adobe PDF SDK  │  │  Audio Player   │  │
│  │  (TypeScript)   │  │   Integration   │  │   Component     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION TIER                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   FastAPI       │  │  PDF Processing │  │  AI Integration │  │
│  │   Web Server    │  │     Engine      │  │     Layer       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌──────────────────┐           ┌──────────────────┐
│   EXTERNAL APIs  │           │    DATA TIER     │
│                  │           │                  │
│ • Google Gemini  │           │ • File System    │
│ • SarvamAI TTS   │           │ • JSON Storage   │
│ • Sentence       │           │ • Static Assets  │
│   Transformers   │           │ • Session Data   │
└──────────────────┘           └──────────────────┘
```

### Architecture Principles

1. **Separation of Concerns**: Clear boundaries between UI, business logic, and data
2. **Session-Based Design**: Each user session maintains isolated document processing
3. **AI-First Approach**: Core functionality built around AI/ML capabilities
4. **Stateless Backend**: RESTful API design with session-based state management
5. **Modular Components**: Loosely coupled modules for easy maintenance and testing

## Component Breakdown

### Frontend Components

#### 1. Core Application Structure
```typescript
App.tsx                    // Main router and application entry point
├── pages/
│   ├── Library.tsx        // Document management and upload interface
│   ├── Viewer.tsx         // Main document analysis interface
│   ├── SimpleViewer.tsx   // Lightweight PDF viewer
│   └── InsightsContext.tsx // Global insights state provider
├── components/
│   ├── AdobeViewer.tsx    // PDF rendering with Adobe SDK
│   ├── ChatbotSidebar.tsx // AI Q&A interface
│   ├── InsightsModal.tsx  // Structured insights display
│   ├── PodcastPanel.tsx   // Audio generation and playback
│   └── Recommendations.tsx // Smart content suggestions
└── store/
    └── useDocumentStore.ts // Zustand state management
```

#### 2. State Management Architecture
```typescript
// Zustand Store Structure
interface DocumentStore {
  // Document Management
  documents: PdfDoc[]
  activeDocId: string | null
  analysisSet: string[]
  
  // User Interaction
  selection: DocumentSelection | null
  
  // Statistics
  documentsToday: number
  storageUsed: number
  maxStorage: number
}
```

#### 3. Component Responsibilities

| Component | Responsibility | Key Features |
|-----------|---------------|--------------|
| **AdobeViewer** | PDF rendering and navigation | Zoom, page navigation, text selection |
| **ChatbotSidebar** | AI Q&A interface | Real-time chat, quick actions, image display |
| **InsightsModal** | Structured insights display | 4-category insights, modal interface |
| **PodcastPanel** | Audio generation/playback | TTS integration, audio controls |
| **DocumentLibrary** | File management | Upload, delete, session management |

### Backend Components

#### 1. API Layer (FastAPI)
```python
app.py                     // Main FastAPI application
├── /upload/new           // Document upload endpoint
├── /process              // PDF processing trigger
├── /chatbot              // Q&A interface
├── /search               // Semantic search
├── /insights             // Insights generation
└── /summary              // Document summarization
```

#### 2. Processing Engine
```python
src/
├── extract.py            // PDF text extraction and structure parsing
├── ranker.py             // Embedding generation (Sentence Transformers)
├── chatbot.py            // AI Q&A logic with Gemini integration
├── insights.py           // Structured insights generation
├── image_extractor.py    // Image extraction and OCR processing
├── summarizer.py         // Document summarization engine
└── singletons.py         // Shared instances (embedder, etc.)
```

#### 3. Core Processing Modules

| Module | Purpose | Key Technologies |
|--------|---------|------------------|
| **PDFExtractor** | Text extraction with structure preservation | PyMuPDF (fitz) |
| **EmbeddingGenerator** | Semantic vector generation | Sentence Transformers |
| **ChatbotEngine** | AI-powered Q&A responses | Google Gemini Pro API |
| **InsightsGenerator** | Structured analysis creation | Gemini + prompt engineering |
| **ImageExtractor** | Image processing and OCR | PIL, Tesseract, ResNet50 |

## Data Flow

### 1. Document Upload and Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant AI as AI Services
    participant FS as File System

    U->>F: Upload PDF file
    F->>B: POST /upload/new (sessionId, file)
    B->>FS: Save PDF to session directory
    B->>F: Return upload confirmation
    
    U->>F: Click "Process Document"
    F->>B: POST /process (sessionId)
    
    B->>B: Extract text with PyMuPDF
    B->>B: Generate embeddings (Sentence Transformers)
    B->>B: Extract images with OCR
    B->>AI: Generate summary (Gemini API)
    B->>FS: Save processed data to current_doc.json
    
    B->>F: Return processing complete
    F->>F: Update UI with processed document
```

### 2. Q&A Interaction Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant AI as Gemini API
    participant D as Document Store

    U->>F: Type question in chat
    F->>B: POST /chatbot (sessionId, query)
    
    B->>D: Load current_doc.json
    B->>B: Generate query embedding
    B->>B: Find top-k similar sections (cosine similarity)
    B->>B: Build context from relevant sections
    
    B->>AI: Send context + query to Gemini
    AI->>B: Return AI-generated answer
    
    B->>F: Return response with sources
    F->>F: Display answer + clickable references
```

### 3. Insights Generation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant S as Search API
    participant AI as Gemini API

    U->>F: Select text + click "Get Insights"
    F->>B: POST /insights (sessionId, selected_text)
    
    B->>S: POST /search (find related sections)
    S->>B: Return top-k relevant sections
    
    B->>B: Build structured prompt
    B->>AI: Request insights (JSON format)
    AI->>B: Return structured insights
    
    B->>F: Return categorized insights
    F->>F: Display in modal (4 categories)
```

### 4. Data Processing Pipeline

```
PDF Upload → Text Extraction → Structure Analysis → Embedding Generation → Storage
     ↓              ↓               ↓                    ↓              ↓
File System → PyMuPDF Parser → Heading Detection → Sentence Transformers → JSON
     ↓              ↓               ↓                    ↓              ↓
Session Dir → Sections List → Hierarchy Levels → 384-dim Vectors → current_doc.json
```

## API Design

### RESTful Endpoints

#### 1. Document Management APIs

```http
POST /upload/new
Content-Type: multipart/form-data
Parameters:
  - sessionId: string (form field)
  - file: PDF file (form field)
Response:
  {
    "message": "PDF uploaded",
    "sessionId": "session_123",
    "documentId": "doc_abc123",
    "file": {
      "storedName": "document_doc_abc123.pdf",
      "pages": 45,
      "url": "/storage/sessions/session_123/pdfs/document_doc_abc123.pdf"
    }
  }
```

```http
POST /process
Content-Type: application/x-www-form-urlencoded
Parameters:
  - sessionId: string
Response:
  {
    "message": "Processing complete",
    "sessionId": "session_123",
    "process_time_sec": 23.456,
    "output_file": "storage/sessions/session_123/output/current_doc.json"
  }
```

#### 2. AI Interaction APIs

```http
POST /chatbot?sessionId={sessionId}
Content-Type: application/json
Body:
  {
    "query": "What are the main benefits of machine learning?"
  }
Response:
  {
    "response": "Based on the document, the main benefits include...",
    "sources": [
      {
        "doc_id": "doc_123",
        "title": "ML Fundamentals",
        "section_heading": "Introduction",
        "page_number": 3,
        "top_snippet": "Machine learning enables...",
        "score": 0.89
      }
    ],
    "relevant_images": [],
    "response_time_sec": 2.34
  }
```

```http
POST /search?sessionId={sessionId}
Content-Type: application/json
Body:
  {
    "selected_text": "deep learning neural networks",
    "top_k": 5,
    "min_score": 0.3
  }
Response:
  {
    "search_time_ms": 45.67,
    "results": [
      {
        "title": "Deep Learning Guide",
        "section": "Neural Network Architecture",
        "page_number": 12,
        "snippets": ["Neural networks are...", "Deep learning uses..."],
        "score": 0.92
      }
    ]
  }
```

#### 3. Insights and Analysis APIs

```http
POST /insights?sessionId={sessionId}
Content-Type: application/json
Body:
  {
    "selected_text": "Transformers revolutionized NLP",
    "top_k": 3
  }
Response:
  {
    "insights": {
      "key_insights": [
        "Transformers use attention mechanisms",
        "Self-attention enables parallel processing"
      ],
      "did_you_know": [
        "BERT was the first transformer for NLP",
        "Attention is all you need paper introduced transformers"
      ],
      "contradictions": [
        "RNNs were sequential; Transformers are parallel"
      ],
      "inspirations": [
        "Apply transformers to computer vision",
        "Use attention for recommendation systems"
      ]
    },
    "related_sections": [...]
  }
```

### API Design Principles

1. **Session-Based**: All APIs require sessionId for user isolation
2. **RESTful**: Standard HTTP methods and status codes
3. **JSON Communication**: Consistent JSON request/response format
4. **Error Handling**: Structured error responses with meaningful messages
5. **Performance Metrics**: Response time tracking for optimization

## Database Design

### File-Based Storage Architecture

IntelliPDF uses a **file-based storage system** instead of traditional databases, optimized for document processing workflows.

#### 1. Directory Structure

```
storage/
└── sessions/
    └── {sessionId}/
        ├── pdfs/                    # Uploaded PDF files
        │   └── document_{docId}.pdf
        └── output/
            └── current_doc.json     # Processed document data

static/
├── images/                          # Extracted PDF images
│   ├── {hash}_img_0.png
│   ├── thumbnails/
│   └── processed/
└── audio/                           # Generated podcast files
    └── podcast_{uuid}.mp3
```

#### 2. Document Data Schema

```json
{
  "metadata": {
    "total_documents": 1,
    "processing_timestamp": "2026-02-03T10:30:00Z"
  },
  "documents": [
    {
      "doc_id": "uuid-string",
      "title": "Machine Learning Fundamentals",
      "file_path": "/storage/sessions/session_123/pdfs/ml_book.pdf",
      "pages": 340,
      "stats": {
        "total_sections": 45,
        "total_images": 12,
        "total_snippets": 135
      },
      "sections": [
        {
          "section_id": "uuid-string",
          "heading": "Chapter 1: Introduction",
          "heading_level": "H1",
          "page_number": 1,
          "content": "Machine learning is a branch of artificial intelligence...",
          "embedding": [0.12, -0.45, 0.78, ...],  // 384-dimensional vector
          "snippets": [
            {
              "text": "Machine learning enables computers to learn from data",
              "embedding": [0.15, -0.42, 0.81, ...]
            }
          ]
        }
      ],
      "images": [
        {
          "page": 5,
          "filename": "abc123_img_0.png",
          "path": "/static/images/abc123_img_0.png",
          "width": 800,
          "height": 600,
          "format": "png",
          "size_kb": 245,
          "ocr_text": "Training Loss vs Iterations",
          "ai_labels": [
            {"label": "graph", "confidence": 0.95},
            {"label": "chart", "confidence": 0.92}
          ]
        }
      ],
      "image_statistics": {
        "total_count": 12,
        "total_size_mb": 2.4,
        "by_format": {"png": 8, "jpeg": 4},
        "size_distribution": {"small": 3, "medium": 7, "large": 2}
      }
    }
  ]
}
```

#### 3. Data Access Patterns

| Operation | Pattern | Performance |
|-----------|---------|-------------|
| **Document Load** | Read single JSON file | O(1) - Direct file access |
| **Section Search** | In-memory cosine similarity | O(n) - Linear scan with early termination |
| **Image Retrieval** | Static file serving | O(1) - Direct file access |
| **Session Cleanup** | Directory deletion | O(1) - Filesystem operation |

### Storage Advantages

1. **Simplicity**: No database setup or maintenance required
2. **Performance**: Fast JSON parsing and in-memory operations
3. **Portability**: Easy backup and migration (copy directories)
4. **Development Speed**: No schema migrations or ORM complexity
5. **Session Isolation**: Natural user separation through directory structure

## Technology Stack

### Frontend Stack

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **React** | 18.3.1 | UI Framework | Modern, component-based, large ecosystem |
| **TypeScript** | 5.8.3 | Type Safety | Compile-time error detection, better IDE support |
| **Vite** | 5.4.19 | Build Tool | Fast HMR, optimized bundling, modern tooling |
| **TailwindCSS** | 3.4.17 | Styling | Utility-first, consistent design system |
| **Shadcn/UI** | Latest | Component Library | Accessible, customizable, modern components |
| **Zustand** | 5.0.7 | State Management | Lightweight, simple API, TypeScript support |
| **React Router** | 6.30.1 | Routing | Standard React routing solution |
| **React Query** | 5.83.0 | Data Fetching | Caching, synchronization, error handling |

### Backend Stack

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **Python** | 3.10+ | Runtime | Excellent AI/ML ecosystem, readable syntax |
| **FastAPI** | Latest | Web Framework | High performance, automatic API docs, async support |
| **PyMuPDF (fitz)** | Latest | PDF Processing | Fast, comprehensive PDF manipulation |
| **Sentence Transformers** | Latest | Embeddings | Pre-trained models, easy integration |
| **Google Gemini** | 2.5-flash | LLM Integration | Advanced reasoning, multimodal, cost-effective |
| **SarvamAI** | Latest | Text-to-Speech | Indian language support, natural voices |
| **Pydantic** | Latest | Data Validation | Type safety, automatic validation |
| **python-dotenv** | Latest | Configuration | Environment variable management |

### AI/ML Stack

| Component | Technology | Model/Version | Purpose |
|-----------|------------|---------------|---------|
| **Embeddings** | Sentence Transformers | all-MiniLM-L6-v2 | Semantic similarity (384-dim) |
| **Summarization** | Transformers | facebook/bart-large-cnn | Document summarization |
| **LLM** | Google Gemini | gemini-2.5-flash | Q&A, insights, reasoning |
| **TTS** | SarvamAI | Custom models | Audio generation |
| **OCR** | Tesseract | Latest | Image text extraction |
| **Image Classification** | TensorFlow/Keras | ResNet50 | Image labeling |

### Infrastructure Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Containerization** | Docker | Deployment packaging |
| **Web Server** | Uvicorn | ASGI server for FastAPI |
| **Static Files** | FastAPI StaticFiles | Image and audio serving |
| **CORS** | FastAPI CORS Middleware | Cross-origin requests |
| **File Storage** | Local Filesystem | Document and media storage |

### Development Tools

| Tool | Purpose |
|------|---------|
| **ESLint** | JavaScript/TypeScript linting |
| **Prettier** | Code formatting |
| **TypeScript Compiler** | Type checking |
| **Vite Dev Server** | Development server with HMR |
| **FastAPI Auto Docs** | API documentation |

## Scalability Considerations

### Current Architecture Limitations

1. **Single-User Design**: Session-based, not multi-tenant
2. **File-Based Storage**: Limited to single server deployment
3. **In-Memory Processing**: Constrained by server RAM
4. **Synchronous Processing**: Blocking operations for large documents

### Horizontal Scaling Strategies

#### 1. Multi-User Architecture
```
Current: Session-based file storage
Future:  User authentication + database storage

Implementation:
├── User Management Service
├── Document Database (PostgreSQL)
├── File Storage Service (S3/MinIO)
└── Session Management (Redis)
```

#### 2. Microservices Decomposition
```
Monolithic FastAPI → Microservices

Services:
├── Document Processing Service
├── AI/ML Service (Gemini, Embeddings)
├── Search Service (Vector Database)
├── User Management Service
└── File Storage Service
```

#### 3. Asynchronous Processing
```python
# Current: Synchronous processing
def process_pdf(file_path):
    extract_text()
    generate_embeddings()
    create_summary()

# Future: Async with queues
async def process_pdf_async(file_path):
    task_id = queue.enqueue(process_pdf_task, file_path)
    return {"task_id": task_id, "status": "processing"}
```

### Vertical Scaling Optimizations

#### 1. Performance Improvements
- **Caching Layer**: Redis for frequently accessed data
- **Database Optimization**: Indexes on search fields
- **CDN Integration**: Static asset delivery
- **Connection Pooling**: Database connection management

#### 2. Resource Optimization
```python
# Memory optimization
- Streaming PDF processing for large files
- Lazy loading of embeddings
- Garbage collection tuning
- Memory-mapped file access

# CPU optimization  
- Parallel embedding generation
- Async I/O operations
- Process pooling for CPU-intensive tasks
```

### Vector Database Integration

For production scale, replace in-memory search with vector database:

```python
# Current: In-memory cosine similarity
def search_sections(query_embedding, sections):
    scores = [cosine_similarity(query_embedding, sec['embedding']) 
              for sec in sections]
    return sorted(zip(sections, scores), key=lambda x: x[1], reverse=True)

# Future: Vector database (Pinecone/Weaviate)
def search_sections_vectordb(query_embedding, top_k=10):
    results = vector_db.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results
```

### Load Balancing Architecture

```
Internet → Load Balancer → [App Server 1, App Server 2, App Server 3]
                        ↓
                   Shared Services:
                   ├── Vector Database (Pinecone)
                   ├── File Storage (S3)
                   ├── Cache Layer (Redis)
                   └── Message Queue (RabbitMQ)
```

## Security Considerations

### Current Security Measures

#### 1. API Security
```python
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input Validation
class ChatbotQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)

# File Upload Validation
if not file.filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=400, detail="Only PDF files allowed")
```

#### 2. Environment Security
```python
# API Key Management
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set")

# File Path Sanitization
def clean_filename(name: str) -> str:
    name = re.sub(r"[^a-z0-9_\-.]", "", name.lower())
    return name
```

### Production Security Enhancements

#### 1. Authentication & Authorization
```python
# JWT Authentication
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

# Role-Based Access Control
@app.get("/documents")
async def get_documents(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user_documents
```

#### 2. Data Protection
```python
# File Encryption
from cryptography.fernet import Fernet

def encrypt_file(file_path: str, key: bytes):
    fernet = Fernet(key)
    with open(file_path, 'rb') as file:
        encrypted_data = fernet.encrypt(file.read())
    return encrypted_data

# Database Encryption
DATABASE_URL = "postgresql://user:pass@localhost/db?sslmode=require"
```

#### 3. Rate Limiting & Monitoring
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chatbot")
@limiter.limit("10/minute")
async def chatbot_endpoint(request: Request, ...):
    # API logic
```

#### 4. Security Headers
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

### Data Privacy Compliance

#### 1. GDPR Compliance
- **Data Minimization**: Only collect necessary document data
- **Right to Deletion**: Implement document deletion endpoints
- **Data Portability**: Export user documents in standard formats
- **Consent Management**: Clear consent for AI processing

#### 2. Document Security
```python
# Secure file handling
def secure_file_upload(file: UploadFile, user_id: str):
    # Virus scanning
    scan_result = antivirus_scan(file)
    if not scan_result.is_clean:
        raise HTTPException(status_code=400, detail="File failed security scan")
    
    # File type validation
    if not is_valid_pdf(file):
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    
    # Size limits
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
```

### API Security Best Practices

1. **Input Sanitization**: Validate all user inputs
2. **Output Encoding**: Prevent XSS in responses
3. **SQL Injection Prevention**: Use parameterized queries
4. **HTTPS Enforcement**: Encrypt data in transit
5. **API Versioning**: Maintain backward compatibility
6. **Audit Logging**: Track all user actions
7. **Error Handling**: Don't expose internal details

---

## Deployment Architecture

### Development Environment
```
Developer Machine:
├── Frontend (Vite Dev Server) → http://localhost:5173
├── Backend (Uvicorn) → http://localhost:8080
└── Static Files → Local filesystem
```

### Production Environment
```
Production Server:
├── Nginx (Reverse Proxy + Static Files)
├── Docker Container (FastAPI + Uvicorn)
├── Docker Container (React Build)
└── Persistent Storage (Documents + Media)
```

### Docker Configuration
```dockerfile
# Multi-stage build for production
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.10-slim as backend
WORKDIR /app
COPY backend/requirements*.txt ./
RUN pip install --no-cache-dir -r requirements_summarizer.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./static/frontend

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

*Document Version: 1.0*  
*Last Updated: February 3, 2026*  
*Project: IntelliPDF - AI-Powered PDF Assistant*