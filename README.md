# 📄 IntelliPDF — AI-Powered PDF Study & Intelligence Assistant

**IntelliPDF** is an AI-powered PDF assistant that helps users **understand large documents faster** using **smart summaries, question answering, recommendations, and insights** — all inside an interactive PDF viewer.

Built for **students, researchers, and professionals**, IntelliPDF makes reading long PDFs (100+ pages) easy by extracting key sections and enabling intelligent interaction.

---

## 🚀 Features

✅ **Upload & Analyze PDFs (Session-based)**  
- Upload a PDF and process it into searchable sections  
- Works with user-wise sessions using `sessionId`

✅ **1-Minute Recap (Smart Summary)**  
- Generates quick revision-style recap from the PDF  
- Useful before exams, interviews, and fast study

✅ **AI Chatbot (Document Q&A)**  
- Ask questions about the PDF  
- Answers generated using **Google Gemini**

✅ **Smart Recommendations (Relevant Sections)**  
- Select text from the PDF → get related matching sections  
- Includes **page numbers** for fast navigation

✅ **Insights Generator (Deep Understanding)**  
Structured insights from selected text + related sections:
- Key insights  
- Quick facts  
- Connections / inspirations  

✅ **Interactive PDF Viewer (Adobe Embed API)**  
- Smooth reading experience  
- Supports jump-to-page feature for recommendations

---

## 🧠 How It Works

1. User uploads a PDF  
2. Backend processes the document:
   - Extracts sections from the PDF  
   - Generates embeddings for similarity search  
3. IntelliPDF enables:
   - Summary (1-minute recap)  
   - Chatbot Q&A  
   - Recommendations (semantic search)  
   - Insights generation (Gemini + context)

---

## 🛠 Tech Stack

### Frontend
- React (Vite)
- TypeScript
- TailwindCSS
- shadcn/ui
- React Query
- Adobe PDF Embed API

### Backend
- FastAPI (Python)
- PyMuPDF (fitz)
- Sentence Transformers (Embeddings)
- Google Gemini (LLM)

### Storage
Session-based folder structure:
- `storage/sessions/<sessionId>/pdfs`
- `storage/sessions/<sessionId>/output`

---

## 📁 Project Structure

```bash
frontend/
  ├── src/components/
  │   ├── SetForAnalysis.tsx
  │   ├── ChatbotSidebar.tsx
  │   ├── Recommendations.tsx
  │   ├── InsightsModal.tsx
  │   └── AdobeViewer.tsx
  ├── src/utils/
  │   └── session.ts
  └── src/config.ts

backend/
  ├── app.py
  ├── main.py
  ├── src/
  │   ├── chatbot.py
  │   ├── insights.py
  │   └── singletons.py
  └── storage/
      └── sessions/


---

## ⚙️ Environment Variables

### ✅ Backend Environment (`backend/.env`)

Create a `.env` file inside the `backend/` folder:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
BACKEND_URL=http://localhost:8080
```

### ✅ Frontend Environment (`frontend/.env`)

Create a `.env` file inside the `frontend/` folder:

```env
VITE_BACKEND_URL=http://localhost:8080
VITE_ADOBE_EMBED_API_KEY=your_adobe_embed_api_key
```

---

## ▶️ Run Locally (Development)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/IntelliPDF.git
cd IntelliPDF
```

---

### 2️⃣ Start Backend (FastAPI)

```bash
cd backend
python -m venv venv
```

✅ Activate the environment:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

✅ Install dependencies & run server:

```bash
pip install -r requirements_doc_intel.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8080
```

Backend runs at:

➡️ `http://localhost:8080`

---

### 3️⃣ Start Frontend (Vite)

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

➡️ `http://localhost:5173`

---

## 🐳 Run Using Docker (Frontend + Backend on SAME Port)

✅ This will run **both frontend + backend together on port 8080**.

### 1️⃣ Build Docker Image

From the project root:

```bash
docker build -t intellipdf .
```

### 2️⃣ Run Docker Container

```bash
docker run -p 8080:8080 intellipdf
```

✅ Now open:

➡️ `http://localhost:8080`

---

## ✅ Example Use Case

1. Upload a large PDF (example: 200 pages)
2. IntelliPDF generates a quick recap
3. Ask: **"Explain the main points in Unit 4"**
4. Instantly get:

   * AI Answers
   * Relevant recommendations with page links
   * Insights for revision

---

## 📌 Notes

✅ Make sure your **Gemini API key** is active and correct (`backend/.env`)
✅ Adobe Viewer requires a valid **Adobe Embed API key** (`frontend/.env`)
✅ Highlighting text improves recommendation quality

---

## 👨‍💻 Author

**Manohar Jinka**
📧 Email: `manujinka22@gmail.com`
🔗 GitHub: [https://github.com/Manohar2503](https://github.com/Manohar2503)
🔗 LinkedIn: [https://www.linkedin.com/in/manohar-jinka-160970267](https://www.linkedin.com/in/manohar-jinka-160970267)
