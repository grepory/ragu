import os
import traceback

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from typing import List, Optional, Dict, Any
import json

from app.models.schemas import (
    DocumentResponse, 
    DocumentList, 
    TextInput,
    QueryRequest,
    QueryResponse,
    QueryResult,
    DeleteDocumentRequest,
    UpdateDocumentTagsRequest
)
from app.db.chroma_client import chroma_client
from app.utils.document_processor import document_processor
from app.services.llm_service import llm_service
from app.core.config import settings

router = APIRouter()


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Form(None),  # Deprecated but kept for compatibility
    tags: Optional[str] = Form(None),
    additional_metadata: Optional[str] = Form(None)
):
    """Upload a document to the vector database.
    
    Args:
        file: Document file
        collection_name: Name of the collection to add the document to
        tags: Optional comma-separated list of tags (e.g., "personal,house,important")
        additional_metadata: Optional JSON string with additional metadata
        
    Returns:
        Upload status
    """
    try:
        # In the new system, all documents go to the main collection
        # collection_name parameter is ignored (kept for backward compatibility)
        
        # Parse additional metadata if provided
        metadata_dict = {}
        if additional_metadata:
            try:
                metadata_dict = json.loads(additional_metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON in additional_metadata"
                )
        
        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Check file size before reading (FastAPI provides size in bytes)
        if hasattr(file, 'size') and file.size:
            file_size_mb = file.size / (1024 * 1024)
            if file_size_mb > settings.MAX_FILE_SIZE_MB:
                raise HTTPException(
                    status_code=413,
                    detail=f"File '{file.filename}' is {file_size_mb:.1f}MB, which exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
                )
        
        # Read file content
        file_content = await file.read()
        
        # Double-check file size after reading
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File '{file.filename}' is {file_size_mb:.1f}MB, which exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
            )
        
        # Save file to temporary location
        temp_file_path = document_processor.save_uploaded_file(file_content, file.filename)
        
        try:
            # Process the document
            texts, metadatas, ids = await document_processor.process_file(temp_file_path, file.filename)
            
            # Check if any chunks were generated
            if not texts or not ids:
                raise ValueError(f"Failed to extract content from '{file.filename}'. Expected IDs to be a non-empty list, got {ids}")
            
            # Add additional metadata to each chunk
            for metadata in metadatas:
                metadata.update(metadata_dict)
                # Add tags if provided
                if tag_list:
                    # Convert tag list to comma-separated string to ensure compatibility with ChromaDB
                    metadata["tags"] = ",".join(tag_list)
            
            # Add to main documents collection
            chroma_client.add_document_to_main_collection(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "status": "success",
                "message": f"Document '{file.filename}' uploaded and processed successfully",
                "chunks": len(texts),
                "tags": tag_list or []
            }
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error processing file '{file.filename}': {traceback.print_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post("/text", status_code=201)
async def add_text(text_input: TextInput):
    """Add text directly to the vector database.
    
    Args:
        text_input: Text content and metadata
        
    Returns:
        Upload status
    """
    try:
        # In the new system, all documents go to the main collection
        # collection_name parameter is ignored (kept for backward compatibility)
        
        # Process the text
        texts, metadatas, ids = document_processor.process_text(
            text=text_input.text,
            source="direct_input"
        )
        
        # Check if any chunks were generated
        if not texts or not ids:
            raise ValueError(f"Failed to extract content from text input. Expected IDs to be a non-empty list, got {ids}")
        
        # Add additional metadata if provided
        if text_input.metadata:
            for metadata in metadatas:
                metadata.update(text_input.metadata)
        
        # Add tags if provided
        if text_input.tags:
            for metadata in metadatas:
                # Convert tag list to comma-separated string to ensure compatibility with ChromaDB
                metadata["tags"] = ",".join(text_input.tags)
        
        # Add to main documents collection
        chroma_client.add_document_to_main_collection(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "status": "success",
            "message": "Text added successfully",
            "chunks": len(texts),
            "tags": text_input.tags or []
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add text: {str(e)}"
        )


@router.get("/{collection_name}/{document_id}", response_model=DocumentResponse)
async def get_document(collection_name: str, document_id: str):
    """Get a document by ID.
    
    Args:
        collection_name: Name of the collection
        document_id: Document ID
        
    Returns:
        Document data
    """
    try:
        # Check if collection exists
        collections = chroma_client.list_collections()
        if collection_name not in collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # Get document
        result = chroma_client.get_document(collection_name, document_id)
        
        # Check if document exists
        if not result or not result.get("ids") or not result.get("documents"):
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' not found in collection '{collection_name}'"
            )
        
        # Extract document data
        doc_id = result["ids"][0]
        text = result["documents"][0]
        metadata = result.get("metadatas", [{}])[0] if result.get("metadatas") else {}
        
        # Convert tags from comma-separated string back to list if present
        tags = metadata.get("tags")
        if tags and isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        return DocumentResponse(
            id=doc_id,
            text=text,
            metadata={
                "source": metadata.get("source", "unknown"),
                "chunk": metadata.get("chunk"),
                "total_chunks": metadata.get("total_chunks"),
                "page": metadata.get("page"),
                "tags": tags,
                "additional_metadata": {k: v for k, v in metadata.items() 
                                       if k not in ["source", "chunk", "total_chunks", "page", "tags"]}
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/by-source")
async def delete_document_by_source(
    request: DeleteDocumentRequest
):
    """Delete all chunks of a document by source filename from main collection.
    
    Args:
        request: JSON body containing the source filename
    """
    try:
        # Extract source from request body
        source = request.source
        
        # Delete all chunks of the document by source from main collection
        chunks_deleted = chroma_client.delete_documents_by_source_from_main_collection(source)
        
        if chunks_deleted == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No document found with source '{source}'"
            )
        
        return {
            "status": "success",
            "message": f"Deleted document '{source}'",
            "chunks_deleted": chunks_deleted
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str):
    """Delete a document by ID from main collection.
    
    Args:
        document_id: Document ID
    """
    try:
        # Delete document from main collection
        chroma_client.delete_document_from_main_collection(document_id)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/", response_model=DocumentList)
async def list_all_documents(
    limit: Optional[int] = Query(None, ge=1, le=10000)
):
    """List all documents in the main collection.
    
    Args:
        limit: Maximum number of documents to return
        
    Returns:
        List of all documents
    """
    try:
        # Get all documents from main collection
        result = chroma_client.get_collection_documents(
            chroma_client.DOCUMENTS_COLLECTION, 
            limit=limit
        )
        
        documents = []
        if result and result.get("ids"):
            # Group documents by source file
            doc_sources = {}
            
            for i, doc_id in enumerate(result["ids"]):
                metadata = result["metadatas"][i] if result.get("metadatas") else {}
                
                source = metadata.get("source", "unknown")
                
                # Clean up the source if it looks like a temp file path
                if source.startswith('/') and 'tmp' in source.lower():
                    source = os.path.basename(source)
                
                if source not in doc_sources:
                    # Convert tags from comma-separated string back to list
                    tags = metadata.get("tags", "")
                    if tags and isinstance(tags, str):
                        tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    else:
                        tags = []
                    
                    doc_sources[source] = {
                        "id": f"doc_{source}",
                        "source": source,
                        "total_chunks": metadata.get("total_chunks", 1),
                        "tags": tags,
                        "metadata": {k: v for k, v in metadata.items() 
                                   if k not in ["source", "chunk", "total_chunks", "tags"]}
                    }
            
            # Convert to DocumentResponse format
            for source_info in doc_sources.values():
                documents.append(DocumentResponse(
                    id=source_info["id"],
                    text=f"Document with {source_info['total_chunks']} chunks",
                    metadata={
                        "source": source_info["source"],
                        "total_chunks": source_info["total_chunks"],
                        "tags": source_info["tags"],
                        "additional_metadata": source_info["metadata"]
                    }
                ))
        
        return DocumentList(
            documents=documents,
            total=len(documents)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/all-collections", response_model=DocumentList)
async def list_all_documents_from_all_collections(
    limit: Optional[int] = Query(100, ge=1, le=1000)
):
    """List documents from all collections (compatibility endpoint).
    
    This endpoint searches both the new main collection and any existing
    old collections to provide access to all user documents.
    
    Args:
        limit: Maximum number of documents to return
        
    Returns:
        List of all documents across all collections
    """
    try:
        all_documents = []
        all_collections = chroma_client.list_collections()
        
        for collection_name in all_collections:
            try:
                result = chroma_client.get_collection_documents(
                    collection_name, 
                    limit=limit
                )
                
                if result and result.get("ids"):
                    # Group documents by source file within this collection
                    doc_sources = {}
                    
                    for i, doc_id in enumerate(result["ids"]):
                        metadata = result["metadatas"][i] if result.get("metadatas") else {}
                        
                        source = metadata.get("source", "unknown")
                        
                        # Clean up the source if it looks like a temp file path
                        if source.startswith('/') and 'tmp' in source.lower():
                            source = os.path.basename(source)
                        
                        if source not in doc_sources:
                            # Convert tags from comma-separated string back to list
                            tags = metadata.get("tags", "")
                            if tags and isinstance(tags, str):
                                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                            else:
                                tags = []
                            
                            doc_sources[source] = {
                                "id": f"{collection_name}_{source}",
                                "source": source,
                                "collection": collection_name,
                                "total_chunks": metadata.get("total_chunks", 1),
                                "tags": tags,
                                "metadata": {k: v for k, v in metadata.items() 
                                           if k not in ["source", "chunk", "total_chunks", "tags"]}
                            }
                    
                    # Convert to DocumentResponse format
                    for source_info in doc_sources.values():
                        all_documents.append(DocumentResponse(
                            id=source_info["id"],
                            text=f"Document in {source_info['collection']} with {source_info['total_chunks']} chunks",
                            metadata={
                                "source": source_info["source"],
                                "collection": source_info["collection"],  # Show which collection it came from
                                "total_chunks": source_info["total_chunks"],
                                "tags": source_info["tags"],
                                "additional_metadata": source_info["metadata"]
                            }
                        ))
            except Exception as e:
                print(f"Error processing collection {collection_name}: {e}")
                continue
        
        return DocumentList(
            documents=all_documents,
            total=len(all_documents)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list all documents: {str(e)}"
        )


@router.get("/debug/{collection_name}")
async def debug_collection(collection_name: str):
    """Debug endpoint to check raw ChromaDB data."""
    try:
        result = chroma_client.get_collection_documents(collection_name, limit=5)
        return {
            "raw_data": result,
            "collection": collection_name
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/search")
async def search_documents(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags")
):
    """Search documents by name and content.
    
    Args:
        q: Search query
        limit: Maximum number of results to return
        tags: Optional tags to filter results by
        
    Returns:
        Search results with relevance scores
    """
    try:
        if not q or not q.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        query = q.strip()
        results = []
        
        # Get all documents from main collection
        all_docs = chroma_client.get_collection_documents(
            chroma_client.DOCUMENTS_COLLECTION, 
            limit=None  # Get all documents for comprehensive search
        )
        
        if not all_docs or not all_docs.get("ids"):
            return {
                "query": query,
                "results": [],
                "total": 0
            }
        
        # Group documents by source for better results
        documents_by_source = {}
        for i, doc_id in enumerate(all_docs["ids"]):
            metadata = all_docs["metadatas"][i] if all_docs.get("metadatas") else {}
            document_text = all_docs["documents"][i] if all_docs.get("documents") else ""
            
            source = metadata.get("source", "unknown")
            
            # Apply tag filtering if specified
            if tags:
                doc_tags_str = metadata.get("tags", "")
                doc_tags = [tag.strip() for tag in doc_tags_str.split(",") if tag.strip()] if doc_tags_str else []
                # Skip if document doesn't have any of the required tags
                if not any(tag in doc_tags for tag in tags):
                    continue
            
            if source not in documents_by_source:
                documents_by_source[source] = {
                    "source": source,
                    "chunks": [],
                    "metadata": metadata,
                    "tags": [tag.strip() for tag in metadata.get("tags", "").split(",") if tag.strip()] if metadata.get("tags") else []
                }
            
            documents_by_source[source]["chunks"].append({
                "id": doc_id,
                "text": document_text,
                "chunk": metadata.get("chunk", 0)
            })
        
        # Perform both filename and content searches
        # Name-based search (fast string matching)
        query_lower = query.lower()
        for source, doc_info in documents_by_source.items():
            if query_lower in source.lower():
                # Calculate relevance score based on how well the query matches
                if source.lower() == query_lower:
                    score = 1.0  # Exact match
                elif source.lower().startswith(query_lower):
                    score = 0.9  # Starts with query
                else:
                    score = 0.7  # Contains query
                
                results.append({
                    "source": source,
                    "match_type": "filename",
                    "score": score,
                    "total_chunks": len(doc_info["chunks"]),
                    "tags": doc_info["tags"],
                    "metadata": doc_info["metadata"],
                    "preview": f"Filename match: {source}",
                    "matched_chunk": None
                })
        
        # Content-based semantic search
        try:
            semantic_results = chroma_client.query_collection(
                collection_name=chroma_client.DOCUMENTS_COLLECTION,
                query_text=query,
                n_results=min(limit * 2, 50)  # Get more results for better filtering
            )
            
            if semantic_results and semantic_results.get("ids") and semantic_results.get("ids")[0]:
                # Group semantic results by source
                source_best_matches = {}
                
                for i, doc_id in enumerate(semantic_results["ids"][0]):
                    metadata = semantic_results["metadatas"][0][i] if semantic_results.get("metadatas") else {}
                    document_text = semantic_results["documents"][0][i] if semantic_results.get("documents") else ""
                    distance = semantic_results["distances"][0][i] if semantic_results.get("distances") else 0
                    
                    source = metadata.get("source", "unknown")
                    
                    # Apply tag filtering
                    if tags:
                        doc_tags_str = metadata.get("tags", "")
                        doc_tags = [tag.strip() for tag in doc_tags_str.split(",") if tag.strip()] if doc_tags_str else []
                        if not any(tag in doc_tags for tag in tags):
                            continue
                    
                    # Convert distance to similarity score (lower distance = higher similarity)
                    score = max(0, 1.0 - distance)
                    
                    # Only keep the best match per source document
                    if source not in source_best_matches or score > source_best_matches[source]["score"]:
                        # Create preview text highlighting the match
                        preview = document_text[:200] + "..." if len(document_text) > 200 else document_text
                        
                        source_best_matches[source] = {
                            "source": source,
                            "match_type": "content",
                            "score": score * 0.95,  # Slightly lower priority than exact filename matches
                            "total_chunks": len(documents_by_source.get(source, {}).get("chunks", [])),
                            "tags": [tag.strip() for tag in metadata.get("tags", "").split(",") if tag.strip()] if metadata.get("tags") else [],
                            "metadata": metadata,
                            "preview": preview,
                            "matched_chunk": {
                                "id": doc_id,
                                "text": document_text,
                                "chunk": metadata.get("chunk", 0)
                            }
                        }
                
                results.extend(source_best_matches.values())
                    
        except Exception as e:
            print(f"Error in semantic search: {e}")
            # Continue with name-only results if semantic search fails
        
        # Remove duplicates (prioritize higher scores) and sort by relevance
        unique_results = {}
        for result in results:
            source = result["source"]
            if source not in unique_results or result["score"] > unique_results[source]["score"]:
                unique_results[source] = result
        
        final_results = sorted(unique_results.values(), key=lambda x: x["score"], reverse=True)
        
        # Limit results
        final_results = final_results[:limit]
        
        return {
            "query": query,
            "results": final_results,
            "total": len(final_results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search documents: {str(e)}"
        )


@router.get("/{collection_name}", response_model=DocumentList)
async def list_collection_documents(
    collection_name: str,
    limit: Optional[int] = Query(100, ge=1, le=1000)
):
    """List all documents in a collection.
    
    Args:
        collection_name: Name of the collection
        limit: Maximum number of documents to return
        
    Returns:
        List of documents in the collection
    """
    try:
        # Check if collection exists
        collections = chroma_client.list_collections()
        if collection_name not in collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # Get all documents in the collection
        result = chroma_client.get_collection_documents(collection_name, limit=limit)
        
        documents = []
        if result and result.get("ids"):
            # Group documents by source file
            doc_sources = {}
            
            for i, doc_id in enumerate(result["ids"]):
                text = result["documents"][i] if result.get("documents") else ""
                metadata = result["metadatas"][i] if result.get("metadatas") else {}
                
                # Try to get the original filename first, fall back to source, then unknown
                source = (
                    metadata.get("original_filename") or 
                    metadata.get("source") or 
                    "unknown"
                )
                
                # Clean up the source if it looks like a temp file path
                if source.startswith('/') and 'tmp' in source.lower():
                    # Extract just the filename part if it's a full path
                    source = os.path.basename(source)
                
                chunk_num = metadata.get("chunk", 0)
                
                if source not in doc_sources:
                    doc_sources[source] = {
                        "id": f"{collection_name}_{source}",
                        "source": source,
                        "chunks": [],
                        "total_chunks": metadata.get("total_chunks", 1),
                        "tags": [],
                        "metadata": {}
                    }
                
                # Convert tags from comma-separated string back to list if present
                tags = metadata.get("tags")
                if tags and isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    doc_sources[source]["tags"] = tags
                
                doc_sources[source]["chunks"].append({
                    "id": doc_id,
                    "chunk": chunk_num,
                    "text": text[:200] + "..." if len(text) > 200 else text  # Preview
                })
                
                # Store additional metadata
                doc_sources[source]["metadata"].update({
                    k: v for k, v in metadata.items() 
                    if k not in ["source", "chunk", "total_chunks", "tags"]
                })
            
            # Convert to DocumentResponse format
            for source_info in doc_sources.values():
                documents.append(DocumentResponse(
                    id=source_info["id"],
                    text=f"Document with {len(source_info['chunks'])} chunks",
                    metadata={
                        "source": source_info["source"],
                        "total_chunks": source_info["total_chunks"],
                        "tags": source_info["tags"],
                        "additional_metadata": source_info["metadata"]
                    }
                ))
        
        return DocumentList(
            documents=documents,
            total=len(documents)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def query_documents(query: QueryRequest):
    """Query documents in the vector database using tags.
    
    Args:
        query: Query parameters
        
    Returns:
        Query results
    """
    try:
        # Use the new tag-based querying system
        result = chroma_client.query_by_tags(
            query_text=query.query_text,
            tags=query.tags,
            n_results=query.n_results,
            include_untagged=query.include_untagged
        )
        
        # Process results
        query_results = []
        
        if result and result.get("ids") and result.get("ids")[0]:
            for i in range(len(result["ids"][0])):
                doc_id = result["ids"][0][i]
                text = result["documents"][0][i] if result.get("documents") and result["documents"][0] else ""
                metadata = result["metadatas"][0][i] if result.get("metadatas") and result["metadatas"][0] else {}
                distance = result["distances"][0][i] if result.get("distances") and result["distances"][0] else 0
                
                # Convert tags from comma-separated string back to list if present
                if metadata.get("tags") and isinstance(metadata["tags"], str):
                    metadata["tags"] = [tag.strip() for tag in metadata["tags"].split(',') if tag.strip()]
                
                # Convert distance to similarity score (1 - distance)
                score = 1 - distance if distance <= 1 else 0
                
                query_results.append(
                    QueryResult(
                        id=doc_id,
                        text=text,
                        metadata=metadata,
                        score=score
                    )
                )
        
        return QueryResponse(
            results=query_results,
            query=query.query_text
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query documents: {str(e)}"
        )


@router.put("/tags")
async def update_document_tags(request: UpdateDocumentTagsRequest):
    """Update tags for a document by source filename.
    
    Args:
        request: JSON body containing source filename and new tags
    """
    try:
        # Update document metadata with new tags
        updated_count = chroma_client.update_document_metadata_by_source(
            source=request.source,
            new_metadata={"tags": request.tags}
        )
        
        if updated_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found with source '{request.source}'"
            )
        
        return {
            "status": "success",
            "message": f"Updated tags for document '{request.source}'",
            "chunks_updated": updated_count,
            "new_tags": request.tags
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update document tags: {str(e)}"
        )


@router.post("/suggest-tags")
async def suggest_tags_for_source(
    source_filename: str = Form(...),
    model: Optional[str] = Form(None)
):
    """Generate LLM-powered tag suggestions for a document.
    
    Args:
        source_filename: The source filename of the document
        model: Optional model to use for tag generation
        
    Returns:
        Suggested tags for the document
    """
    try:
        # Get document chunks from the main collection
        result = chroma_client.get_documents_by_source_from_main_collection(source_filename)
        
        if not result or not result.get("documents"):
            raise HTTPException(
                status_code=404,
                detail=f"No document found with source '{source_filename}'"
            )
        
        # Extract document texts
        document_texts = result["documents"]
        
        # Get existing tags from the system
        existing_tags = chroma_client.get_all_tags()
        
        # Generate tag suggestions using LLM
        suggested_tags = await llm_service.suggest_tags(
            document_texts=document_texts,
            existing_tags=existing_tags,
            model=model,
            max_tags=8
        )
        
        return {
            "status": "success",
            "source": source_filename,
            "suggested_tags": suggested_tags,
            "existing_tags": existing_tags[:20]  # Return some existing tags for reference
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate tag suggestions: {str(e)}"
        )


