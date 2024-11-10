from database.settings import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from schemas.document import DocumentResponseSchema, FormattingSuggestionResponse
from sqlalchemy import select, func
from models.document import Document, FormattingSuggestion
from utils.helper_apa import APAValidator
import os
from typing import Optional


async def document_create(user_id: int,
                          file_path: str,
                          file_name: str,
                          db: AsyncSession = Depends(get_session),
                          ) -> DocumentResponseSchema:
    new_document = Document(
        user_id=user_id,
        file_path=file_path,
        file_name=file_name,
    )

    db.add(new_document)

    await db.commit()
    await db.refresh(new_document)

    return DocumentResponseSchema.from_orm(new_document)


async def document_delete(user_id: int,
                          document_id: int,
                          db: AsyncSession = Depends(get_session),
                          ):
    document = await db.execute(
        select(Document).filter(Document.id == document_id)
    )
    document = document.scalars().first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this document")

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    await db.delete(document)
    await db.commit()


async def create_formatting_suggestions(document_id: int, db: AsyncSession) -> FormattingSuggestionResponse:
    result = await db.execute(select(Document).filter(Document.id == document_id))
    document = result.scalars().first()

    if not document:
        raise HTTPException(status_code=404, detail=f"Document with id {document_id} not found.")

    result = await db.execute(
        select(FormattingSuggestion).where(FormattingSuggestion.document_id == document_id)
    )
    existing_suggestion = result.scalars().first()
    apa_validator = APAValidator()
    issues = apa_validator.validate_document(document.file_path)
    suggestion = "\n".join(issues)
    if existing_suggestion:
        existing_suggestion.description = suggestion
        existing_suggestion.created_at = func.now()
        formatting_suggestion = existing_suggestion
    else:
        new_suggestion = FormattingSuggestion(document_id=document_id, description=suggestion)
        db.add(new_suggestion)
        formatting_suggestion = new_suggestion

    await db.commit()
    await db.refresh(formatting_suggestion)

    return FormattingSuggestionResponse.from_orm(formatting_suggestion)


async def get_formatting_suggestion_by_document_id(document_id: int, db: AsyncSession) -> Optional[
    FormattingSuggestionResponse]:
    result = await db.execute(
        select(FormattingSuggestion).where(FormattingSuggestion.document_id == document_id)
    )

    formatting_suggestion = result.scalars().first()

    if not formatting_suggestion:
        raise HTTPException(status_code=404,
                            detail=f"No formatting suggestion found for document with id {document_id}")

    return FormattingSuggestionResponse.from_orm(formatting_suggestion)


async def delete_formatting_suggestion(formatting_suggestion: int, db: AsyncSession) -> None:
    result = await db.execute(
        select(FormattingSuggestion).where(FormattingSuggestion.id == formatting_suggestion)
    )

    formatting_suggestion = result.scalars().first()

    if not formatting_suggestion:
        raise HTTPException(status_code=404,
                            detail=f"No formatting suggestion found id {formatting_suggestion}")

    await db.delete(formatting_suggestion)
    await db.commit()