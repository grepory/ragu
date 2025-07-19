from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.api import api_router

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - API Documentation",
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "message": "RAG Management System is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)