from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from database import Base

class Document(Base):
    __tablename__ = "documents"
    id         = Column(String, primary_key=True)
    user_id    = Column(String, nullable=False, index=True)
    filename   = Column(String, nullable=False)
    status     = Column(String, default="processing")
    chunks     = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())