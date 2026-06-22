---
title: Docwise API
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

<div align="center">

<img src="https://img.shields.io/badge/DocWise-RAG%20Document%20Intelligence-0F6E56?style=for-the-badge&logoColor=white" alt="DocWise"/>

# DocWise — Multi-Document RAG SaaS

**Upload your documents. Ask anything. Get answers with sources.**

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Streamlit-FF4B4B?style=flat-square)](https://docwise-bhducltoyfasnyehruma6t.streamlit.app/)
[![API Docs](https://img.shields.io/badge/📡_API_Docs-HuggingFace-FFD21E?style=flat-square)](https://subata24-docwise-api.hf.space/docs)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=flat-square&logo=postgresql&logoColor=white)](https://neon.tech)
[![HuggingFace](https://img.shields.io/badge/Backend-HuggingFace%20Spaces-FFD21E?style=flat-square)](https://huggingface.co/spaces/Subata24/docwise-api)

</div>

---

## What it does

DocWise lets you upload PDF documents and have a conversation with them using AI. Ask questions across multiple documents at once, compare them side by side, or search semantically across your entire library. Every answer cites its source document.

---

## Features

### 📄 Multi-document upload
Upload multiple PDFs. Each one is chunked, embedded, and indexed into a per-user vector store. Document records persist across sessions via PostgreSQL.

### 💬 Conversational RAG with memory
Chat with your documents with full conversation memory. Follow-up questions work correctly — "explain that more" and "what did you mean by X" understand context from previous turns.

### 🔍 Semantic cross-document search
Search for a concept across your entire document library. Results ranked by similarity score with source attribution.

### 📊 Document comparison
Ask the same question across two or more documents simultaneously. Useful for comparing contracts, research papers, or policy documents.

### 📍 Source citations
Every answer includes which document it came from. No silent hallucination.

### ⚡ Async ingestion pipeline
Upload returns immediately. PDF processing runs as a background task. Poll the status endpoint to check when your document is ready to query.

---

## Architecture

┌──────────────────────────────────────────────────────┐

│                  Streamlit Frontend                  │

│         Upload · Chat · Search · Compare             │

└───────────────────────┬──────────────────────────────┘

│ HTTP

┌───────────────────────▼──────────────────────────────┐

│         FastAPI Backend — HuggingFace Spaces         │

│     Upload · Ingest · Chat · Search · Compare        │

└──────────┬────────────────────────────┬──────────────┘

│                            │

┌──────────▼──────────┐    ┌────────────▼─────────────┐

│    PostgreSQL        │    │        RAG Layer          │

│    Neon (cloud)      │    │  LangChain + ChromaDB    │

│  Document records    │    │  Groq LLaMA 3.1          │

│  Upload status       │    │  HuggingFace Embeddings  │

└─────────────────────┘    └──────────────────────────┘

**Ingestion workflow:**
1. User uploads PDF via Streamlit
2. FastAPI saves file and creates DB record with status `processing`
3. Background task chunks PDF → generates embeddings → stores in ChromaDB
4. DB record updated to `ready`
5. User polls status endpoint, then starts chatting

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| Database | PostgreSQL (Neon) |
| ORM | SQLAlchemy |
| AI model | Groq LLaMA 3.1 |
| RAG framework | LangChain |
| Vector store | ChromaDB |
| Embeddings | HuggingFace sentence-transformers |
| Backend deploy | HuggingFace Spaces (Docker) |
| Frontend deploy | Streamlit Cloud |

---

## API reference

### `GET /health`
Health check.
```json
{ "app": "DocWise", "status": "running", "version": "1.0.0" }
```

### `POST /documents/upload`

Upload a PDF document and start asynchronous ingestion.

#### Query Parameters

| Parameter | Type   | Required | Description                                           |
| --------- | ------ | -------- | ----------------------------------------------------- |
| user_id   | string | Yes      | Unique identifier for the user uploading the document |

#### Request Body

`multipart/form-data`

| Field | Type     | Required | Description                  |
| ----- | -------- | -------- | ---------------------------- |
| file  | PDF File | Yes      | Document to upload and index |

#### Response

```json
{
  "doc_id": "a1b2c3d4",
  "status": "processing"
}
```
### `DELETE /chat/{session_id}`
Clear conversation memory for a session.

---

## Getting started locally

**Prerequisites:** Python 3.11+, Groq API key from [console.groq.com](https://console.groq.com), Neon account from [neon.tech](https://neon.tech)

```bash
git clone https://github.com/subata24/Docwise
cd Docwise
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in the root:
```env
GROQ_API_KEY=your_groq_key
DATABASE_URL=postgresql://user:pass@localhost/docwise
CHROMA_PERSIST_DIR=./chroma_db
UPLOAD_DIR=./uploads
```

Run backend:
```bash
uvicorn backend.main:app --reload --port 7860
# API docs at http://localhost:7860/docs
```

Run frontend:
```bash
streamlit run frontend/app.py
```

---

## Project structure
Docwise/

├── backend/

│   ├── main.py        # FastAPI routes

│   ├── ingest.py      # PDF chunking + ChromaDB indexing

│   ├── rag.py         # LangChain RAG + conversation memory

│   ├── models.py      # SQLAlchemy database models

│   ├── database.py    # DB connection setup

│   └── schemas.py     # Pydantic request/response shapes

├── frontend/

│   └── app.py         # Streamlit UI

├── Dockerfile

├── docker-compose.yml

├── requirements.txt

---

## Engineering highlights

- Per-user ChromaDB collections — users only retrieve from their own documents
- MMR retrieval (Maximal Marginal Relevance) returns diverse chunks, not repetitive ones
- ConversationBufferWindowMemory keeps last 6 turns — follow-up questions work correctly
- Async background ingestion — no request timeouts on large PDFs
- Document status tracking in PostgreSQL — client polls until ready
- Source attribution on every answer
- Dockerized and deployed on HuggingFace Spaces free tier — no credit card required

---
---

## Author

**Subata Khan** — AI Engineer & LLM Systems Developer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-subata--khan-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/subata-khan)
[![GitHub](https://img.shields.io/badge/GitHub-subata24-181717?style=flat-square&logo=github)](https://github.com/subata24)

---

<div align="center">
<sub>Built to make document intelligence accessible — one PDF at a time.</sub>
</div>