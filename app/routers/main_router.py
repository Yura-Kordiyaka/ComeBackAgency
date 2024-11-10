from fastapi import APIRouter
from .user import user_router
from .document import document_router
router = APIRouter(
    prefix="/v1",
)
router.include_router(user_router)
router.include_router(document_router)
