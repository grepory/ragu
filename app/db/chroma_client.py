import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

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
        
        # Default embedding function (OpenAI)
        self.default_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name="text-embedding-ada-002"
        )
    
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


# Create a singleton instance
chroma_client = ChromaClient()