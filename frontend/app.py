import os
import time
import uuid

import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


st.set_page_config(page_title="DocWise", page_icon="📄", layout="wide")

st.markdown(
    """
<style>
html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.block-container {
    max-width: 1180px;
    padding-top: 1.4rem;
}

[data-testid="stSidebar"] {
    background: #0f172a;
}

[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(148, 163, 184, 0.35);
    border-radius: 8px;
    padding: 0.7rem;
}

.hero {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.15rem 1.25rem;
    margin-bottom: 1.2rem;
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 60%, #eef2ff 100%);
}

.hero h1 {
    font-size: 2rem;
    line-height: 1.1;
    margin: 0 0 0.35rem 0;
}

.hero p {
    color: #475569;
    margin: 0;
}

.metric-row {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.2rem;
}

.metric-box {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    background: #ffffff;
}

.metric-box span {
    display: block;
    color: #64748b;
    font-size: 0.8rem;
    margin-bottom: 0.15rem;
}

.metric-box strong {
    color: #0f172a;
    font-size: 1.1rem;
}
</style>
""",
    unsafe_allow_html=True,
)

try:
    API_URL = os.getenv("API_URL") or st.secrets.get("API_URL", "http://localhost:7860")
except StreamlitSecretNotFoundError:
    API_URL = os.getenv("API_URL", "http://127.0.0.1:7860")
API_URL = API_URL.rstrip("/")


if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "docs" not in st.session_state:
    st.session_state.docs = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = set()


def api_online():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def fetch_docs():
    try:
        response = requests.get(
            f"{API_URL}/documents/{st.session_state.user_id}",
            timeout=10,
        )
        return response.json() if response.status_code == 200 else []
    except requests.RequestException:
        return []


def status_label(status):
    return {
        "ready": "Ready",
        "processing": "Processing",
        "failed": "Failed",
    }.get(status, status or "Unknown")


with st.sidebar:
    st.title("📄 DocWise")
    st.caption("Chat with your documents")
    st.caption(f"API: {API_URL}")

    if api_online():
        st.success("Backend online")
    else:
        st.error("Backend offline")

    uploaded = st.file_uploader("Upload PDF", type="pdf")
    upload_key = f"{uploaded.name}:{uploaded.size}" if uploaded else None

    if uploaded:
        st.caption(f"Selected: {uploaded.name}")

    if uploaded and upload_key in st.session_state.uploaded_files:
        st.info("This PDF was already uploaded in this session.")
    elif uploaded and st.button("Upload document", type="primary"):
        with st.spinner("Uploading..."):
            try:
                response = requests.post(
                    f"{API_URL}/documents/upload",
                    params={"user_id": st.session_state.user_id},
                    files={
                        "file": (
                            uploaded.name,
                            uploaded.getvalue(),
                            "application/pdf",
                        )
                    },
                    timeout=60,
                )
                if response.status_code == 200:
                    st.session_state.uploaded_files.add(upload_key)
                    st.success("Uploaded - processing in background")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Upload failed: {response.status_code} {response.text}")
            except requests.RequestException as exc:
                st.error(f"Upload request failed: {exc}")

    if st.button("Refresh documents"):
        st.session_state.docs = fetch_docs()
        st.rerun()

    st.session_state.docs = fetch_docs()
    ready_docs = [d for d in st.session_state.docs if d.get("status") == "ready"]
    processing_docs = [
        d for d in st.session_state.docs if d.get("status") == "processing"
    ]
    failed_docs = [d for d in st.session_state.docs if d.get("status") == "failed"]

    if st.session_state.docs:
        st.subheader("Documents")
        for doc in st.session_state.docs:
            detail = status_label(doc.get("status"))
            if doc.get("chunks"):
                detail += f" · {doc['chunks']} chunks"
            st.caption(f"{doc['filename']} - {detail}")

    if processing_docs:
        with st.spinner("Processing document..."):
            time.sleep(2)
        st.rerun()

    for doc in failed_docs:
        st.error(f"{doc['filename']} failed to process. Check the backend terminal.")

    doc_names = [d["filename"] for d in ready_docs]
    selected_names = st.multiselect(
        "Chat with these documents",
        doc_names,
        default=doc_names,
    )
    selected_ids = [
        d["doc_id"] for d in ready_docs if d["filename"] in selected_names
    ]

    if st.button("Clear chat"):
        try:
            requests.delete(
                f"{API_URL}/chat/{st.session_state.session_id}",
                params={"user_id": st.session_state.user_id},
                timeout=10,
            )
        except requests.RequestException:
            pass
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.rerun()


ready_docs = [d for d in st.session_state.docs if d.get("status") == "ready"]
processing_docs = [d for d in st.session_state.docs if d.get("status") == "processing"]

st.markdown(
    """
<div class="hero">
  <h1>DocWise</h1>
  <p>Upload PDFs, retrieve grounded answers, and keep every response tied to source documents.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="metric-row">
  <div class="metric-box"><span>Total documents</span><strong>{len(st.session_state.docs)}</strong></div>
  <div class="metric-box"><span>Ready</span><strong>{len(ready_docs)}</strong></div>
  <div class="metric-box"><span>Processing</span><strong>{len(processing_docs)}</strong></div>
</div>
""",
    unsafe_allow_html=True,
)

if not st.session_state.docs:
    st.info("Upload a PDF in the sidebar to get started.")
elif not ready_docs:
    st.info("Your PDF is still processing. Click Refresh documents in a few seconds.")
else:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    question = st.chat_input("Ask anything about your documents...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        with st.spinner("Thinking..."):
            response = requests.post(
                f"{API_URL}/chat",
                json={
                    "user_id": st.session_state.user_id,
                    "session_id": st.session_state.session_id,
                    "question": question,
                    "doc_ids": selected_ids or None,
                },
                timeout=120,
            )
            if response.status_code != 200:
                st.error(response.json().get("detail", "Chat request failed"))
                st.stop()
            result = response.json()

        answer = result.get("answer", "No response")
        sources = result.get("sources", [])

        full_answer = answer
        if sources:
            full_answer += f"\n\n*Sources: {', '.join(sources)}*"

        st.session_state.messages.append(
            {"role": "assistant", "content": full_answer}
        )
        st.chat_message("assistant").write(full_answer)
