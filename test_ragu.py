#!/usr/bin/env python3
"""
Test script for RAGU (Retrieval-Augmented Generation Utility)

This script tests the core functionality of the RAGU system:
1. Collection management
2. Document upload and retrieval
3. WebSocket chat interaction

To run this test, make sure the RAGU server is running:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Then run this script:
    python test_ragu.py
"""

import os
import json
import asyncio
import requests
import websockets
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
WEBSOCKET_URL = "ws://localhost:8000/api/v1/chat/ws"
TEST_COLLECTION = f"test_collection_{datetime.now().strftime('%Y%m%d%H%M%S')}"
TEST_TEXT = """
Retrieval-Augmented Generation (RAG) is an AI framework that enhances Large Language Model (LLM) outputs by 
incorporating relevant information retrieved from external knowledge sources. Unlike traditional LLMs that rely 
solely on their training data, RAG systems can access, retrieve, and leverage up-to-date or specialized information 
from databases, documents, or other sources.

The RAG process works in three main steps:
1. Retrieval: When a query is received, the system searches for and retrieves relevant information from its knowledge base.
2. Augmentation: The retrieved information is added to the prompt sent to the LLM.
3. Generation: The LLM generates a response based on both its internal knowledge and the retrieved information.

Benefits of RAG include:
- More accurate and up-to-date responses
- Reduced hallucinations (fabricated information)
- Ability to cite sources
- Customizable knowledge base
- Lower cost compared to fine-tuning

RAG is particularly useful for applications requiring factual accuracy, domain-specific knowledge, or access to 
current information beyond the LLM's training cutoff date.
"""


class Colors:
    """Terminal colors for better readability."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_step(message):
    """Print a step message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}[STEP] {message}{Colors.ENDC}")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


def print_info(message):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.ENDC}")


def test_collection_management():
    """Test collection management functionality."""
    print_step("Testing collection management")
    
    # Create collection
    try:
        response = requests.post(
            f"{BASE_URL}/collections/",
            json={"name": TEST_COLLECTION, "description": "Test collection for RAGU"}
        )
        response.raise_for_status()
        print_success(f"Created collection: {TEST_COLLECTION}")
    except Exception as e:
        print_error(f"Failed to create collection: {str(e)}")
        return False
    
    # List collections
    try:
        response = requests.get(f"{BASE_URL}/collections/")
        response.raise_for_status()
        collections = response.json()["collections"]
        if TEST_COLLECTION in collections:
            print_success(f"Collection {TEST_COLLECTION} found in list")
        else:
            print_error(f"Collection {TEST_COLLECTION} not found in list")
            return False
    except Exception as e:
        print_error(f"Failed to list collections: {str(e)}")
        return False
    
    return True


def test_document_management():
    """Test document management functionality."""
    print_step("Testing document management")
    
    # Add text to collection
    try:
        response = requests.post(
            f"{BASE_URL}/documents/text",
            json={
                "text": TEST_TEXT,
                "collection_name": TEST_COLLECTION,
                "metadata": {"source": "test_script", "type": "RAG information"}
            }
        )
        response.raise_for_status()
        result = response.json()
        print_success(f"Added text to collection: {result['chunks']} chunks")
        
        # Store document ID for later use
        document_id = None
    except Exception as e:
        print_error(f"Failed to add text: {str(e)}")
        return False
    
    # Query documents
    try:
        response = requests.post(
            f"{BASE_URL}/documents/query",
            json={
                "collection_name": TEST_COLLECTION,
                "query_text": "What is RAG?",
                "n_results": 3
            }
        )
        response.raise_for_status()
        result = response.json()
        
        if result["results"]:
            document_id = result["results"][0]["id"]
            print_success(f"Query successful: Found {len(result['results'])} results")
            print_info(f"First result: {result['results'][0]['text'][:100]}...")
        else:
            print_error("Query returned no results")
            return False
    except Exception as e:
        print_error(f"Failed to query documents: {str(e)}")
        return False
    
    # Get document by ID if we have one
    if document_id:
        try:
            response = requests.get(f"{BASE_URL}/documents/{TEST_COLLECTION}/{document_id}")
            response.raise_for_status()
            document = response.json()
            print_success(f"Retrieved document by ID: {document_id}")
            print_info(f"Document text: {document['text'][:100]}...")
        except Exception as e:
            print_error(f"Failed to get document by ID: {str(e)}")
            return False
    
    return True


