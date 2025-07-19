#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.chroma_client import chroma_client

# Test the delete functionality using our new method
collection_name = "test_collection"
source_filename = "tmpkluubbmy.pdf"

print(f"Testing deletion for collection: {collection_name}, source: {source_filename}")

# Check before deletion
print("\n--- Before deletion ---")
docs_before = chroma_client.get_collection_documents(collection_name)
print(f"Total document groups: {len(docs_before.get('documents', []))}")

# Try the deletion using our new method
print(f"\n--- Testing deletion with new method ---")
try:
    chunks_deleted = chroma_client.delete_documents_by_source(collection_name, source_filename)
    print(f"Deleted {chunks_deleted} chunks")
    
    # Check after deletion
    print("\n--- After deletion ---")
    docs_after = chroma_client.get_collection_documents(collection_name)
    print(f"Remaining document groups: {len(docs_after.get('documents', []))}")
    
except Exception as e:
    print(f"Error during deletion: {e}")
    import traceback
    traceback.print_exc()