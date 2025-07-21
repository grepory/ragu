import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction, ONNXMiniLM_L6_V2

from app.core.config import settings

class ChromaClient:
    """Client for interacting with ChromaDB vector database."""
    
    # Constants
    DOCUMENTS_COLLECTION = "documents"  # Single collection for all documents
    
    def __init__(self):
        """Initialize ChromaDB client."""
        # Ensure persistence directory exists
        os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        # Try to use the embedding function based on the configured LLM provider
        # Always try ONNX first as it's more stable and avoids CoreML issues
        try:
            # Try to use optimized ONNX embedding function (avoids CoreML warnings)
            import platform
            providers = []
            
            # Configure providers based on platform for best performance
            if platform.system() == "Darwin":  # macOS
                # Use CPU provider to avoid CoreML issues that cause warnings
                providers = ["CPUExecutionProvider"]
            elif platform.system() == "Windows":
                providers = ["CPUExecutionProvider"]
            else:  # Linux
                providers = ["CPUExecutionProvider"]
            
            self.default_ef = ONNXMiniLM_L6_V2(preferred_providers=providers)
            print(f"Using optimized ONNX embedding function (providers: {providers})")
            
        except Exception as onnx_error:
            print(f"Failed to initialize ONNX embedding function: {onnx_error}")
            
            # Try provider-specific embedding functions
            if settings.DEFAULT_LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
                try:
                    # Try to use OpenAI embedding function
                    self.default_ef = embedding_functions.OpenAIEmbeddingFunction(
                        api_key=settings.OPENAI_API_KEY,
                        model_name="text-embedding-ada-002"
                    )
                    print("Using OpenAI embedding function")
                except Exception as e:
                    print(f"Failed to initialize OpenAI embedding function: {e}")
                    # Fall back to DefaultEmbeddingFunction
                    self.default_ef = DefaultEmbeddingFunction()
                    print("Using ChromaDB's DefaultEmbeddingFunction as fallback")
            elif settings.DEFAULT_LLM_PROVIDER == "ollama" and settings.OLLAMA_EMBED_MODEL:
                try:
                    # Try to use Ollama embedding function if available
                    from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
                    self.default_ef = OllamaEmbeddingFunction(
                        url=settings.OLLAMA_BASE_URL,
                        model_name=settings.OLLAMA_EMBED_MODEL
                    )
                    print(f"Using Ollama embedding function with model {settings.OLLAMA_EMBED_MODEL}")
                except Exception as e:
                    print(f"Failed to initialize Ollama embedding function: {e}")
                    # Fall back to DefaultEmbeddingFunction
                    self.default_ef = DefaultEmbeddingFunction()
                    print("Using ChromaDB's DefaultEmbeddingFunction as fallback")
            else:
                # Use DefaultEmbeddingFunction as a final fallback
                self.default_ef = DefaultEmbeddingFunction()
                print("Using ChromaDB's DefaultEmbeddingFunction as fallback")
    
    def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
        """Get or create a collection in ChromaDB.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB collection
        """
        try:
            return self.client.get_collection(
                name=collection_name,
                embedding_function=self.default_ef
            )
        except ValueError:
            return self.client.create_collection(
                name=collection_name,
                embedding_function=self.default_ef
            )
    
    def list_collections(self) -> List[str]:
        """List all collections in ChromaDB.
        
        Returns:
            List of collection names
        """
        return [col.name for col in self.client.list_collections()]
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection from ChromaDB.
        
        Args:
            collection_name: Name of the collection to delete
        """
        self.client.delete_collection(collection_name)
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs
        """
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def query_collection(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query a collection for similar documents.
        
        Args:
            collection_name: Name of the collection
            query_text: Query text
            n_results: Number of results to return
            where: Optional filter criteria
            
        Returns:
            Query results
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
    
    def get_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Dict[str, Any]:
        """Get a document by ID.
        
        Args:
            collection_name: Name of the collection
            document_id: Document ID
            
        Returns:
            Document data
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.get(ids=[document_id])
    
    def delete_document(
        self,
        collection_name: str,
        document_id: str
    ) -> None:
        """Delete a document by ID.
        
        Args:
            collection_name: Name of the collection
            document_id: Document ID
        """
        collection = self.get_or_create_collection(collection_name)
        collection.delete(ids=[document_id])
    
    def delete_documents_by_source(
        self,
        collection_name: str,
        source: str
    ) -> int:
        """Delete all document chunks by source filename.
        
        Args:
            collection_name: Name of the collection
            source: Source filename to delete (can be full path or just filename)
            
        Returns:
            Number of chunks deleted
        """
        collection = self.get_or_create_collection(collection_name)
        
        # First try exact match
        result = collection.get(where={"source": source})
        
        # If no exact match, get all documents and find those where source ends with the filename
        if not result or not result.get("ids"):
            all_docs = collection.get()
            if all_docs and all_docs.get("ids"):
                matching_ids = []
                for i, doc_id in enumerate(all_docs["ids"]):
                    doc_source = all_docs["metadatas"][i].get("source", "")
                    # Check if source ends with the filename (handles temp paths)
                    if doc_source.endswith(source) or doc_source.endswith("/" + source):
                        matching_ids.append(doc_id)
                
                if matching_ids:
                    collection.delete(ids=matching_ids)
                    return len(matching_ids)
        else:
            # Delete all matching documents
            collection.delete(ids=result["ids"])
            return len(result["ids"])
        
        return 0
    
    def get_collection_documents(
        self,
        collection_name: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get all documents in a collection.
        
        Args:
            collection_name: Name of the collection
            limit: Maximum number of documents to return (optional)
            
        Returns:
            Collection data including documents, metadata, and IDs
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Get all documents in the collection
        result = collection.get(limit=limit)
        
        return result
    
    def get_documents_collection(self) -> chromadb.Collection:
        """Get the main documents collection.
        
        Returns:
            The main documents collection
        """
        return self.get_or_create_collection(self.DOCUMENTS_COLLECTION)
    
    def query_by_tags(
        self,
        query_text: str,
        tags: Optional[List[str]] = None,
        n_results: int = 5,
        include_untagged: bool = True
    ) -> Dict[str, Any]:
        """Query documents by tags, including untagged documents.
        
        Args:
            query_text: Query text
            tags: List of tags to filter by (None means no tag filtering)
            n_results: Number of results to return
            include_untagged: Whether to include untagged documents
            
        Returns:
            Query results combining tagged and untagged documents
        """
        collection = self.get_documents_collection()
        
        # If no tags specified, query all documents
        if not tags:
            return collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
        
        # Build where clause for tag filtering using ChromaDB's supported operators
        # We'll use $in with exact tag matches and handle comma-separated values differently
        where_conditions = []
        
        # For each selected tag, we need to match it in the comma-separated tags field
        # Since ChromaDB doesn't support regex, we'll query all documents and filter client-side
        # For better performance with large datasets, consider storing tags as separate fields
        
        # Include untagged documents if requested
        if include_untagged:
            where_conditions.append({"tags": {"$eq": ""}})  # Empty string only
        
        # Get all results without where clause filtering, then filter client-side
        # This is more reliable than trying to use complex where clauses
        all_results = collection.query(
            query_texts=[query_text],
            n_results=n_results * 3  # Get more results to filter from
        )
        
        # Filter results client-side for tag matching
        if tags and all_results and all_results.get("metadatas") and all_results.get("metadatas")[0]:
            filtered_ids = []
            filtered_documents = []
            filtered_metadatas = []
            filtered_distances = []
            
            for i, metadata in enumerate(all_results["metadatas"][0]):
                doc_tags_str = metadata.get("tags", "")
                doc_tags = [tag.strip() for tag in doc_tags_str.split(",") if tag.strip()] if doc_tags_str else []
                
                # Check if any selected tag matches document tags
                tag_match = any(tag in doc_tags for tag in tags)
                
                # Check if we should include untagged documents
                is_untagged = not doc_tags
                
                if tag_match or (include_untagged and is_untagged):
                    filtered_ids.append(all_results["ids"][0][i])
                    filtered_documents.append(all_results["documents"][0][i])
                    filtered_metadatas.append(all_results["metadatas"][0][i])
                    if all_results.get("distances"):
                        filtered_distances.append(all_results["distances"][0][i])
                    
                    # Limit results
                    if len(filtered_ids) >= n_results:
                        break
            
            # Return filtered results in ChromaDB format
            result = {
                "ids": [filtered_ids],
                "documents": [filtered_documents],
                "metadatas": [filtered_metadatas]
            }
            if filtered_distances:
                result["distances"] = [filtered_distances]
            
            return result
        
        # If no tag filtering needed, return all results as-is
        
        return all_results
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags from all documents.
        
        Returns:
            List of unique tags
        """
        collection = self.get_documents_collection()
        
        # Get all documents with their metadata
        result = collection.get()
        
        if not result or not result.get("metadatas"):
            return []
        
        # Extract all tags from metadata
        all_tags = set()
        for metadata in result["metadatas"]:
            tags_str = metadata.get("tags", "")
            if tags_str and isinstance(tags_str, str):
                # Split comma-separated tags and clean them
                tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                all_tags.update(tags)
        
        return sorted(list(all_tags))
    
    def get_tag_counts(self) -> Dict[str, int]:
        """Get tag usage statistics by document count (not chunk count).
        
        Returns:
            Dictionary mapping tag names to number of unique documents that have that tag
        """
        collection = self.get_documents_collection()
        
        # Get all documents with their metadata
        result = collection.get()
        
        if not result or not result.get("metadatas"):
            return {}
        
        # Group chunks by source (document) first
        documents_by_source = {}
        for metadata in result["metadatas"]:
            source = metadata.get("source", "unknown")
            tags_str = metadata.get("tags", "")
            
            if source not in documents_by_source:
                documents_by_source[source] = tags_str
        
        # Count tag usage by unique documents (not chunks)
        tag_counts = {}
        for source, tags_str in documents_by_source.items():
            if tags_str and isinstance(tags_str, str):
                # Split comma-separated tags and clean them
                tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return dict(sorted(tag_counts.items()))
    
    def add_document_to_main_collection(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """Add documents to the main documents collection.
        
        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs
        """
        self.add_documents(self.DOCUMENTS_COLLECTION, documents, metadatas, ids)
    
    def get_documents_by_tags(
        self,
        tags: Optional[List[str]] = None,
        include_untagged: bool = True,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get documents filtered by tags.
        
        Args:
            tags: List of tags to filter by (None means no tag filtering)
            include_untagged: Whether to include untagged documents
            limit: Maximum number of documents to return
            
        Returns:
            Filtered documents
        """
        collection = self.get_documents_collection()
        
        # If no tags specified, get all documents
        if not tags:
            return collection.get(limit=limit)
        
        # Get all documents and filter client-side (similar to query_by_tags)
        all_docs = collection.get(limit=limit * 2 if limit else None)  # Get extra to filter from
        
        if not tags:
            return all_docs  # Return all if no tag filtering
        
        # Filter client-side
        if all_docs and all_docs.get("metadatas"):
            filtered_ids = []
            filtered_documents = []
            filtered_metadatas = []
            
            for i, metadata in enumerate(all_docs["metadatas"]):
                doc_tags_str = metadata.get("tags", "")
                doc_tags = [tag.strip() for tag in doc_tags_str.split(",") if tag.strip()] if doc_tags_str else []
                
                # Check if any selected tag matches document tags
                tag_match = any(tag in doc_tags for tag in tags)
                
                # Check if we should include untagged documents
                is_untagged = not doc_tags
                
                if tag_match or (include_untagged and is_untagged):
                    filtered_ids.append(all_docs["ids"][i])
                    filtered_documents.append(all_docs["documents"][i])
                    filtered_metadatas.append(all_docs["metadatas"][i])
                    
                    # Limit results
                    if limit and len(filtered_ids) >= limit:
                        break
            
            return {
                "ids": filtered_ids,
                "documents": filtered_documents,
                "metadatas": filtered_metadatas
            }
        
        return all_docs
    
    def delete_document_from_main_collection(self, document_id: str) -> None:
        """Delete a document from the main collection.
        
        Args:
            document_id: Document ID to delete
        """
        self.delete_document(self.DOCUMENTS_COLLECTION, document_id)
    
    def delete_documents_by_source_from_main_collection(self, source: str) -> int:
        """Delete documents by source from the main collection.
        
        Args:
            source: Source filename to delete
            
        Returns:
            Number of documents deleted
        """
        return self.delete_documents_by_source(self.DOCUMENTS_COLLECTION, source)
    
    def get_documents_by_source_from_main_collection(self, source: str) -> Optional[Dict[str, Any]]:
        """Get documents by source from the main collection.
        
        Args:
            source: Source filename to retrieve
            
        Returns:
            Documents data or None if not found
        """
        collection = self.get_documents_collection()
        try:
            # First try exact match
            result = collection.get(
                where={"source": source},
                include=["documents", "metadatas"]
            )
            
            if result and result.get("ids"):
                return result
            
            # If no exact match, get all documents and filter manually (similar to delete_documents_by_source)
            all_docs = collection.get(include=["documents", "metadatas"])
            if all_docs and all_docs.get("ids"):
                matching_indices = []
                for i, doc_id in enumerate(all_docs["ids"]):
                    doc_source = all_docs["metadatas"][i].get("source", "")
                    # Check if source matches exactly or ends with the filename (handles temp paths)
                    if doc_source == source or doc_source.endswith("/" + source) or doc_source.endswith(source):
                        matching_indices.append(i)
                
                if matching_indices:
                    # Return filtered results in the same format
                    filtered_result = {
                        "ids": [all_docs["ids"][i] for i in matching_indices],
                        "documents": [all_docs["documents"][i] for i in matching_indices],
                        "metadatas": [all_docs["metadatas"][i] for i in matching_indices]
                    }
                    return filtered_result
            
            return None
        except Exception as e:
            print(f"Error getting documents by source '{source}': {e}")
            return None
    
    def update_document_metadata_by_source(self, source: str, new_metadata: Dict[str, Any]) -> int:
        """Update metadata for all document chunks with the given source filename.
        
        Args:
            source: Source filename to update
            new_metadata: New metadata to set (tags will be converted to string)
            
        Returns:
            Number of document chunks updated
        """
        try:
            collection = self.get_documents_collection()
            
            # Get all documents in the collection
            result = collection.get()
            
            if not result or not result["ids"]:
                return 0
            
            # Find documents with matching source
            ids_to_update = []
            metadatas_to_update = []
            
            for i, doc_id in enumerate(result["ids"]):
                metadata = result["metadatas"][i] if result.get("metadatas") else {}
                
                if metadata.get("source") == source:
                    # Update metadata while preserving other fields
                    updated_metadata = metadata.copy()
                    
                    # Convert tags list to comma-separated string for ChromaDB storage
                    for key, value in new_metadata.items():
                        if key == "tags" and isinstance(value, list):
                            updated_metadata[key] = ",".join(value) if value else ""
                        else:
                            updated_metadata[key] = value
                    
                    ids_to_update.append(doc_id)
                    metadatas_to_update.append(updated_metadata)
            
            if ids_to_update:
                collection.update(
                    ids=ids_to_update,
                    metadatas=metadatas_to_update
                )
            
            return len(ids_to_update)
            
        except Exception as e:
            print(f"Error updating document metadata: {e}")
            raise
    
    def migrate_documents_to_main_collection(self, copy_from_collections: List[str] = None) -> Dict[str, int]:
        """Migrate documents from old collections to the main collection.
        
        Args:
            copy_from_collections: List of collection names to migrate from.
                                 If None, migrates from all existing collections except main.
        
        Returns:
            Dictionary with migration statistics
        """
        if copy_from_collections is None:
            copy_from_collections = [
                name for name in self.list_collections() 
                if name != self.DOCUMENTS_COLLECTION
            ]
        
        stats = {"collections_processed": 0, "documents_migrated": 0, "errors": 0}
        
        for collection_name in copy_from_collections:
            try:
                # Get all documents from the source collection
                result = self.get_collection_documents(collection_name)
                
                if result and result.get("ids"):
                    # Add documents to main collection
                    self.add_document_to_main_collection(
                        documents=result["documents"],
                        metadatas=result["metadatas"],
                        ids=[f"migrated_{collection_name}_{doc_id}" for doc_id in result["ids"]]
                    )
                    
                    stats["documents_migrated"] += len(result["ids"])
                    stats["collections_processed"] += 1
                    
                    print(f"Migrated {len(result['ids'])} documents from {collection_name}")
                    
            except Exception as e:
                print(f"Error migrating collection {collection_name}: {e}")
                stats["errors"] += 1
        
        return stats


# Create a singleton instance
chroma_client = ChromaClient()