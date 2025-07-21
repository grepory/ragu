# Getting Started with RAGU

This guide will help you get started with RAGU (Retrieval-Augmented Generation Utility), a complete RAG management and interrogation system.

## Quick Start

### Prerequisites

- Python 3.8 or higher
- One or more of the following LLM providers:
  - Ollama installed locally or access to a remote Ollama instance
  - Anthropic API key (for Claude models)
  - OpenAI API key (for GPT models)

### Installation

1. Clone the repository or download the source code.

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the `.env.example` file to `.env` in the project root and update it with your LLM provider configuration:
   ```bash
   cp .env.example .env
   # Then edit the .env file with your preferred text editor
   ```
   
   Note: 
   - The `.env.example` file contains all the necessary environment variables with default values and explanatory comments.
   - If you're using a remote Ollama instance, update the OLLAMA_BASE_URL accordingly.
   - You only need to configure the providers you plan to use.

### Running the Server

Start the RAGU server with:

```bash
python run_app.py
```

This will:
- Start the server on port 8000
- Display clear URLs for accessing the application
- Automatically open your default web browser to the frontend

Alternatively, you can start the server manually with:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at http://localhost:8000, and the API documentation at http://localhost:8000/docs.

### Testing the Installation

To verify that everything is working correctly, run the test script:

```bash
python test_ragu.py
```

This script will test all the core functionality of the system, including collection management, document processing, and WebSocket chat.

## Basic Usage

### 1. Create a Collection

First, create a collection to store your documents:

```bash
curl -X POST http://localhost:8000/api/v1/collections/ \
  -H "Content-Type: application/json" \
  -d '{"name": "my_collection", "description": "My first collection"}'
```

### 2. Add Documents

Upload a document to your collection:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@path/to/your/document.pdf" \
  -F "collection_name=my_collection"
```

Or add text directly:

```bash
curl -X POST http://localhost:8000/api/v1/documents/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is some text to add to the vector database.",
    "collection_name": "my_collection",
    "metadata": {"source": "direct_input"}
  }'
```

### 3. Query Documents

Search for documents semantically similar to a query:

```bash
curl -X POST http://localhost:8000/api/v1/documents/query \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my_collection",
    "query_text": "What is retrieval-augmented generation?",
    "n_results": 5
  }'
```

### 4. Chat with the RAG System

For a simple chat interaction, use the REST endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my_collection",
    "query": "Explain retrieval-augmented generation in simple terms.",
    "model": "ollama:llama2"
  }'
```

You can specify which LLM provider and model to use by setting the `model` parameter in your requests. The format is `provider:model`. For example:

- `ollama:llama2` - Use Ollama with the llama2 model
- `anthropic:claude-3-haiku-20240307` - Use Anthropic with the Claude 3 Haiku model
- `openai:gpt-4o` - Use OpenAI with the GPT-4o model

If you don't specify a provider, the default provider from your configuration will be used. If you don't specify a model, the default model for the selected provider will be used.

For a more interactive experience with streaming responses, use the WebSocket endpoint at `ws://localhost:8000/api/v1/chat/ws`. See the README.md for detailed WebSocket usage examples.

## Next Steps

- Check out the full API documentation at http://localhost:8000/docs
- Explore the Python client example in the README.md
- Customize the system by modifying the configuration in `app/core/config.py`

## Troubleshooting

### Common Issues

1. **Connection refused**: Make sure the server is running and accessible at the specified host and port.

2. **Ollama connection errors**: Verify that Ollama is running and accessible at the URL specified in the OLLAMA_BASE_URL environment variable. For local instances, ensure Ollama is running on port 11434.

3. **API key errors**: If using Anthropic or OpenAI, ensure that you have set the correct API keys in your environment variables (ANTHROPIC_API_KEY or OPENAI_API_KEY).

4. **Model not found errors**: Ensure that the model you're trying to use is available with your selected provider. For Ollama, you may need to pull the model first with `ollama pull model_name`.

5. **Provider not installed**: If you see errors about missing modules for a specific provider, make sure you've installed the required packages with `pip install -r requirements.txt`.

6. **Missing dependencies**: If you encounter import errors, make sure all dependencies are installed with `pip install -r requirements.txt`.

7. **Permission errors**: Ensure that the application has write permissions for the `chroma_db` directory.

8. **Document upload errors**: If you see an error like "Failed to extract content from '[filename]'", the document might be in a format that can't be processed properly. Try the following:
   - Check if the document is password-protected or encrypted
   - Convert the document to a different format (e.g., from PDF to DOCX)
   - For PDFs, ensure they contain actual text content and not just scanned images
   - Try splitting large documents into smaller chunks before uploading

9. **Embedding function errors**: If you see an error like "You must provide an embedding function to compute embeddings", ensure that you have properly configured your LLM provider settings in the .env file. The system uses embedding functions from your configured LLM provider (OpenAI or Ollama) and falls back to a default embedding function if neither is available.

### Getting Help

If you encounter any issues not covered here, please:

1. Check the detailed documentation in the README.md
2. Look for error messages in the server logs
3. Consult the FastAPI or ChromaDB documentation for specific component issues

## System Architecture

RAGU consists of several key components:

1. **FastAPI Backend**: Handles HTTP requests and WebSocket connections
2. **ChromaDB**: Vector database for storing and retrieving document embeddings
3. **Document Processor**: Processes and chunks documents for storage
4. **LLM Service**: Integrates with multiple LLM providers:
   - Ollama for local or remote models
   - Anthropic for Claude models
   - OpenAI for GPT models
5. **Web Interface**: HTML/JS frontend with file upload and conversational UI

Understanding this architecture can help you customize and extend the system for your specific needs.