async def test_websocket_chat():
    """Test WebSocket chat functionality."""
    print_step("Testing WebSocket chat")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Send chat message
            await websocket.send(json.dumps({
                "type": "chat",
                "collection_name": TEST_COLLECTION,
                "query": "Explain the three main steps of RAG in detail",
                "history": []
            }))
            
            print_success("Connected to WebSocket and sent query")
            print_info("Receiving response (this may take a few seconds)...")
            
            # Process responses
            full_response = ""
            sources_received = False
            
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                if data["type"] == "start":
                    print_info("Response generation started")
                
                elif data["type"] == "token":
                    # Just print the first few tokens
                    if len(full_response) < 100:
                        print(data["content"], end="", flush=True)
                    full_response += data["content"]
                
                elif data["type"] == "complete":
                    print("\n")
                    print_success("Response complete")
                    
                    if data["content"]["sources"]:
                        sources_received = True
                        print_info(f"Received {len(data['content']['sources'])} sources")
                    
                    break
                
                elif data["type"] == "error":
                    print_error(f"Error: {data['content']}")
                    return False
            
            if len(full_response) > 0 and sources_received:
                print_success("WebSocket chat test successful")
                return True
            else:
                print_error("WebSocket response incomplete")
                return False
                
    except Exception as e:
        print_error(f"WebSocket test failed: {str(e)}")
        return False


async def cleanup():
    """Clean up test resources."""
    print_step("Cleaning up test resources")
    
    # Delete test collection
    try:
        response = requests.delete(f"{BASE_URL}/collections/{TEST_COLLECTION}")
        if response.status_code == 204:
            print_success(f"Deleted test collection: {TEST_COLLECTION}")
        else:
            print_error(f"Failed to delete test collection: {response.text}")
    except Exception as e:
        print_error(f"Error during cleanup: {str(e)}")


async def run_tests():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}===== RAGU TEST SUITE ====={Colors.ENDC}")
    print(f"{Colors.BLUE}Testing RAGU at {BASE_URL}{Colors.ENDC}\n")
    
    try:
        # Test server connection
        response = requests.get(f"{BASE_URL.split('/api')[0]}/health")
        if response.status_code == 200:
            print_success("Server is running")
        else:
            print_error("Server is not responding correctly")
            return
    except Exception:
        print_error(f"Cannot connect to server at {BASE_URL}")
        print_info("Make sure the server is running with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Run tests
    collection_test = test_collection_management()
    if not collection_test:
        print_error("Collection management test failed, aborting remaining tests")
        return
    
    document_test = test_document_management()
    if not document_test:
        print_error("Document management test failed, aborting remaining tests")
        await cleanup()
        return
    
    websocket_test = await test_websocket_chat()
    
    # Clean up
    await cleanup()
    
    # Print summary
    print(f"\n{Colors.BOLD}{Colors.HEADER}===== TEST SUMMARY ====={Colors.ENDC}")
    print(f"Collection Management: {'✓' if collection_test else '✗'}")
    print(f"Document Management:   {'✓' if document_test else '✗'}")
    print(f"WebSocket Chat:        {'✓' if websocket_test else '✗'}")
    
    if collection_test and document_test and websocket_test:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed! RAGU is working correctly.{Colors.ENDC}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some tests failed. Please check the logs above.{Colors.ENDC}")


if __name__ == "__main__":
    asyncio.run(run_tests())