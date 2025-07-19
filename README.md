# RAGU: Retrieval-Augmented Generation Utility

RAGU is a complete RAG (Retrieval-Augmented Generation) management and interrogation system built with FastAPI, ChromaDB, and LangChain. It provides a powerful API for document management, vector storage, and LLM-powered chat functionality.

## Features

- **Document Management**: Upload, process, and manage documents in vector collections
- **Document Tagging**: Add tags to documents for better organization and filtering
- **Vector Database**: ChromaDB integration for efficient semantic search
- **LLM Integration**: Support for multiple LLM providers:
  - Ollama with local or remote models (including nomic-embed-text)
  - Anthropic with Claude models (including haiku)
  - OpenAI with GPT models (including 4o)
- **WebSocket Chat**: Real-time, streaming chat interface with RAG capabilities
- **REST API**: Comprehensive REST API for all operations
- **Document Processing**: Support for various document types (PDF, DOCX, CSV, text)

## Installation

### Prerequisites

- Python 3.8+
- [Optional] Virtual environment (recommended)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ragu.git
   cd ragu
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the `.env.example` file to `.env` in the project root and update it with your LLM provider configuration:
   ```bash
   cp .env.example .env
   # Then edit the .env file with your preferred text editor
   ```
   
   The `.env.example` file contains all the necessary environment variables with default values and explanatory comments. You only need to configure the providers you plan to use.

## Running the Application

Start the server with:

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

The API will be available at http://localhost:8000, and the API documentation at http://localhost:8000/docs.

## API Documentation

### Collections API

Collections are used to organize documents in the vector database.

#### Create a Collection

```http
POST /api/v1/collections/
Content-Type: application/json

{
  "name": "my_collection",
  "description": "My first collection"
}
```

#### List Collections

```http
GET /api/v1/collections/
```

#### Get Collection

```http
GET /api/v1/collections/{collection_name}
```

#### Delete Collection

```http
DELETE /api/v1/collections/{collection_name}
```

### Documents API

Documents are the core content stored in the vector database.

#### Upload a Document

```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: [file]
collection_name: my_collection
tags: personal,house,important
additional_metadata: {"source": "website", "author": "John Doe"}
```

The `tags` parameter is optional and should be a comma-separated list of tags to associate with the document.

#### Add Text Directly

```http
POST /api/v1/documents/text
Content-Type: application/json

{
  "text": "This is some text to add to the vector database.",
  "collection_name": "my_collection",
  "tags": ["personal", "notes", "important"],
  "metadata": {"source": "direct_input", "author": "Jane Smith"}
}
```

The `tags` parameter is optional and should be an array of strings representing tags to associate with the document.

#### Get Document

```http
GET /api/v1/documents/{collection_name}/{document_id}
```

#### Delete Document

```http
DELETE /api/v1/documents/{collection_name}/{document_id}
```

#### Query Documents

```http
POST /api/v1/documents/query
Content-Type: application/json

{
  "collection_name": "my_collection",
  "query_text": "What is retrieval-augmented generation?",
  "n_results": 5,
  "where": {
    "tags": {"$in": ["personal", "important"]}
  }
}
```

The `where` parameter is optional and can be used to filter documents by metadata fields, including tags. In the example above, the query will only return documents that have either the "personal" or "important" tag. You can use other operators like `$eq` for exact match or `$contains` for substring match.

### Chat API

The Chat API provides both REST and WebSocket interfaces for interacting with the LLM.

#### Model Selection

You can specify which LLM provider and model to use by setting the `model` parameter in your requests. The format is:

```
provider:model
```

For example:
- `ollama:llama2` - Use Ollama with the llama2 model
- `anthropic:claude-3-haiku-20240307` - Use Anthropic with the Claude 3 Haiku model
- `openai:gpt-4o` - Use OpenAI with the GPT-4o model

If you don't specify a provider, the default provider from your configuration will be used. If you don't specify a model, the default model for the selected provider will be used.

#### REST Chat Endpoint

```http
POST /api/v1/chat/
Content-Type: application/json

{
  "collection_name": "my_collection",
  "query": "What is retrieval-augmented generation?",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there! How can I help you?"}
  ],
  "model": "llama2"
}
```

#### WebSocket Chat

Connect to the WebSocket endpoint at `/api/v1/chat/ws` and send JSON messages with the following format:

