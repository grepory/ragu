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


class DeleteDocumentRequest(BaseModel):
    """Schema for delete document by source request."""
    source: str = Field(..., description="Source filename to delete")


class UpdateDocumentTagsRequest(BaseModel):
    """Schema for updating document tags request."""
    source: str = Field(..., description="Source filename to update")
    tags: List[str] = Field(..., description="New tags for the document")


class TextInput(BaseModel):
    """Schema for text input."""
    text: str = Field(..., description="Text content to process")
    collection_name: Optional[str] = Field(None, description="Name of the collection to add the text to (deprecated)")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Query schemas
class QueryRequest(BaseModel):
    """Schema for query request."""
    collection_name: Optional[str] = Field(None, description="Name of the collection to query (deprecated)")
    query_text: str = Field(..., description="Query text")
    n_results: int = Field(5, description="Number of results to return")
    where: Optional[Dict[str, Any]] = Field(None, description="Filter criteria")
    tags: Optional[List[str]] = Field(None, description="Tags to filter by")
    include_untagged: bool = Field(True, description="Whether to include untagged documents")


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
    collection_name: Optional[str] = Field(None, description="Name of the collection to query (deprecated)")
    query: str = Field(..., description="User query")
    history: Optional[List[ChatMessage]] = Field(None, description="Chat history")
    model: Optional[str] = Field(None, description="LLM model to use")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation to continue")
    tags: Optional[List[str]] = Field(None, description="Tags to filter documents by")
    include_untagged: bool = Field(True, description="Whether to include untagged documents")


class ChatResponse(BaseModel):
    """Schema for chat response."""
    answer: str = Field(..., description="LLM response")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents used for the response")
    history: List[ChatMessage] = Field(..., description="Updated chat history")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation")


# Conversation schemas
class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    collection_name: Optional[str] = Field(None, description="Name of the collection used in the conversation (deprecated)")
    title: Optional[str] = Field(None, description="Title of the conversation")
    model: Optional[str] = Field(None, description="LLM model used in the conversation")
    messages: List[ChatMessage] = Field(..., description="Messages in the conversation")
    tags: Optional[List[str]] = Field(None, description="Tags used for document filtering")
    include_untagged: bool = Field(True, description="Whether to include untagged documents in queries")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, description="Title of the conversation")
    messages: Optional[List[ChatMessage]] = Field(None, description="Messages in the conversation")
    tags: Optional[List[str]] = Field(None, description="Tags used for document filtering")
    include_untagged: Optional[bool] = Field(None, description="Whether to include untagged documents in queries")


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: str = Field(..., description="Conversation ID")
    collection_name: Optional[str] = Field(None, description="Name of the collection used in the conversation (deprecated)")
    title: str = Field(..., description="Title of the conversation")
    model: Optional[str] = Field(None, description="LLM model used in the conversation")
    messages: List[ChatMessage] = Field(..., description="Messages in the conversation")
    tags: Optional[List[str]] = Field(None, description="Tags used for document filtering")
    include_untagged: bool = Field(True, description="Whether to include untagged documents in queries")
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


# Tag-based schemas
class TagListResponse(BaseModel):
    """Schema for tag list response."""
    tags: List[str] = Field(..., description="List of all tags")
    tag_counts: Dict[str, int] = Field(..., description="Tag usage counts")


class TagBasedQueryRequest(BaseModel):
    """Schema for tag-based query request."""
    query_text: str = Field(..., description="Query text")
    tags: Optional[List[str]] = Field(None, description="Tags to filter by")
    include_untagged: bool = Field(True, description="Whether to include untagged documents")
    n_results: int = Field(5, description="Number of results to return")


class DocumentUploadRequest(BaseModel):
    """Schema for document upload request (tag-based)."""
    tags: Optional[List[str]] = Field(None, description="Tags to associate with the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")