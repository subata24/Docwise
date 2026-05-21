import os, uuid
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def ingest_pdf(file_path: str, doc_id: str, user_id: str) -> dict:
    loader   = PyPDFLoader(file_path)
    raw_docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_documents(raw_docs)

    for chunk in chunks:
        chunk.metadata.update({
            "doc_id":  doc_id,
            "user_id": user_id,
            "source":  Path(file_path).name,
        })

    vectorstore = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=EMBED_MODEL,
        persist_directory=CHROMA_DIR
    )
    vectorstore.add_documents(chunks)

    return {
        "doc_id":       doc_id,
        "chunks_added": len(chunks),
        "pages":        len(raw_docs)
    }


def get_vectorstore(user_id: str) -> Chroma:
    return Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=EMBED_MODEL,
        persist_directory=CHROMA_DIR
    )