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
- **FastAPI app** (`app/main.py`): Main application with CORS, static files, and Jinja2 templates
- **API router** (`app/api/api.py`): Centralized router including all endpoint modules
- **API routes** (`app/api/routes/`): Modular RESTful endpoints
  - `documents.py`: Document upload, retrieval, and management
  - `collections.py`: Vector collection operations
  - `chat.py`: WebSocket chat endpoint for streaming responses
  - `conversations.py`: Chat history management
  - `tags.py`: Document tagging and metadata operations  
  - `migration.py`: Database migration utilities
- **Vector database** (`app/db/chroma_client.py`): ChromaDB integration for document embeddings
- **LLM service** (`app/services/llm_service.py`): Multi-provider LLM integration (Ollama, Anthropic, OpenAI)
- **Document processing** (`app/utils/document_processor.py`): Text extraction and chunking
- **Data models** (`app/models/schemas.py`): Pydantic models for API requests/responses

### Key Features
- **Multi-provider LLM support**: Ollama (local), Anthropic Claude, OpenAI GPT
- **Document tagging**: Metadata-based document organization and filtering with advanced UI
- **WebSocket chat**: Real-time streaming chat with conversation history at `/api/v1/chat/ws`
- **Vector collections**: Organized document storage with semantic search
- **Web interface**: Responsive HTML/JS frontend with drag-drop upload and conversational UI
- **Conversation management**: Persistent chat history with sidebar navigation
- **Advanced tag filtering**: Multi-select tag filtering with search and autocomplete

### Data Flow
1. Documents uploaded via API → processed into chunks → embedded → stored in ChromaDB collections
2. Chat queries → semantic search for relevant chunks → LLM generates response with sources
3. Conversation history maintained for contextual follow-up questions
4. Tag-based filtering applied to document search and retrieval

### Configuration
- **Settings** (`app/core/config.py`): Pydantic-based configuration with environment variables
- **LLM providers**: Configurable via `DEFAULT_LLM_PROVIDER` environment variable
- **Model selection**: Runtime model selection via API `provider:model` format

### Frontend Components
- **Templates** (`app/templates/`): Jinja2 HTML templates
  - `index.html`: Main application shell with sidebar and content panels
  - `chat_interface.html`: Chat interface with model/tag selection
  - `file_management.html`: Document upload and management interface
- **Static assets** (`app/static/`): 
  - `css/styles.css`: Complete theme styling with CSS custom properties
  - `js/model-query.js`: Chat functionality and WebSocket handling
  - `js/pdf-upload.js`: File upload handling with progress tracking
- **UI Components**: Tag selection, model dropdown, conversation history, document management

### Database
- **ChromaDB**: Persistent vector storage in `./chroma_db/` directory
- **Collections**: Logical grouping of related documents with metadata
- **Conversation store** (`app/db/conversation_store.py`): JSON-based chat history persistence
- **Document metadata**: Rich tagging system with search and filtering capabilities

## UI Theme and Style Guidelines

### Color Scheme
RAGU uses a cohesive color palette defined as CSS custom properties in `app/static/css/styles.css`:

```css
:root {
    --oxford-stone: #C4B49D;    /* Primary accent, backgrounds */
    --joas-white: #DACBB4;      /* Light backgrounds, selected states */
    --salon-drab: #494135;      /* Primary text, borders, buttons */
    --smelt-black: #2E2E2E;     /* Secondary text, icons */
}
```

### Component Styling Guidelines

#### Buttons
- **Primary buttons**: `background-color: var(--salon-drab)`, `color: var(--joas-white)`
- **Secondary buttons**: `background-color: var(--oxford-stone)`, `border: var(--salon-drab)`
- **Hover effects**: Darken primary color (`#3a3328` for salon-drab)
- **Disabled state**: Use opacity and muted variants of theme colors

#### Form Controls
- **Background**: `var(--joas-white)` for inputs, `var(--oxford-stone)` for containers
- **Borders**: `rgba(73, 65, 53, 0.2)` for subtle borders, full `var(--salon-drab)` for focus
- **Focus states**: `box-shadow: 0 0 0 0.2rem rgba(73, 65, 53, 0.25)`

#### Tags and Badges
- **Selected tags**: `background: var(--salon-drab)`, `color: var(--joas-white)`
- **Unselected tags**: `background: var(--joas-white)`, `border: var(--oxford-stone)`
- **Tag counts**: Small badges with `rgba(73, 65, 53, 0.15)` background

#### Modals and Overlays
- **Modal background**: `var(--oxford-stone)` with `var(--salon-drab)` headers
- **Overlay**: `rgba(73, 65, 53, 0.8)` for backdrop
- **Modal headers**: Dark (`var(--salon-drab)`) with light text (`var(--joas-white)`)

#### Layout Components
- **Sidebar**: `#E2D5C1` background with `#5C5244` header sections
- **Main content**: `var(--oxford-stone)` background
- **Navigation**: `#5C5244` top navigation with light text
- **Chat interface**: Consistent theme colors with proper contrast ratios

### Accessibility Considerations
- Maintain sufficient color contrast ratios (minimum 4.5:1 for normal text)
- Use theme colors consistently across all components
- Provide focus indicators with themed box-shadow effects
- Ensure interactive elements have clear hover/active states

### CSS Architecture
- All theme colors are defined as CSS custom properties in `:root`
- Components use `var(--color-name)` references throughout
- Consistent spacing using rem units and standard Bootstrap-compatible sizing
- Responsive design with mobile-first approach for smaller screens

## Important Notes

- The application auto-detects and handles common dependency issues (see `run_app.py` error handling)
- WebSocket endpoint at `/api/v1/chat/ws` for streaming responses
- Document tags support filtering with ChromaDB metadata queries (`$in`, `$eq`, etc.)
- LLM provider switching without restart via API model parameter
- Theme colors should be used consistently across all UI components
- CSS custom properties enable easy theme maintenance and consistency