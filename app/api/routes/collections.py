from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.schemas import CollectionCreate, CollectionResponse, CollectionList
from app.db.chroma_client import chroma_client

router = APIRouter()


@router.post("/", response_model=CollectionResponse, status_code=201)
async def create_collection(collection: CollectionCreate):
    """Create a new collection in the vector database.
    
    Args:
        collection: Collection creation data
        
    Returns:
        Created collection data
    """
    try:
        # Check if collection already exists
        existing_collections = chroma_client.list_collections()
        if collection.name in existing_collections:
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{collection.name}' already exists"
            )
        
        # Create the collection
        chroma_client.get_or_create_collection(collection.name)
        
        return CollectionResponse(
            name=collection.name,
            description=collection.description
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create collection: {str(e)}"
        )


@router.get("/", response_model=CollectionList)
async def list_collections():
    """List all collections in the vector database.
    
    Returns:
        List of collection names
    """
    try:
        collections = chroma_client.list_collections()
        return CollectionList(collections=collections)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.get("/{collection_name}", response_model=CollectionResponse)
async def get_collection(collection_name: str):
    """Get information about a specific collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection data
    """
    try:
        # Check if collection exists
        collections = chroma_client.list_collections()
        if collection_name not in collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # For now, we only return the name as ChromaDB doesn't store descriptions
        return CollectionResponse(
            name=collection_name,
            description=None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection: {str(e)}"
        )


@router.delete("/{collection_name}", status_code=204)
async def delete_collection(collection_name: str):
    """Delete a collection from the vector database.
    
    Args:
        collection_name: Name of the collection to delete
    """
    try:
        # Check if collection exists
        collections = chroma_client.list_collections()
        if collection_name not in collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found"
            )
        
        # Delete the collection
        chroma_client.delete_collection(collection_name)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete collection: {str(e)}"
        )