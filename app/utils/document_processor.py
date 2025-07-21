import os
import uuid
import signal
import asyncio
from typing import List, Dict, Any, Tuple
import tempfile
from functools import wraps
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
)

from app.core.config import settings


class TimeoutError(Exception):
    """Raised when document processing times out."""
    pass


async def run_with_timeout(func, timeout_seconds: int, *args, **kwargs):
    """Run a function with a timeout using asyncio.
    
    This is cross-platform and works on Windows, Mac, and Linux.
    """
    import concurrent.futures
    import threading
    
    def target():
        return func(*args, **kwargs)
    
    # Use ThreadPoolExecutor to run the function in a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(target)
        try:
            # Wait for the result with timeout
            result = future.result(timeout=timeout_seconds)
            return result
        except concurrent.futures.TimeoutError:
            # Cancel the future (though it may not stop immediately)
            future.cancel()
            raise TimeoutError(f"Document processing timed out after {timeout_seconds} seconds")


class DocumentProcessor:
    """Utility for processing documents for RAG."""
    
    def __init__(self):
        """Initialize document processor."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
    
    def check_file_size(self, file_path: str, file_name: str) -> None:
        """Check if file size is within limits.
        
        Args:
            file_path: Path to the file
            file_name: Original filename
            
        Raises:
            ValueError: If file is too large
        """
        try:
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            if file_size_mb > settings.MAX_FILE_SIZE_MB:
                raise ValueError(
                    f"File '{file_name}' is {file_size_mb:.1f}MB, which exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB. "
                    f"Please try a smaller file or contact support for assistance with large files."
                )
        except OSError as e:
            raise ValueError(f"Could not check file size for '{file_name}': {str(e)}")
    
    def _process_file_sync(self, file_path: str, file_name: str) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
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
                    "source": file_name,  # This should be the original filename
                    "original_filename": file_name,  # Add explicit field for original filename
                    "chunk": i,
                    "total_chunks": len(chunks),
                }
                
                # Add any existing metadata from the document (but don't override source)
                if hasattr(chunk, 'metadata') and chunk.metadata:
                    for key, value in chunk.metadata.items():
                        # Don't let document loaders override our source filename
                        if key not in ['source', 'original_filename']:
                            metadata[key] = value
                
                metadatas.append(metadata)
                # Generate a unique ID for each chunk
                ids.append(str(uuid.uuid4()))
            
            return texts, metadatas, ids
        
        except Exception as e:
            # Log the error with more details
            import traceback
            print(f"Error processing file {file_name}: {str(e)}")
            print(f"File path: {file_path}")
            print(f"File extension: {file_extension}")
            print(f"Traceback: {traceback.format_exc()}")
            # Return empty lists to avoid breaking the upload process
            return [], [], []
    
    async def process_file(self, file_path: str, file_name: str) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """Process a file and split it into chunks with size and timeout checks.
        
        Args:
            file_path: Path to the file
            file_name: Original filename
            
        Returns:
            Tuple of (chunks, metadatas, ids)
        """
        try:
            # Check file size first
            self.check_file_size(file_path, file_name)
            
            # Process with timeout using cross-platform async approach
            return await run_with_timeout(
                self._process_file_sync,
                settings.PROCESSING_TIMEOUT_SECONDS,
                file_path,
                file_name
            )
            
        except TimeoutError:
            raise ValueError(
                f"Processing of '{file_name}' timed out after {settings.PROCESSING_TIMEOUT_SECONDS} seconds. "
                f"This usually happens with very large or complex files. Please try a smaller file or contact support."
            )
        except ValueError:
            # Re-raise ValueError (size/timeout errors)
            raise
        except Exception as e:
            # Log and convert other errors to ValueError
            import traceback
            print(f"Error processing file {file_name}: {str(e)}")
            print(f"File path: {file_path}")
            print(f"Traceback: {traceback.format_exc()}")
            raise ValueError(f"Failed to process '{file_name}': {str(e)}")
    
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