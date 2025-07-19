from typing import List, Dict, Any, Optional, Callable, AsyncGenerator, Protocol, Union, Type
import json
import abc
from llama_index.llms import Ollama
from llama_index.core.llms import ChatMessage as LlamaIndexChatMessage
from llama_index.core.callbacks import CallbackManager
from llama_index.core.base.llms.types import ChatResponse, MessageRole, LLM
from llama_index.core.prompts import PromptTemplate

# Import these conditionally to avoid errors if not installed
try:
    from llama_index.llms.anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    
try:
    from llama_index.llms.openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.core.config import settings, LLMProvider
from app.db.chroma_client import chroma_client
from app.models.schemas import ChatMessage

# System prompt template for RAG
RAG_SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on the provided context.
Use the following pieces of context to answer the user's question. If you don't know the answer, just say that you don't know, don't try to make up an answer.
Be concise and clear in your response. Always cite your sources at the end of your response.

Context:
{context}

Question: {query}

Answer:"""


class StreamingCallbackHandler:
    """Callback handler for streaming LLM responses."""
    
    def __init__(self, websocket):
        """Initialize with WebSocket connection."""
        self.websocket = websocket
    
    async def on_token(self, token: str, **kwargs) -> None:
        """Send new token to client via WebSocket."""
        await self.websocket.send_json({
            "type": "token",
            "content": token
        })


class LLMProviderBase(abc.ABC):
    """Base class for LLM providers."""
    
    @abc.abstractmethod
    def get_llm(self, model: Optional[str] = None, streaming: bool = False, 
                callback_handler: Optional[StreamingCallbackHandler] = None) -> LLM:
        """Get LLM instance.
        
        Args:
            model: Model name
            streaming: Whether to stream responses
            callback_handler: Callback handler for streaming
            
        Returns:
            LLM instance
        """
        pass
    
    @abc.abstractmethod
    def get_default_model(self) -> str:
        """Get default model for this provider.
        
        Returns:
            Default model name
        """
        pass


class OllamaProvider(LLMProviderBase):
    """Ollama LLM provider."""
    
    def get_llm(self, model: Optional[str] = None, streaming: bool = False, 
                callback_handler: Optional[StreamingCallbackHandler] = None) -> LLM:
        """Get Ollama LLM instance.
        
        Args:
            model: Model name
            streaming: Whether to stream responses
            callback_handler: Callback handler for streaming
            
        Returns:
            Ollama LLM instance
        """
        callback_manager = None
        if streaming and callback_handler:
            callback_manager = CallbackManager([callback_handler])
            
        return Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=model or self.get_default_model(),
            temperature=0.7,
            streaming=streaming,
            callback_manager=callback_manager
        )
    
    def get_default_model(self) -> str:
        """Get default model for Ollama.
        
        Returns:
            Default model name
        """
        return settings.OLLAMA_DEFAULT_MODEL


class AnthropicProvider(LLMProviderBase):
    """Anthropic LLM provider."""
    
    def get_llm(self, model: Optional[str] = None, streaming: bool = False, 
                callback_handler: Optional[StreamingCallbackHandler] = None) -> LLM:
        """Get Anthropic LLM instance.
        
        Args:
            model: Model name
            streaming: Whether to stream responses
            callback_handler: Callback handler for streaming
            
        Returns:
            Anthropic LLM instance
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package is not installed. Please install it with 'pip install llama-index-llms-anthropic'")
            
        callback_manager = None
        if streaming and callback_handler:
            callback_manager = CallbackManager([callback_handler])
            
        return Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            model=model or self.get_default_model(),
            temperature=0.7,
            streaming=streaming,
            callback_manager=callback_manager
        )
    
    def get_default_model(self) -> str:
        """Get default model for Anthropic.
        
        Returns:
            Default model name
        """
        return settings.ANTHROPIC_DEFAULT_MODEL


