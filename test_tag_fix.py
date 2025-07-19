import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

def test_add_text_with_tags():
    """Test adding text with tags to verify the tag handling fix."""
    # Prepare the request
    url = f"{BASE_URL}/documents/text"
    
    # JSON data with tags
    data = {
        "text": "This is a test document for the house collection with house tag.",
        "collection_name": "house",
        "tags": ["house"]
    }
    
    # Send the request
    response = requests.post(url, json=data)
    
    # Check the response
    if response.status_code == 201:
        print("Text added successfully with tags.")
        print(response.json())
        return True
    else:
        print(f"Failed to add text: {response.status_code}")
        print(response.text)
        return False

def test_query_with_tags():
    """Test querying documents with tag filters."""
    # Prepare the request
    url = f"{BASE_URL}/documents/query"
    
    # Query with tag filter
    data = {
        "collection_name": "house",
        "query_text": "house",
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
    print("Testing adding text with tags...")
    add_success = test_add_text_with_tags()
    
    if add_success:
        print("\nTesting query with tag filters...")
        test_query_with_tags()

if __name__ == "__main__":
    main()