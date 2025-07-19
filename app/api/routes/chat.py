from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import List, Dict, Any, Optional
import json

from app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from app.db.chroma_client import chroma_client
from app.services.llm_service import llm_service, StreamingCallbackHandler

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat functionality.
    
    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse message
                message = json.loads(data)
                
                # Check message type
                if message.get("type") == "chat":
                    # Extract chat request
                    collection_name = message.get("collection_name")
                    query = message.get("query")
                    history_data = message.get("history", [])
                    model = message.get("model")
                    
                    # Validate required fields
                    if not collection_name or not query:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Missing required fields: collection_name and query"
                        })
                        continue
                    
                    # Check if collection exists
                    collections = chroma_client.list_collections()
                    if collection_name not in collections:
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Collection '{collection_name}' not found"
                        })
                        continue
                    
                    # Convert history data to ChatMessage objects
                    history = [
                        ChatMessage(role=msg.get("role"), content=msg.get("content"))
                        for msg in history_data
                        if msg.get("role") and msg.get("content")
                    ] if history_data else None
                    
                    # Create streaming callback handler
                    callback_handler = StreamingCallbackHandler(websocket)
                    
                    # Send start message
                    await websocket.send_json({
                        "type": "start",
                        "content": "Generating response..."
                    })
                    
                    # Generate RAG response with streaming
                    response_data = await llm_service.generate_rag_response(
                        query=query,
                        collection_name=collection_name,
                        history=history,
                        model=model,
                        streaming=True,
                        callback_handler=callback_handler
                    )
                    
                    # Send complete response
                    await websocket.send_json({
                        "type": "complete",
                        "content": {
                            "answer": response_data["answer"],
                            "sources": response_data["sources"],
                            "history": [
                                {"role": msg.role, "content": msg.content}
                                for msg in response_data["history"]
                            ]
                        }
                    })
                
                elif message.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_json({
                        "type": "pong",
                        "content": "pong"
                    })
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Unknown message type: {message.get('type')}"
                    })
            
            except json.JSONDecodeError:
                # Invalid JSON
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON message"
                })
            
            except Exception as e:
                # Other errors
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error processing message: {str(e)}"
                })
    
    except WebSocketDisconnect:
        # Client disconnected
        pass


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """REST endpoint for chat functionality.
    
    This is a non-streaming alternative to the WebSocket endpoint.
    
    Args:
        request: Chat request
        
    Returns:
        Chat response
    """
    try:
        # Check if collection exists
        collections = chroma_client.list_collections()
        if request.collection_name not in collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{request.collection_name}' not found"
            )
        
        # Generate RAG response
        response_data = await llm_service.generate_rag_response(
            query=request.query,
            collection_name=request.collection_name,
            history=request.history,
            model=request.model
        )
        
        return ChatResponse(
            answer=response_data["answer"],
            sources=response_data["sources"],
            history=response_data["history"]
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )