from fastapi import APIRouter

from app.api.routes import documents, collections, chat, conversations, tags, migration

api_router = APIRouter()

# Include routers for different API endpoints
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(migration.router, prefix="/migration", tags=["migration"])