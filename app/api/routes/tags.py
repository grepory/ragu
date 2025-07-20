from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from app.models.schemas import (
    TagListResponse,
    TagBasedQueryRequest,
    QueryResponse,
    QueryResult
)
from app.db.chroma_client import chroma_client

router = APIRouter()


@router.get("/", response_model=TagListResponse)
async def get_all_tags():
    """Get all available tags and their usage counts.
    
    Returns:
        List of tags and their usage statistics
    """
    try:
        tags = chroma_client.get_all_tags()
        tag_counts = chroma_client.get_tag_counts()
        
        return TagListResponse(
            tags=tags,
            tag_counts=tag_counts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tags: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_by_tags(request: TagBasedQueryRequest):
    """Query documents by tags.
    
    Args:
        request: Tag-based query request
        
    Returns:
        Query results matching the specified tags
    """
    try:
        # Query documents using the tag-based method
        results = chroma_client.query_by_tags(
            query_text=request.query_text,
            tags=request.tags,
            n_results=request.n_results,
            include_untagged=request.include_untagged
        )
        
        # Transform ChromaDB results into our schema format
        query_results = []
        if results and "ids" in results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):  # ChromaDB returns nested lists
                query_results.append(QueryResult(
                    id=doc_id,
                    text=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    score=1.0 - results["distances"][0][i] if results["distances"] else 1.0  # Convert distance to similarity
                ))
        
        return QueryResponse(
            results=query_results,
            query=request.query_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query by tags: {str(e)}")


@router.get("/documents")
async def get_documents_by_tags(
    tags: Optional[List[str]] = Query(None, description="Tags to filter by"),
    include_untagged: bool = Query(True, description="Whether to include untagged documents"),
    limit: Optional[int] = Query(None, description="Maximum number of documents to return")
):
    """Get documents filtered by tags.
    
    Args:
        tags: List of tags to filter by
        include_untagged: Whether to include untagged documents
        limit: Maximum number of documents to return
        
    Returns:
        Filtered documents
    """
    try:
        result = chroma_client.get_documents_by_tags(
            tags=tags,
            include_untagged=include_untagged,
            limit=limit
        )
        
        # Transform the result for the response
        documents = []
        if result and "ids" in result and result["ids"]:
            for i, doc_id in enumerate(result["ids"]):
                # Extract document info from metadata
                metadata = result["metadatas"][i] if result["metadatas"] else {}
                
                # Group documents by source
                source = metadata.get("source", "Unknown")
                if not any(doc.get("source") == source for doc in documents):
                    # Count chunks for this source
                    source_chunks = [
                        j for j, meta in enumerate(result["metadatas"] or [])
                        if meta.get("source") == source
                    ]
                    
                    # Extract tags from metadata
                    tags_str = metadata.get("tags", "")
                    doc_tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()] if tags_str else []
                    
                    documents.append({
                        "source": source,
                        "total_chunks": len(source_chunks),
                        "tags": doc_tags,
                        "metadata": metadata
                    })
        
        return {
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents by tags: {str(e)}")