from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentResponseSchema(BaseModel):
    id: int
    user_id: int
    file_path: str
    status: Optional[str] = "uploaded"

    class Config:
        orm_mode = True
        from_attributes = True


class FormattingSuggestionResponse(BaseModel):
    id: int
    document_id: int
    description: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
