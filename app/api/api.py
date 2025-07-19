from fastapi import APIRouter

from app.api.routes import documents, collections, chat

api_router = APIRouter()

# Include routers for different API endpoints
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])