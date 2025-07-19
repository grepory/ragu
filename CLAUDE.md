# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Start server**: `python run_app.py` (recommended) - includes error handling and auto-opens browser
- **Manual start**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Install dependencies**: `pip install -r requirements.txt`

### Testing
- Test files are present (`test_*.py`) but no standardized test runner is configured
- Individual test files can be run with `python test_<name>.py`

### Environment Setup
- Copy `.env.example` to `.env` and configure LLM providers
- Required for API keys (Anthropic, OpenAI) or Ollama configuration

## Architecture Overview

RAGU is a FastAPI-based RAG (Retrieval-Augmented Generation) system with the following key components:

### Core Architecture
- **FastAPI app** (`app/main.py`): Main application with CORS, static files, and template serving
- **API routes** (`app/api/`): RESTful endpoints for collections, documents, chat, and conversations
- **Vector database** (`app/db/chroma_client.py`): ChromaDB integration for document embeddings
- **LLM service** (`app/services/llm_service.py`): Multi-provider LLM integration (Ollama, Anthropic, OpenAI)
- **Document processing** (`app/utils/document_processor.py`): Text extraction and chunking

### Key Features
- **Multi-provider LLM support**: Ollama (local), Anthropic Claude, OpenAI GPT
- **Document tagging**: Metadata-based document organization and filtering
- **WebSocket chat**: Real-time streaming chat with conversation history
- **Vector collections**: Organized document storage with semantic search
- **Web interface**: HTML/JS frontend with drag-drop upload and conversational UI

### Data Flow
1. Documents uploaded via API → processed into chunks → embedded → stored in ChromaDB collections
2. Chat queries → semantic search for relevant chunks → LLM generates response with sources
3. Conversation history maintained for contextual follow-up questions

### Configuration
- **Settings** (`app/core/config.py`): Pydantic-based configuration with environment variables
- **LLM providers**: Configurable via `DEFAULT_LLM_PROVIDER` environment variable
- **Model selection**: Runtime model selection via API `provider:model` format

### Frontend
- **Templates** (`app/templates/`): Jinja2 HTML templates
- **Static assets** (`app/static/`): CSS and JavaScript for document upload and chat interface
- **Model selection**: Dynamic model switching in chat interface

### Database
- **ChromaDB**: Persistent vector storage in `./chroma_db/` directory
- **Collections**: Logical grouping of related documents
- **Conversation store** (`app/db/conversation_store.py`): Chat history persistence

## Important Notes

- The application auto-detects and handles common dependency issues (see `run_app.py` error handling)
- WebSocket endpoint at `/api/v1/chat/ws` for streaming responses
- Document tags support filtering with ChromaDB metadata queries (`$in`, `$eq`, etc.)
- LLM provider switching without restart via API model parameter