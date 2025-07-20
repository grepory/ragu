from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from app.db.chroma_client import chroma_client

router = APIRouter()


@router.post("/migrate-documents")
async def migrate_documents_to_main_collection():
    """Migrate all documents from old collections to the new main collection.
    
    This helps users transition from the old collection-based system 
    to the new tag-based system without losing their data.
    
    Returns:
        Migration statistics
    """
    try:
        stats = chroma_client.migrate_documents_to_main_collection()
        
        return {
            "status": "success",
            "message": f"Migration completed. Processed {stats['collections_processed']} collections, "
                      f"migrated {stats['documents_migrated']} documents with {stats['errors']} errors.",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )


@router.get("/collections-status")
async def get_collections_status():
    """Get information about existing collections and migration status.
    
    Returns:
        Collection status information
    """
    try:
        all_collections = chroma_client.list_collections()
        main_collection_exists = chroma_client.DOCUMENTS_COLLECTION in all_collections
        
        # Get document counts for each collection
        collection_info = {}
        for collection_name in all_collections:
            try:
                result = chroma_client.get_collection_documents(collection_name, limit=1000)
                doc_count = len(result.get("ids", [])) if result else 0
                collection_info[collection_name] = {
                    "document_count": doc_count,
                    "is_main_collection": collection_name == chroma_client.DOCUMENTS_COLLECTION
                }
            except Exception as e:
                collection_info[collection_name] = {
                    "document_count": 0,
                    "error": str(e),
                    "is_main_collection": collection_name == chroma_client.DOCUMENTS_COLLECTION
                }
        
        return {
            "collections": collection_info,
            "main_collection_exists": main_collection_exists,
            "migration_needed": len([c for c in all_collections if c != chroma_client.DOCUMENTS_COLLECTION]) > 0,
            "total_collections": len(all_collections)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collection status: {str(e)}"
        )