class OpenAIProvider(LLMProviderBase):
    """OpenAI LLM provider."""
    
    def get_llm(self, model: Optional[str] = None, streaming: bool = False, 
                callback_handler: Optional[StreamingCallbackHandler] = None) -> LLM:
        """Get OpenAI LLM instance.
        
        Args:
            model: Model name
            streaming: Whether to stream responses
            callback_handler: Callback handler for streaming
            
        Returns:
            OpenAI LLM instance
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is not installed. Please install it with 'pip install llama-index-llms-openai'")
            
        callback_manager = None
        if streaming and callback_handler:
            callback_manager = CallbackManager([callback_handler])
            
        return OpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=model or self.get_default_model(),
            temperature=0.7,
            streaming=streaming,
            callback_manager=callback_manager
        )
    
    def get_default_model(self) -> str:
        """Get default model for OpenAI.
        
        Returns:
            Default model name
        """
        return settings.OPENAI_DEFAULT_MODEL


class LLMService:
    """Service for interacting with LLMs."""
    
    def __init__(self):
        """Initialize LLM service."""
        self.providers = {
            LLMProvider.OLLAMA: OllamaProvider(),
            LLMProvider.ANTHROPIC: AnthropicProvider(),
            LLMProvider.OPENAI: OpenAIProvider()
        }
        self.default_provider = settings.DEFAULT_LLM_PROVIDER
        # For backward compatibility
        self.default_model = settings.DEFAULT_MODEL
    
    def _parse_model_string(self, model_string: Optional[str]) -> tuple[LLMProvider, Optional[str]]:
        """Parse model string to get provider and model.
        
        Format: provider:model or just model (uses default provider)
        
        Args:
            model_string: Model string to parse
            
        Returns:
            Tuple of (provider, model)
        """
        if not model_string:
            return self.default_provider, None
            
        if ":" in model_string:
            provider_str, model = model_string.split(":", 1)
            try:
                provider = LLMProvider(provider_str.lower())
            except ValueError:
                # If provider is invalid, use default provider
                return self.default_provider, model_string
            return provider, model
        
        return self.default_provider, model_string
    
    def get_llm(self, model: Optional[str] = None, streaming: bool = False, 
                callback_handler: Optional[StreamingCallbackHandler] = None) -> LLM:
        """Get LLM instance.
        
        Args:
            model: Model name or provider:model (defaults to default model)
            streaming: Whether to stream responses
            callback_handler: Callback handler for streaming
            
        Returns:
            LLM instance
        """
        provider_enum, model_name = self._parse_model_string(model)
        
        # Get provider instance
        provider = self.providers[provider_enum]
        
        # Get LLM from provider
        return provider.get_llm(model=model_name, streaming=streaming, callback_handler=callback_handler)
    
    async def generate_rag_response(
        self,
        query: str,
        collection_name: str,
        history: Optional[List[ChatMessage]] = None,
        model: Optional[str] = None,
        streaming: bool = False,
        callback_handler: Optional[StreamingCallbackHandler] = None,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """Generate RAG response.
        
        Args:
            query: User query
            collection_name: Name of the collection to query
            history: Optional chat history
            model: Optional model name or provider:model
            streaming: Whether to stream responses
            callback_handler: Callback handler for streaming
            n_results: Number of results to retrieve from vector DB
            
        Returns:
            Response data with answer and sources
        """
        # Query vector database for relevant documents
        results = chroma_client.query_collection(
            collection_name=collection_name,
            query_text=query,
            n_results=n_results
        )
        
        # Extract context from results
        context_texts = []
        sources = []
        
        if results and results.get("ids") and results.get("ids")[0]:
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                text = results["documents"][0][i] if results.get("documents") and results["documents"][0] else ""
                metadata = results["metadatas"][0][i] if results.get("metadatas") and results["metadatas"][0] else {}
                
                if text:
                    context_texts.append(f"[Document {i+1}]: {text}")
                    sources.append({
                        "id": doc_id,
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "metadata": metadata
                    })
        
        # Combine context texts
        context = "\n\n".join(context_texts) if context_texts else "No relevant information found."
        
        # Get LLM
        llm = self.get_llm(model=model, streaming=streaming, callback_handler=callback_handler)
        
        # Create prompt
        prompt = PromptTemplate(template=RAG_SYSTEM_PROMPT)
        
        # Format the prompt with context and query
        formatted_prompt = prompt.format(context=context, query=query)
        
        # Generate response
        if streaming:
            # For streaming, we need to collect all tokens
            response_text = ""
            async for token in await llm.astream_complete(formatted_prompt):
                response_text += token.delta
            response = response_text
        else:
            # For non-streaming, we can just get the complete response
            response = await llm.acomplete(formatted_prompt)
            response = response.text
        
        # Update history if provided
        updated_history = []
        if history:
            updated_history = history.copy()
        
        # Add current exchange to history
        updated_history.append(ChatMessage(role="user", content=query))
        updated_history.append(ChatMessage(role="assistant", content=response))
        
        return {
            "answer": response,
            "sources": sources,
            "history": updated_history
        }


# Create a singleton instance
llm_service = LLMService()