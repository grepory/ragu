import os
from enum import Enum
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class LLMProvider(str, Enum):
    """Enum for LLM providers."""
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RAG Management System"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Vector DB settings
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./chroma_db",
        description="Directory where ChromaDB will persist data"
    )
    
    # LLM provider settings
    DEFAULT_LLM_PROVIDER: LLMProvider = Field(
        default=LLMProvider(os.getenv("DEFAULT_LLM_PROVIDER", "ollama")),
        description="Default LLM provider to use (ollama, anthropic, openai)"
    )
    
    # Ollama settings
    OLLAMA_BASE_URL: str = Field(
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        description="Base URL for Ollama API (local or remote)"
    )
    OLLAMA_DEFAULT_MODEL: str = Field(
        default=os.getenv("OLLAMA_DEFAULT_MODEL", "llama2"),
        description="Default Ollama model to use"
    )
    OLLAMA_EMBED_MODEL: str = Field(
        default=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        description="Ollama embedding model to use"
    )
    
    # Anthropic settings
    ANTHROPIC_API_KEY: str = Field(
        default=os.getenv("ANTHROPIC_API_KEY", ""),
        description="Anthropic API key"
    )
    ANTHROPIC_DEFAULT_MODEL: str = Field(
        default=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-haiku-20240307"),
        description="Default Anthropic model to use"
    )
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(
        default=os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key"
    )
    OPENAI_DEFAULT_MODEL: str = Field(
        default=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o"),
        description="Default OpenAI model to use"
    )
    
    # Mistral settings
    MISTRAL_API_KEY: str = Field(
        default=os.getenv("MISTRAL_API_KEY", ""),
        description="Mistral API key for OCR services"
    )
    MISTRAL_BASE_URL: str = Field(
        default=os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai"),
        description="Base URL for Mistral API"
    )
    
    # For backward compatibility
    DEFAULT_MODEL: str = Field(
        default=os.getenv("DEFAULT_MODEL", "llama2"),
        description="Default LLM model to use (legacy, use provider-specific settings instead)"
    )
    
    # Document settings
    CHUNK_SIZE: int = Field(
        default=1000,
        description="Size of text chunks for document processing"
    )
    CHUNK_OVERLAP: int = Field(
        default=200,
        description="Overlap between text chunks"
    )
    MAX_FILE_SIZE_MB: int = Field(
        default=30,
        description="Maximum file size in MB for document upload"
    )
    PROCESSING_TIMEOUT_SECONDS: int = Field(
        default=60,
        description="Maximum time in seconds to process a document"
    )

    class Config:
        case_sensitive = True
        env_file = ".env"


# Create global settings object
settings = Settings()