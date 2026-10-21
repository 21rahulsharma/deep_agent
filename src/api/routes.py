from fastapi import APIRouter
from .chat_api import router as chat_router
router = APIRouter()

router.include_router(chat_router)