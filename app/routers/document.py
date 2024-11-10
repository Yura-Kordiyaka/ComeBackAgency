from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from schemas.document import DocumentResponseSchema, FormattingSuggestionResponse
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from starlette import status
from database.settings import get_session
from services.user_auth import get_current_user
from crud.document import document_create, document_delete, create_formatting_suggestions, \
    get_formatting_suggestion_by_document_id,delete_formatting_suggestion
import aiofiles
import os

document_router = APIRouter(prefix="/document", tags=["document"])


@document_router.post("/create", response_model=DocumentResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_document(file: UploadFile = File(...),
                          db: AsyncSession = Depends(get_session),
                          current_user: User = Depends(get_current_user)
                          ):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .docx files are allowed."
        )

    out_file_path = f"uploaded_files/{file.filename}"

    os.makedirs(os.path.dirname(out_file_path), exist_ok=True)

    async with aiofiles.open(out_file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    document = await document_create(current_user.id, out_file_path, file.filename, db)

    return document


@document_router.delete("/delete/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int,
                          db: AsyncSession = Depends(get_session),
                          current_user: User = Depends(get_current_user)
                          ):
    await document_delete(current_user.id, document_id, db)

    return None


@document_router.post("/apa_style_check", response_model=FormattingSuggestionResponse,
                      status_code=status.HTTP_201_CREATED)
async def create_apa_style_check(document_id: int,
                          db: AsyncSession = Depends(get_session),
                          current_user: User = Depends(get_current_user)):
    response = await create_formatting_suggestions(document_id, db)
    return response


@document_router.get("/apa_style_suggestions/{document_id}", response_model=FormattingSuggestionResponse)
async def get_apa_style_suggestions(document_id: int, db: AsyncSession = Depends(get_session),
                                current_user: User = Depends(get_current_user)):
    response = await get_formatting_suggestion_by_document_id(document_id, db)
    return response

@document_router.delete("/apa_style_suggestions/{formatting_suggestion}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_apa_style_suggestions(formatting_suggestion: int, db: AsyncSession = Depends(get_session),
                                current_user: User = Depends(get_current_user)):
    await delete_formatting_suggestion(formatting_suggestion, db)
    return None