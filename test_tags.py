import requests
import json
import os

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_upload_with_tags():
    """Test uploading a document with tags."""
    # Path to a test PDF file
    pdf_path = "HOA rules.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Test file {pdf_path} not found. Please provide a valid PDF file.")
        return
    
    # Prepare the request
    url = f"{BASE_URL}/documents/upload"
    
    # Form data with tags
    files = {
        'file': (os.path.basename(pdf_path), open(pdf_path, 'rb'), 'application/pdf')
    }
    data = {
        'collection_name': 'test_collection',
        'tags': 'house,rules,important'
    }
    
    # Send the request
    response = requests.post(url, files=files, data=data)
    
    # Check the response
    if response.status_code == 201:
        print("Document uploaded successfully with tags.")
        print(response.json())
        
        # Get the document ID from the response
        # For this test, we'll need to query the collection to get a document ID
        return True
    else:
        print(f"Failed to upload document: {response.status_code}")
        print(response.text)
        return False

def test_query_with_tags():
    """Test querying documents with tag filters."""
    # Prepare the request
    url = f"{BASE_URL}/documents/query"
    
    # Query with tag filter
    data = {
        "collection_name": "test_collection",
        "query_text": "rules",
        "n_results": 5,
        "where": {"tags": {"$in": ["house"]}}
    }
    
    # Send the request
    response = requests.post(url, json=data)
    
    # Check the response
    if response.status_code == 200:
        print("Query executed successfully.")
        results = response.json()
        print(f"Found {len(results['results'])} documents matching the query and tag filter.")
        
        # Print the tags of each result
        for i, result in enumerate(results['results']):
            print(f"Result {i+1}:")
            print(f"  Text: {result['text'][:100]}...")
            print(f"  Tags: {result['metadata'].get('tags', 'No tags')}")
            print(f"  Score: {result['score']}")
            print()
        
        return True
    else:
        print(f"Failed to execute query: {response.status_code}")
        print(response.text)
        return False

def main():
    """Run the tests."""
    print("Testing document upload with tags...")
    upload_success = test_upload_with_tags()
    
    if upload_success:
        print("\nTesting query with tag filters...")
        test_query_with_tags()

if __name__ == "__main__":
    main()