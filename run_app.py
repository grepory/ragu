#!/usr/bin/env python3
"""
Wrapper script for running the RAG Management System application.
This script provides helpful error messages when the application fails to start.
"""

import sys
import traceback
import webbrowser
import time
import threading

def open_browser():
    """Open the browser after a short delay to ensure the server is up."""
    time.sleep(2)  # Wait for the server to start
    url = "http://localhost:8000"
    webbrowser.open(url)
    print(f"\n✅ Browser opened automatically at {url}")

def main():
    """Run the application with error handling."""
    try:
        # Try to import and run the application
        from app.main import app
        import uvicorn
        
        # If we get here, the imports succeeded
        print("Starting RAG Management System...")
        print("\n🌐 Access the application in your browser at: http://localhost:8000")
        print("   API documentation available at: http://localhost:8000/docs")
        
        # Start browser in a separate thread
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Run the application
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError as e:
        # Handle import errors
        if "cannot import name 'Ollama' from 'llama_index.llms'" in str(e):
            print("\n===== ERROR: Ollama Import Failed =====")
            print("The application failed to start because it couldn't import the Ollama class.")
            print("\nPossible solutions:")
            print("1. Install the llama-index-llms-ollama package:")
            print("   pip install llama-index-llms-ollama")
            print("\n2. Update your .env file to use a different LLM provider:")
            print("   DEFAULT_LLM_PROVIDER=anthropic  # if you have Anthropic API key")
            print("   DEFAULT_LLM_PROVIDER=openai     # if you have OpenAI API key")
            print("\n3. Update the llama-index packages:")
            print("   pip install -U llama-index llama-index-core llama-index-llms-ollama")
            print("\nFull error message:")
            print(str(e))
        elif "proxies" in str(e) and "openai" in str(e).lower():
            print("\n===== ERROR: OpenAI Client Version Mismatch =====")
            print("The application failed to start because of a version mismatch between ChromaDB and OpenAI.")
            print("\nPossible solutions:")
            print("1. Update the ChromaDB package:")
            print("   pip install -U chromadb")
            print("\n2. Update the OpenAI package:")
            print("   pip install -U openai")
            print("\n3. If you're still having issues, try using a different embedding function by modifying app/db/chroma_client.py")
            print("\nFull error message:")
            print(str(e))
        elif "cannot import name 'LLM' from 'llama_index.core.base.llms.types'" in str(e):
            print("\n===== ERROR: LLM Import Failed =====")
            print("The application failed to start because of a version mismatch in the llama-index packages.")
            print("\nPossible solutions:")
            print("1. Update all llama-index packages:")
            print("   pip install -U llama-index llama-index-core llama-index-llms-ollama llama-index-llms-anthropic llama-index-llms-openai")
            print("\n2. Fix the import in app/services/llm_service.py:")
            print("   Change 'from llama_index.core.base.llms.types import ChatResponse, MessageRole, LLM'")
            print("   to 'from llama_index.core.llms.base import LLM'")
            print("   and 'from llama_index.core.base.llms.types import ChatResponse, MessageRole'")
            print("\n3. If you're still having issues, consider downgrading to compatible versions:")
            print("   pip install llama-index==0.9.48 llama-index-core==0.9.48")
            print("\nFull error message:")
            print(str(e))
        else:
            # Generic import error
            print("\n===== ERROR: Import Failed =====")
            print(f"The application failed to start because of an import error: {str(e)}")
            print("\nThis might be due to missing or incompatible packages.")
            print("Try updating your dependencies:")
            print("   pip install -U -r requirements.txt")
            print("\nFull error message:")
            print(str(e))
    except Exception as e:
        # Handle other errors
        print("\n===== ERROR: Application Failed to Start =====")
        print(f"The application failed to start with error: {str(e)}")
        print("\nStack trace:")
        traceback.print_exc()
        print("\nPlease check your configuration and dependencies.")

if __name__ == "__main__":
    main()