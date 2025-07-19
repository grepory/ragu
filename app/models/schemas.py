from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


# Collection schemas
class CollectionCreate(BaseModel):
    """Schema for creating a new collection."""
    name: str = Field(..., description="Name of the collection")
    description: Optional[str] = Field(None, description="Description of the collection")


class CollectionResponse(BaseModel):
    """Schema for collection response."""
    name: str = Field(..., description="Name of the collection")
    description: Optional[str] = Field(None, description="Description of the collection")


class CollectionList(BaseModel):
    """Schema for list of collections."""
    collections: List[str] = Field(..., description="List of collection names")


# Document schemas
class DocumentMetadata(BaseModel):
    """Schema for document metadata."""
    source: str = Field(..., description="Source of the document")
    chunk: Optional[int] = Field(None, description="Chunk number")
    total_chunks: Optional[int] = Field(None, description="Total number of chunks")
    page: Optional[int] = Field(None, description="Page number for PDF documents")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the document")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text")
    metadata: DocumentMetadata = Field(..., description="Document metadata")


class DocumentList(BaseModel):
    """Schema for list of documents."""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


class TextInput(BaseModel):
    """Schema for text input."""
    text: str = Field(..., description="Text content to process")
    collection_name: str = Field(..., description="Name of the collection to add the text to")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Query schemas
class QueryRequest(BaseModel):
    """Schema for query request."""
    collection_name: str = Field(..., description="Name of the collection to query")
    query_text: str = Field(..., description="Query text")
    n_results: int = Field(5, description="Number of results to return")
    where: Optional[Dict[str, Any]] = Field(None, description="Filter criteria")


class QueryResult(BaseModel):
    """Schema for a single query result."""
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    score: float = Field(..., description="Similarity score")


class QueryResponse(BaseModel):
    """Schema for query response."""
    results: List[QueryResult] = Field(..., description="Query results")
    query: str = Field(..., description="Original query")


# Chat schemas
class ChatMessage(BaseModel):
    """Schema for chat message."""
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Schema for chat request."""
    collection_name: str = Field(..., description="Name of the collection to query")
    query: str = Field(..., description="User query")
    history: Optional[List[ChatMessage]] = Field(None, description="Chat history")
    model: Optional[str] = Field(None, description="LLM model to use")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation to continue")


class ChatResponse(BaseModel):
    """Schema for chat response."""
    answer: str = Field(..., description="LLM response")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents used for the response")
    history: List[ChatMessage] = Field(..., description="Updated chat history")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation")


# Conversation schemas
class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    collection_name: str = Field(..., description="Name of the collection used in the conversation")
    title: Optional[str] = Field(None, description="Title of the conversation")
    model: Optional[str] = Field(None, description="LLM model used in the conversation")
    messages: List[ChatMessage] = Field(..., description="Messages in the conversation")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, description="Title of the conversation")
    messages: Optional[List[ChatMessage]] = Field(None, description="Messages in the conversation")


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: str = Field(..., description="Conversation ID")
    collection_name: str = Field(..., description="Name of the collection used in the conversation")
    title: str = Field(..., description="Title of the conversation")
    model: Optional[str] = Field(None, description="LLM model used in the conversation")
    messages: List[ChatMessage] = Field(..., description="Messages in the conversation")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ConversationList(BaseModel):
    """Schema for list of conversations."""
    conversations: List[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total number of conversations")


class TitleGenerationRequest(BaseModel):
    """Schema for title generation request."""
    messages: List[ChatMessage] = Field(..., description="Messages to generate title from")
    model: Optional[str] = Field(None, description="LLM model to use for title generation")


class TitleGenerationResponse(BaseModel):
    """Schema for title generation response."""
    title: str = Field(..., description="Generated title")