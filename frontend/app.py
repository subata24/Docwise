import requests, uuid
import streamlit as st

st.set_page_config(page_title="DocWise", page_icon="📄", layout="wide")

API_URL = st.secrets.get("API_URL", "http://localhost:8000")

if "user_id"    not in st.session_state:
    st.session_state.user_id    = str(uuid.uuid4())[:8]
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "messages"   not in st.session_state:
    st.session_state.messages   = []
if "docs"       not in st.session_state:
    st.session_state.docs       = []


def fetch_docs():
    try:
        r = requests.get(
            f"{API_URL}/documents/{st.session_state.user_id}")
        return r.json() if r.status_code == 200 else []
    except:
        return []


# Sidebar
with st.sidebar:
    st.title("📄 DocWise")
    st.caption("Chat with your documents")

    uploaded = st.file_uploader("Upload PDF", type="pdf")
    if uploaded:
        with st.spinner("Uploading..."):
            r = requests.post(
                f"{API_URL}/documents/upload",
                params={"user_id": st.session_state.user_id},
                files={"file": (uploaded.name,
                                uploaded.getvalue(),
                                "application/pdf")}
            )
            if r.status_code == 200:
                st.success(f"Uploaded — processing in background")
                st.rerun()
            else:
                st.error("Upload failed")

    if st.button("Refresh documents"):
        st.session_state.docs = fetch_docs()
        st.rerun()

    st.session_state.docs = fetch_docs()
    doc_names = [d["filename"] for d in st.session_state.docs]

    selected_names = st.multiselect(
        "Chat with these documents",
        doc_names,
        default=doc_names
    )
    selected_ids = [
        d["doc_id"] for d in st.session_state.docs
        if d["filename"] in selected_names
    ]

    if st.button("Clear chat"):
        requests.delete(
            f"{API_URL}/chat/{st.session_state.session_id}",
            params={"user_id": st.session_state.user_id}
        )
        st.session_state.messages   = []
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.rerun()

# Main area
st.title("Chat with your documents")

if not st.session_state.docs:
    st.info("Upload a PDF in the sidebar to get started.")
else:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    question = st.chat_input("Ask anything about your documents...")
    if question:
        st.session_state.messages.append(
            {"role": "user", "content": question})
        st.chat_message("user").write(question)

        with st.spinner("Thinking..."):
            r = requests.post(f"{API_URL}/chat", json={
                "user_id":    st.session_state.user_id,
                "session_id": st.session_state.session_id,
                "question":   question,
                "doc_ids":    selected_ids or None
            })
            result = r.json()

        answer  = result.get("answer", "No response")
        sources = result.get("sources", [])

        full_answer = answer
        if sources:
            full_answer += f"\n\n*Sources: {', '.join(sources)}*"

        st.session_state.messages.append(
            {"role": "assistant", "content": full_answer})
        st.chat_message("assistant").write(full_answer)