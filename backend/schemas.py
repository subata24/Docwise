from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    user_id:    str
    session_id: str
    question:   str
    doc_ids:    Optional[list[str]] = None

class ChatResponse(BaseModel):
    answer:  str
    sources: list[str]