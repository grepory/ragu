#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.chroma_client import chroma_client

# Test the delete functionality directly
collection_name = "test_collection"
source_filename = "tmpkluubbmy.pdf"

print(f"Testing deletion for collection: {collection_name}, source: {source_filename}")

# Get the collection
collection = chroma_client.get_or_create_collection(collection_name)

# Get all documents to see what's there
print("\n--- Before deletion ---")
all_docs = collection.get()
print(f"Total documents: {len(all_docs['ids']) if all_docs and all_docs.get('ids') else 0}")

if all_docs and all_docs.get('ids'):
    for i, doc_id in enumerate(all_docs['ids'][:5]):  # Show first 5
        metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') else {}
        print(f"ID: {doc_id}")
        print(f"Source: {metadata.get('source', 'N/A')}")
        print(f"Metadata keys: {list(metadata.keys())}")
        print("---")

# Try the deletion
print(f"\n--- Testing deletion ---")
try:
    result = collection.get(where={"source": source_filename})
    print(f"Found {len(result['ids']) if result and result.get('ids') else 0} documents matching source '{source_filename}'")
    
    if result and result.get('ids'):
        print(f"IDs to delete: {result['ids'][:5]}...")  # Show first 5
        collection.delete(ids=result['ids'])
        print(f"Deleted {len(result['ids'])} documents")
        
        # Check after deletion
        print("\n--- After deletion ---")
        remaining_docs = collection.get()
        print(f"Remaining documents: {len(remaining_docs['ids']) if remaining_docs and remaining_docs.get('ids') else 0}")
    else:
        print("No matching documents found for deletion")
        
except Exception as e:
    print(f"Error during deletion: {e}")
    import traceback
    traceback.print_exc()