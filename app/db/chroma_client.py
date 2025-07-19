import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.core.config import settings

class ChromaClient:
    """Client for interacting with ChromaDB vector database."""
    
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
            # Use DefaultEmbeddingFunction as a fallback
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


# Create a singleton instance
chroma_client = ChromaClient()