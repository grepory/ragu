#!/usr/bin/env python3
"""
Test script to verify document upload functionality.
"""

import requests
import sys
import os

def test_upload_document(file_path, collection_name="test_collection"):
    """
    Test uploading a document to the API.
    
    Args:
        file_path: Path to the document to upload
        collection_name: Name of the collection to upload to
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return
    
    print(f"Uploading {file_path} to collection {collection_name}...")
    
    # Prepare the file and form data
    files = {"file": open(file_path, "rb")}
    data = {"collection_name": collection_name}
    
    try:
        # Make the request to the API
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files=files,
            data=data
        )
        
        # Check the response
        if response.status_code == 201:
            print("Success!")
            print(response.json())
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"Exception: {str(e)}")
    finally:
        # Close the file
        files["file"].close()

if __name__ == "__main__":
    # Use the file path from command line argument or default to "HOA rules.pdf"
    file_path = sys.argv[1] if len(sys.argv) > 1 else "HOA rules.pdf"
    test_upload_document(file_path)