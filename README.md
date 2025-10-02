
---

# Adobe Hackathon 2025 – Finale Solution

## Project Overview

This project is an **interactive, intelligent PDF reading application** built for the **Adobe India Hackathon 2025 (Finale)**.

It extends the **PDF understanding engine** and **persona-driven document intelligence system** built in earlier rounds, and brings them into a **real user experience**.

### Key Features

* **Adobe PDF Embed API** – renders PDFs with 100% fidelity (zoom/pan supported).
* **Bulk & Fresh Uploads** – users can upload past PDFs and open new ones.
* **Context-Aware Recommendations** – highlights at least 3 relevant sections across PDFs (>80% accuracy).
* **Snippets** – short 1–2 sentence explanations of relevance.
* **Insights Bulb** – provides insights, counterpoints, and connections across documents.
* **Podcast Mode** – generates narrated audio overview using TTS.

---

## Project Structure

```
Finale-solution/
│── frontend/        # React + TypeScript frontend
│── backend/         # Python backend with LLM & TTS
│── credentials/     # Credentials for Gemini & TTS
│── dockerfile       # Build instructions
│── README.md        # Documentation
```

---

## Frontend

Located in the `frontend/` folder. Built using:

* React (TypeScript)
* Adobe PDF Embed API (for high-fidelity PDF rendering)
* Tailwind CSS (responsive UI)

### Important Note for Recommendations

The recommendation logic is handled in:

```
frontend/src/components/recommendations.tsx
frontend/src/components/InsightsModal.tsx
```

If recommendations or insights do not appear automatically:

1. Copy the selected text.
2. Paste it into the `selected_text` field inside the `fetchRecommendations()` and `useQuery()` function.

This ensures smooth manual testing during development.

---

## Backend

Located in the `backend/` folder. Built using:

* Python
* Gemini 2.5 Flash – for LLM calls (recommendations and insights).
* Gemini TTS – for generating audio in Podcast Mode.

### Models Used

* LLM: `gemini-2.5-flash`
* TTS: Gemini TTS (via environment variables).

---

## Running with Docker

### 1. Build the image

```bash
docker build --no-cache -t <image-name> .
```

### 2. Run the container

```bash
docker run --rm -p 8080:8080 \
   -e GOOGLE_APPLICATION_CREDENTIALS=/credentials/tts_account.json \
   -e GEMINI_MODEL=gemini-2.5-flash \
   -e ADOBE_EMBED_API_KEY=<user-id> \
   -v "path/credentials:/credentials" \
   -v "path/backend/input:/app/input" \
   -v "path/backend/newpdf:/app/newpdf" \
   -v "path/backend/output:/app/output" \
   <image-name>
```

---

## Accessing the App

Once the container is running, open:
[http://localhost:8080](http://localhost:8080)

---

## Deliverables Recap

* Working prototype (browser-accessible).
* Frontend and Backend integrated.
* Insights and Recommendations powered by Gemini.
* TTS (Podcast Mode) enabled.

---


