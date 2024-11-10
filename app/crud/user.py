import schemas.user
import schemas.token
from models.user import User
from fastapi import Depends, HTTPException
from database.settings import get_session
from schemas.user import UserResponseSchemas, UserCreateSchemas
from services.user_auth import create_access_token, create_refresh_token, get_hashed_password
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.document import Document
from schemas.document import DocumentResponseSchema
from typing import List

async def create_user(db: Depends(get_session), user_in: UserCreateSchemas) -> UserResponseSchemas:
    user_in.password = get_hashed_password(user_in.password)
    existing_user = await db.execute(select(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)))
    existing_user = existing_user.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    user = User(**user_in.dict())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    access = await create_access_token(user.id)
    refresh = await create_refresh_token(user.id)
    token = schemas.token.Token(access_token=access, refresh_token=refresh)
    return UserResponseSchemas(**user_in.dict(), id=user.id, token=token)


async def get_user_documents(user_id: int, db: AsyncSession) -> List[DocumentResponseSchema]:
    result = await db.execute(
        select(Document).where(Document.user_id == user_id)
    )
    documents = result.scalars().all()
    return [DocumentResponseSchema.from_orm(doc) for doc in documents]