from sqlalchemy import Column, Integer, String, ForeignKey, Text,JSON
from sqlalchemy import DateTime, func
from sqlalchemy.orm import relationship
from database.settings import Base


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    status = Column(String, default="uploaded")
    uploaded_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime)
    user = relationship("User", back_populates="documents")
    formatting_suggestions = relationship("FormattingSuggestion", back_populates="document", cascade="all, delete")


class FormattingSuggestion(Base):
    __tablename__ = "formatting_suggestions"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    description = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=func.now())
    document = relationship("Document", back_populates="formatting_suggestions")
