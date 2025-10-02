#  IntelliPDF – AI-Powered PDF Assistant

##  Overview
Reading large PDFs (200+ pages) is time-consuming for students, researchers, professionals, and collectors. **IntelliPDF** is an AI-powered solution that helps users save valuable time by providing **summarized content, query-based responses, recommendations, and audio podcasts** for any PDF.

Built with **Google Gemini Pro**, IntelliPDF transforms how users interact with documents.

---

##  Features
-  **Summarization** – Get concise summaries of large PDFs instantly.  
-  **AI Chatbot** – Ask any query about the PDF and get precise answers powered by Gemini.  
-  **Smart Recommendations** – Receive suggestions with direct links to relevant PDF pages.  
-  **Insights Generation** – Extract the most important insights related to your query.  
-  **Podcast Mode** – If reading feels boring, listen to AI-generated audio podcasts of responses.  

---

##  Tech Stack
- **AI Model:** Google Gemini Pro  
- **Frontend:** React (Vite), TailwindCSS  
- **Backend:** FastAPI (Python)  
- **Database:** MongoDB  
- **Extras:** Text-to-Speech for podcast feature  

---

##  Project Structure
```bash
frontend/
  ├── src/components/
  │   ├── ChatbotSidebar.tsx      # Chatbot with query + recommendations
  │   ├── Recommendations.tsx     # Displays AI recommendations
  │   └── InsightsModal.tsx       # Shows insights in detail
backend/
  ├── api/
  │   └── routes/insights.py      # Insights & recommendation API
  ├── app.py                      # FastAPI main entry point
  └── requirements.txt            # Backend dependencies
```
## How It Works

User uploads a large PDF (200+ pages).

IntelliPDF automatically generates a summary.

User interacts with the chatbot to ask queries.

Backend calls Gemini Pro to provide:

Direct answer to the query

Smart recommendations with page links

Insights with key highlights

Podcast-style audio narration

User quickly accesses exactly what they need without reading the full document.

🖥️ Running Locally
1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/IntelliPDF.git
cd IntelliPDF
```
2️⃣ Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

3️⃣ Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # (Windows)
source venv/bin/activate  # (Mac/Linux)

pip install -r requirements.txt

# Run the server
uvicorn app:app --reload --host 0.0.0.0 --port 8080
```
## Example Use Case

A student uploads a 200-page pdf.

IntelliPDF instantly provides a summary.

The student asks, "What are the main results in chapter 5?".

AI returns the answer, provides recommendations with page links, generates key insights, and also delivers a podcast-style audio explanation.
