import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil

from app.core.config import settings
from app.models.schemas import ChatMessage, ConversationResponse, ConversationCreate, ConversationUpdate

class ConversationStore:
    """Store for managing conversation history."""
    
    def __init__(self):
        """Initialize conversation store."""
        # Define the directory for storing conversations
        self.conversations_dir = os.path.join(settings.CHROMA_PERSIST_DIRECTORY, "conversations")
        
        # Ensure the conversations directory exists
        os.makedirs(self.conversations_dir, exist_ok=True)
    
    def _get_conversation_path(self, conversation_id: str) -> str:
        """Get the file path for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            File path for the conversation
        """
        return os.path.join(self.conversations_dir, f"{conversation_id}.json")
    
    def _serialize_datetime(self, obj: Any) -> Any:
        """Serialize datetime objects to ISO format strings.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serialized object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def create_conversation(self, conversation: ConversationCreate) -> ConversationResponse:
        """Create a new conversation.
        
        Args:
            conversation: Conversation data
            
        Returns:
            Created conversation
        """
        # Generate a unique ID for the conversation
        conversation_id = str(uuid.uuid4())
        
        # Create timestamps
        now = datetime.now()
        
        # Create the conversation data
        conversation_data = {
            "id": conversation_id,
            "collection_name": conversation.collection_name,
            "title": conversation.title or "New Conversation",
            "model": conversation.model,
            "messages": [msg.dict() for msg in conversation.messages],
            "created_at": now,
            "updated_at": now
        }
        
        # Save the conversation to a file
        with open(self._get_conversation_path(conversation_id), "w") as f:
            json.dump(conversation_data, f, default=self._serialize_datetime)
        
        # Return the created conversation
        return ConversationResponse(
            id=conversation_id,
            collection_name=conversation.collection_name,
            title=conversation.title or "New Conversation",
            model=conversation.model,
            messages=conversation.messages,
            created_at=now,
            updated_at=now
        )
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation data or None if not found
        """
        conversation_path = self._get_conversation_path(conversation_id)
        
        # Check if the conversation file exists
        if not os.path.exists(conversation_path):
            return None
        
        # Load the conversation data
        with open(conversation_path, "r") as f:
            conversation_data = json.load(f)
        
        # Convert timestamps from strings to datetime objects
        created_at = datetime.fromisoformat(conversation_data["created_at"])
        updated_at = datetime.fromisoformat(conversation_data["updated_at"])
        
        # Convert messages from dicts to ChatMessage objects
        messages = [
            ChatMessage(**msg) for msg in conversation_data["messages"]
        ]
        
        # Return the conversation
        return ConversationResponse(
            id=conversation_data["id"],
            collection_name=conversation_data["collection_name"],
            title=conversation_data["title"],
            model=conversation_data.get("model"),
            messages=messages,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def update_conversation(self, conversation_id: str, update: ConversationUpdate) -> Optional[ConversationResponse]:
        """Update a conversation.
        
        Args:
            conversation_id: ID of the conversation
            update: Update data
            
        Returns:
            Updated conversation or None if not found
        """
        # Get the existing conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        # Update the conversation data
        conversation_data = conversation.dict()
        
        if update.title is not None:
            conversation_data["title"] = update.title
        
        if update.messages is not None:
            conversation_data["messages"] = [msg.dict() for msg in update.messages]
        
        # Update the timestamp
        conversation_data["updated_at"] = datetime.now()
        
        # Save the updated conversation
        with open(self._get_conversation_path(conversation_id), "w") as f:
            json.dump(conversation_data, f, default=self._serialize_datetime)
        
        # Return the updated conversation
        return ConversationResponse(
            id=conversation_id,
            collection_name=conversation_data["collection_name"],
            title=conversation_data["title"],
            model=conversation_data.get("model"),
            messages=[ChatMessage(**msg) if isinstance(msg, dict) else msg for msg in conversation_data["messages"]],
            created_at=conversation_data["created_at"],
            updated_at=conversation_data["updated_at"]
        )
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            True if the conversation was deleted, False otherwise
        """
        conversation_path = self._get_conversation_path(conversation_id)
        
        # Check if the conversation file exists
        if not os.path.exists(conversation_path):
            return False
        
        # Delete the conversation file
        os.remove(conversation_path)
        return True
    
    def list_conversations(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """List all conversations.
        
        Args:
            skip: Number of conversations to skip
            limit: Maximum number of conversations to return
            
        Returns:
            Dictionary with conversations and total count
        """
        # Get all conversation files
        conversation_files = [
            f for f in os.listdir(self.conversations_dir)
            if f.endswith(".json")
        ]
        
        # Sort conversation files by modification time (newest first)
        conversation_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(self.conversations_dir, f)),
            reverse=True
        )
        
        # Apply pagination
        conversation_files = conversation_files[skip:skip + limit]
        
        # Load conversations
        conversations = []
        for file in conversation_files:
            conversation_id = file.replace(".json", "")
            conversation = self.get_conversation(conversation_id)
            if conversation:
                conversations.append(conversation)
        
        # Return conversations and total count
        return {
            "conversations": conversations,
            "total": len(os.listdir(self.conversations_dir))
        }
    
    def clear_all_conversations(self) -> None:
        """Clear all conversations (for testing purposes)."""
        if os.path.exists(self.conversations_dir):
            shutil.rmtree(self.conversations_dir)
            os.makedirs(self.conversations_dir, exist_ok=True)


# Create a singleton instance
conversation_store = ConversationStore()