```json
{
  "type": "chat",
  "collection_name": "my_collection",
  "query": "What is retrieval-augmented generation?",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there! How can I help you?"}
  ],
  "model": "llama2"
}
```

The server will respond with messages in the following formats:

1. Start message:
```json
{
  "type": "start",
  "content": "Generating response..."
}
```

2. Token messages (streaming):
```json
{
  "type": "token",
  "content": "piece of text"
}
```

3. Complete message:
```json
{
  "type": "complete",
  "content": {
    "answer": "The complete answer...",
    "sources": [
      {
        "id": "document_id",
        "text": "Snippet of the source document...",
        "metadata": {"source": "document.pdf", "page": 1}
      }
    ],
    "history": [
      {"role": "user", "content": "What is RAG?"},
      {"role": "assistant", "content": "The complete answer..."}
    ]
  }
}
```

4. Error message:
```json
{
  "type": "error",
  "content": "Error message"
}
```

## Examples

### Python Client Example

Here's a simple Python client for interacting with the API:

```python
import requests
import websockets
import json
import asyncio

BASE_URL = "http://localhost:8000/api/v1"

# Create a collection
def create_collection(name, description=None):
    response = requests.post(
        f"{BASE_URL}/collections/",
        json={"name": name, "description": description}
    )
    return response.json()

# Upload a document
def upload_document(file_path, collection_name, tags=None, metadata=None):
    files = {"file": open(file_path, "rb")}
    data = {"collection_name": collection_name}
    if tags:
        data["tags"] = ",".join(tags)
    if metadata:
        data["additional_metadata"] = json.dumps(metadata)
    
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        files=files,
        data=data
    )
    return response.json()

# Query documents
def query_documents(collection_name, query_text, n_results=5, tags=None):
    query_data = {
        "collection_name": collection_name,
        "query_text": query_text,
        "n_results": n_results
    }
    
    # Add tag filtering if specified
    if tags:
        query_data["where"] = {"tags": {"$in": tags}}
    
    response = requests.post(
        f"{BASE_URL}/documents/query",
        json=query_data
    )
    return response.json()

# WebSocket chat client
async def chat_websocket(collection_name, query, history=None, model=None):
    uri = f"ws://localhost:8000/api/v1/chat/ws"
    async with websockets.connect(uri) as websocket:
        # Send chat message
        await websocket.send(json.dumps({
            "type": "chat",
            "collection_name": collection_name,
            "query": query,
            "history": history or [],
            "model": model
        }))
        
        # Process responses
        full_response = ""
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "token":
                # Print token as it arrives
                print(data["content"], end="", flush=True)
                full_response += data["content"]
            
            elif data["type"] == "complete":
                # Chat complete
                print("\n\nSources:")
                for i, source in enumerate(data["content"]["sources"]):
                    print(f"{i+1}. {source['text']} (ID: {source['id']})")
                
                return data["content"]
            
            elif data["type"] == "error":
                # Error occurred
                print(f"\nError: {data['content']}")
                return None

# Example usage
if __name__ == "__main__":
    # Create a collection
    create_collection("my_docs", "My documents collection")
    
    # Upload a document with tags
    upload_document(
        "path/to/document.pdf", 
        "my_docs", 
        tags=["house", "important", "insurance"],
        metadata={"source": "local", "author": "Insurance Company"}
    )
    
    # Upload another document with different tags
    upload_document(
        "path/to/another_document.pdf", 
        "my_docs", 
        tags=["personal", "important", "legal"],
        metadata={"source": "local", "author": "Law Firm"}
    )
    
    # Query documents without tag filtering
    results = query_documents("my_docs", "What is RAG?")
    
    # Query documents with tag filtering (only "house" tagged documents)
    house_results = query_documents("my_docs", "What is RAG?", tags=["house"])
    
    # Query documents with multiple tag filtering (documents tagged as either "important" or "personal")
    important_results = query_documents("my_docs", "What is RAG?", tags=["important", "personal"])
    
    # Chat with WebSocket
    asyncio.run(chat_websocket("my_docs", "Explain RAG in simple terms."))
```

## Project Structure

```
ragu/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── collections.py
│   │   │   └── documents.py
│   │   └── api.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── chroma_client.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   └── llm_service.py
│   ├── utils/
│   │   └── document_processor.py
│   └── main.py
├── chroma_db/
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.