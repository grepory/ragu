from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from app.models.schemas import (
    ConversationCreate, 
    ConversationUpdate, 
    ConversationResponse, 
    ConversationList,
    TitleGenerationRequest,
    TitleGenerationResponse,
    ChatMessage
)
from app.db.conversation_store import conversation_store
from app.services.llm_service import llm_service

router = APIRouter()


@router.post("/", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate):
    """Create a new conversation.
    
    Args:
        conversation: Conversation data
        
    Returns:
        Created conversation
    """
    # If no title is provided and there are messages, generate a title
    if not conversation.title and conversation.messages:
        # Only generate a title if there's at least one user message
        user_messages = [msg for msg in conversation.messages if msg.role == "user"]
        if user_messages:
            title = await generate_title_from_messages(conversation.messages, conversation.model)
            conversation.title = title
    
    return conversation_store.create_conversation(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get a conversation by ID.
    
    Args:
        conversation_id: ID of the conversation
        
    Returns:
        Conversation data
    """
    conversation = conversation_store.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: str, update: ConversationUpdate):
    """Update a conversation.
    
    Args:
        conversation_id: ID of the conversation
        update: Update data
        
    Returns:
        Updated conversation
    """
    conversation = conversation_store.update_conversation(conversation_id, update)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    return conversation


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation.
    
    Args:
        conversation_id: ID of the conversation
        
    Returns:
        Success message
    """
    success = conversation_store.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    return {"message": f"Conversation {conversation_id} deleted"}


@router.get("/", response_model=ConversationList)
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all conversations.
    
    Args:
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return
        
    Returns:
        List of conversations
    """
    result = conversation_store.list_conversations(skip=skip, limit=limit)
    return ConversationList(
        conversations=result["conversations"],
        total=result["total"]
    )


@router.post("/generate-title", response_model=TitleGenerationResponse)
async def generate_title(request: TitleGenerationRequest):
    """Generate a title for a conversation.
    
    Args:
        request: Title generation request
        
    Returns:
        Generated title
    """
    title = await generate_title_from_messages(request.messages, request.model)
    return TitleGenerationResponse(title=title)


async def generate_title_from_messages(messages: List[ChatMessage], model: Optional[str] = None) -> str:
    """Generate a title from conversation messages.
    
    Args:
        messages: List of messages
        model: Optional model to use
        
    Returns:
        Generated title
    """
    # Extract the first user message
    user_messages = [msg for msg in messages if msg.role == "user"]
    if not user_messages:
        return "New conversation"
    
    first_message = user_messages[0].content
    
    # Truncate the message if it's too long
    if len(first_message) > 100:
        first_message = first_message[:100] + "..."
    
    # Create a prompt for title generation
    prompt = f"""Generate a short sentence title (5-10 words maximum) for a conversation that starts with this message:

User message: "{first_message}"

The title should be a natural, conversational sentence that captures what the user wants to know or do. Use sentence case and avoid quotation marks. Examples:
- "How do I set up my development environment"
- "What are the best practices for testing"
- "Help me troubleshoot this error message"

Respond with just the title sentence, nothing else."""
    
    try:
        # Get LLM
        llm = llm_service.get_llm(model=model)
        
        # Generate title
        response = await llm.acomplete(prompt)
        title = response.text.strip()
        
        # Limit title length
        if len(title) > 50:
            title = title[:50] + "..."
        
        # Remove quotes if present
        title = title.strip('"\'')
        
        return title
    except Exception as e:
        # If title generation fails, use a default title based on the first message
        print(f"Error generating title: {e}")
        
        # Use the first few words of the first message as the title
        words = first_message.split()
        if len(words) <= 6:
            return first_message
        else:
            return " ".join(words[:6]) + "..."