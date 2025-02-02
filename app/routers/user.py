from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database.settings import get_session
from schemas.user import UserCreateSchemas, UserResponseSchemas
from services.user_auth import login_user, get_current_user
import crud.user as crud_user
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from schemas.document import DocumentResponseSchema
from models.user import User

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.post("/sign_up", response_model=UserResponseSchemas, status_code=status.HTTP_201_CREATED)
async def sign_up(user: UserCreateSchemas, db: AsyncSession = Depends(get_session)):
    user = await crud_user.create_user(db, user)
    return user


@user_router.post("/login")
async def login(user: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    user = await login_user(db, user)
    return user


@user_router.get('/info', summary='Get details of currently logged in user', response_model=UserResponseSchemas)
async def get_me(token: str = Depends(get_current_user)):
    return token


@user_router.get('/documents', summary='Get all user documents', response_model=List[DocumentResponseSchema])
async def get_documents(
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)):
    response = await crud_user.get_user_documents(current_user.id, db)
    return response
