#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.chroma_client import chroma_client

# Check the actual source paths in the house collection
collection_name = "house"

print(f"Checking collection: {collection_name}")

# Get the collection
collection = chroma_client.get_or_create_collection(collection_name)

# Get all documents to see what's there
print("\n--- Raw ChromaDB data ---")
all_docs = collection.get()
print(f"Total documents: {len(all_docs['ids']) if all_docs and all_docs.get('ids') else 0}")

if all_docs and all_docs.get('ids'):
    for i, doc_id in enumerate(all_docs['ids'][:3]):  # Show first 3
        metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') else {}
        print(f"ID: {doc_id}")
        print(f"Source: '{metadata.get('source', 'N/A')}'")
        print("---")