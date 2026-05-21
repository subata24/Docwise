import uuid, os, shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, get_db, Base, SessionLocal
from models import Document
from schemas import ChatRequest, ChatResponse
from ingest import ingest_pdf, UPLOAD_DIR
from rag import build_chain, ask, compare_documents, cross_search

Base.metadata.create_all(bind=engine)
app = FastAPI(title="DocWise API", version="1.0.0")

_chains: dict = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents/upload")
async def upload_document(
    user_id: str,
    bg: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    doc_id    = str(uuid.uuid4())[:8]
    save_path = f"{UPLOAD_DIR}/{doc_id}_{file.filename}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    record = Document(
        id=doc_id, user_id=user_id,
        filename=file.filename, status="processing"
    )
    db.add(record)
    db.commit()

    bg.add_task(_ingest_bg, save_path, doc_id, user_id)
    return {"doc_id": doc_id, "status": "processing"}


def _ingest_bg(path: str, doc_id: str, user_id: str):
    db = SessionLocal()
    try:
        result = ingest_pdf(path, doc_id, user_id)
        doc    = db.query(Document).filter(
                     Document.id == doc_id).first()
        if doc:
            doc.status = "ready"
            doc.chunks = result["chunks_added"]
            db.commit()
    finally:
        db.close()


@app.get("/documents/{user_id}")
def list_documents(user_id: str, db: Session = Depends(get_db)):
    docs = db.query(Document).filter(
        Document.user_id == user_id,
        Document.status  == "ready"
    ).all()
    return [{"doc_id": d.id, "filename": d.filename,
             "chunks": d.chunks} for d in docs]


@app.get("/documents/{user_id}/{doc_id}/status")
def doc_status(user_id: str, doc_id: str,
               db: Session = Depends(get_db)):
    doc = db.query(Document).filter(
        Document.id      == doc_id,
        Document.user_id == user_id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return {"doc_id": doc_id, "status": doc.status,
            "chunks": doc.chunks}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    key = f"{req.user_id}:{req.session_id}"
    if key not in _chains:
        _chains[key] = build_chain(req.user_id,
                                   req.doc_ids or None)
    return ChatResponse(**ask(_chains[key], req.question))


@app.delete("/chat/{session_id}")
def clear_session(session_id: str, user_id: str):
    _chains.pop(f"{user_id}:{session_id}", None)
    return {"cleared": True}


@app.post("/documents/compare")
def compare(user_id: str, doc_ids: list[str], question: str):
    if len(doc_ids) < 2:
        raise HTTPException(400, "Need at least 2 documents")
    return compare_documents(user_id, doc_ids, question)


@app.get("/documents/search")
def search(user_id: str, query: str, k: int = 8):
    return cross_search(user_id, query, k)