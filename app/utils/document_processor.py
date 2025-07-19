import os
import uuid
from typing import List, Dict, Any, Tuple
import tempfile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
)

from app.core.config import settings

class DocumentProcessor:
    """Utility for processing documents for RAG."""
    
    def __init__(self):
        """Initialize document processor."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
    
    def process_file(self, file_path: str, file_name: str) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """Process a file and split it into chunks.
        
        Args:
            file_path: Path to the file
            file_name: Original filename
            
        Returns:
            Tuple of (chunks, metadatas, ids)
        """
        # Determine file type and use appropriate loader
        file_extension = os.path.splitext(file_name)[1].lower()
        
        try:
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension in ['.docx', '.doc']:
                loader = Docx2txtLoader(file_path)
            elif file_extension == '.csv':
                loader = CSVLoader(file_path)
            else:
                # Default to text loader for other file types
                loader = TextLoader(file_path)
            
            # Load and split the document
            documents = loader.load()
            chunks = self.text_splitter.split_documents(documents)
            
            # Extract text and metadata
            texts = [chunk.page_content for chunk in chunks]
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                # Create metadata for each chunk
                metadata = {
                    "source": file_name,
                    "chunk": i,
                    "total_chunks": len(chunks),
                }
                # Add any existing metadata from the document
                if hasattr(chunk, 'metadata'):
                    metadata.update(chunk.metadata)
                
                metadatas.append(metadata)
                # Generate a unique ID for each chunk
                ids.append(str(uuid.uuid4()))
            
            return texts, metadatas, ids
        
        except Exception as e:
            # Log the error and re-raise
            print(f"Error processing file {file_name}: {str(e)}")
            raise
    
    def process_text(self, text: str, source: str = "direct_input") -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """Process raw text and split it into chunks.
        
        Args:
            text: Raw text to process
            source: Source identifier for the text
            
        Returns:
            Tuple of (chunks, metadatas, ids)
        """
        # Split the text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create metadata and IDs
        metadatas = []
        ids = []
        
        for i, _ in enumerate(chunks):
            metadata = {
                "source": source,
                "chunk": i,
                "total_chunks": len(chunks),
            }
            metadatas.append(metadata)
            ids.append(str(uuid.uuid4()))
        
        return chunks, metadatas, ids
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save an uploaded file to a temporary location.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Path to the saved file
        """
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
        
        try:
            # Write the content to the file
            temp_file.write(file_content)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            # Clean up on error
            temp_file.close()
            os.unlink(temp_file.name)
            raise e


# Create a singleton instance
document_processor = DocumentProcessor()