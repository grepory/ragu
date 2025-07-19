// Vue.js component for model selection and querying

// Define available models
const availableModels = [
    { value: 'ollama:llama2', label: 'Ollama: Llama 2' },
    { value: 'ollama:mistral', label: 'Ollama: Mistral' },
    { value: 'ollama:nomic-embed-text', label: 'Ollama: Nomic Embed Text' },
    { value: 'anthropic:claude-3-haiku-20240307', label: 'Anthropic: Claude 3 Haiku' },
    { value: 'anthropic:claude-3-sonnet-20240229', label: 'Anthropic: Claude 3 Sonnet' },
    { value: 'anthropic:claude-3-opus-20240229', label: 'Anthropic: Claude 3 Opus' },
    { value: 'openai:gpt-4o', label: 'OpenAI: GPT-4o' },
    { value: 'openai:gpt-4-turbo', label: 'OpenAI: GPT-4 Turbo' },
    { value: 'openai:gpt-3.5-turbo', label: 'OpenAI: GPT-3.5 Turbo' }
];

// Create Vue app
const { createApp, ref, onMounted, computed, watch } = Vue;

const ModelQueryComponent = {
    template: `
        <div class="model-query-component">
            <!-- Conversation List Modal -->
            <div v-if="showConversationList" class="conversation-list-modal">
                <div class="conversation-list-header">
                    <h4><i class="bi bi-chat-left-text me-2"></i>Conversations</h4>
                    <button class="btn btn-sm btn-outline-secondary" @click="startNewConversation">
                        <i class="bi bi-plus-circle me-1"></i>New Conversation
                    </button>
                </div>
                
                <div v-if="isLoadingConversations" class="text-center p-4">
                    <div class="loading-spinner"></div>
                    <p class="mt-2">Loading conversations...</p>
                </div>
                
                <div v-else-if="conversations.length === 0" class="text-center text-muted p-4">
                    <i class="bi bi-chat-square-text fs-2"></i>
                    <p class="mt-2">No conversations yet</p>
                    <button class="btn btn-primary mt-2" @click="startNewConversation">
                        Start a new conversation
                    </button>
                </div>
                
                <div v-else class="conversation-list">
                    <div v-for="conversation in conversations" :key="conversation.id" 
                         class="conversation-item p-3 mb-2">
                        <div class="conversation-content" @click="selectConversation(conversation.id)">
                            <div class="conversation-title">
                                <i class="bi bi-chat-text me-2"></i>
                                {{ conversation.title }}
                            </div>
                            <div class="conversation-meta">
                                <small class="text-muted">
                                    {{ new Date(conversation.updated_at).toLocaleString() }}
                                    <span class="ms-2">{{ conversation.messages.length }} messages</span>
                                </small>
                            </div>
                        </div>
                        <div class="conversation-actions">
                            <button class="btn btn-sm btn-outline-secondary me-1" 
                                    @click.stop="renameConversation(conversation)"
                                    title="Rename conversation">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" 
                                    @click.stop="confirmDeleteConversation(conversation)"
                                    title="Delete conversation">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Conversation history - Primary visual element -->
            <div v-if="!showConversationList" class="conversation-wrapper">
                <div class="conversation-header">
                    <button class="btn btn-sm btn-outline-secondary" @click="toggleConversationList">
                        <i class="bi bi-list me-1"></i>Conversations
                    </button>
                    <span v-if="currentConversationId" class="conversation-title">
                        {{ conversations.find(c => c.id === currentConversationId)?.title || 'Current Conversation' }}
                    </span>
                </div>
                
                <div v-if="conversationHistory.length > 0" class="conversation-history">
                    <div class="conversation-container p-3">
                        <div v-for="(message, index) in conversationHistory" :key="index" 
                             :class="['message mb-2 p-2 rounded', message.role === 'user' ? 'user-message text-end' : 'assistant-message']">
                            <div class="message-header mb-1">
                                <small class="fw-bold">
                                    <i :class="['bi me-1', message.role === 'user' ? 'bi-person-circle' : 'bi-robot']"></i>
                                    {{ message.role === 'user' ? 'You' : 'Assistant' }}
                                </small>
                            </div>
                            <div class="message-content">
                                {{ message.content }}
                            </div>
                        </div>
                    </div>
                </div>
                <div v-else class="empty-conversation-placeholder">
                    <div class="text-center text-muted p-5">
                        <i class="bi bi-chat-square-text fs-1"></i>
                        <p class="mt-3">Your conversation will appear here</p>
                    </div>
                </div>
            </div>
            
            <!-- Input area fixed at bottom -->
            <div class="chat-input-area">
                <!-- Small dropdowns for model and collection selection -->
                <div class="dropdowns-container">
                    <!-- Collection selection -->
                    <div class="dropdown-item collection-dropdown">
                        <label for="collection-select" class="form-label small-label">
                            <i class="bi bi-collection me-1"></i> Collection
                        </label>
                        <div class="input-group input-group-sm">
                            <select 
                                id="collection-select"
                                class="form-select form-select-sm"
                                v-model="selectedCollection"
                            >
                                <option value="">Select a collection</option>
                                <option v-for="collection in collections" :key="collection" :value="collection">
                                    {{ collection }}
                                </option>
                            </select>
                            <button 
                                class="btn btn-outline-secondary btn-sm" 
                                type="button"
                                @click="createCollection"
                            >
                                New
                            </button>
                        </div>
                        <div class="form-text small-text" v-if="collections.length === 0">
                            No collections found. Please upload documents first.
                        </div>
                    </div>
                    
                    <!-- Model selection -->
                    <div class="dropdown-item model-dropdown">
                        <label for="model-select" class="form-label small-label">
                            <i class="bi bi-cpu me-1"></i> Model
                        </label>
                        <select 
                            id="model-select"
                            class="form-select form-select-sm"
                            v-model="selectedModel"
                        >
                            <option value="">Default Model</option>
                            <optgroup label="Ollama Models">
                                <option v-for="model in models.filter(m => m.value.startsWith('ollama'))" :key="model.value" :value="model.value">
                                    {{ model.label }}
                                </option>
                            </optgroup>
                            <optgroup label="Anthropic Models">
                                <option v-for="model in models.filter(m => m.value.startsWith('anthropic'))" :key="model.value" :value="model.value">
                                    {{ model.label }}
                                </option>
                            </optgroup>
                            <optgroup label="OpenAI Models">
                                <option v-for="model in models.filter(m => m.value.startsWith('openai'))" :key="model.value" :value="model.value">
                                    {{ model.label }}
                                </option>
                            </optgroup>
                        </select>
                    </div>
                </div>
                
                <!-- Query input -->
                <div class="query-input">
                    <textarea
                        id="query-textarea"
                        class="form-control"
                        v-model="queryText"
                        placeholder="Type your message here..."
                        rows="2"
                        @keydown.enter.prevent="handleEnterKey"
                    ></textarea>
                    
                    <!-- Submit button -->
                    <button 
                        class="btn btn-primary send-button"
                        @click="submitQuery"
                        :disabled="isLoading || !canSubmit"
                    >
                        <i v-if="!isLoading" class="bi bi-send"></i>
                        <span v-if="isLoading" class="loading-spinner"></span>
                        <span class="button-text">{{ isLoading ? 'Processing...' : 'Send' }}</span>
                    </button>
                </div>
                
                <!-- Error message -->
                <div v-if="error" class="alert alert-danger mt-2 mb-0 py-2 small">
                    {{ error }}
                </div>
                
                <!-- Model info -->
                <div class="model-info text-end">
                    <small class="text-muted">
                        <i class="bi bi-info-circle me-1"></i>
                        Model: {{ selectedModel || 'Default' }}
                    </small>
                </div>
            </div>
        </div>
    `,
    setup() {
        // Reactive state
        const collections = ref([]);
        const selectedCollection = ref('');
        const models = ref(availableModels);
        const selectedModel = ref('');
        const queryText = ref('');
        const isLoading = ref(false);
        const error = ref('');
        const results = ref(null);
        const conversationHistory = ref([]);
        const lastSources = ref([]);
        const conversations = ref([]);
        const currentConversationId = ref(null);
        const showConversationList = ref(false);
        const isLoadingConversations = ref(false);
        
        // Local storage keys for persistence
        const STORAGE_KEY_COLLECTION = 'ragu_selected_collection';
        const STORAGE_KEY_MODEL = 'ragu_selected_model';
        
        // Computed properties
        const canSubmit = computed(() => {
            return selectedCollection.value && queryText.value.trim().length > 0;
        });
        
        // Fetch collections on component mount and load saved preferences
        onMounted(async () => {
            await fetchCollections();
            
            // Load saved model preference
            const savedModel = localStorage.getItem(STORAGE_KEY_MODEL);
            if (savedModel) {
                // Check if the saved model exists in available models
                const modelExists = models.value.some(model => model.value === savedModel);
                if (modelExists) {
                    selectedModel.value = savedModel;
                }
            }
            
            // Note: We'll apply the saved collection after collections are loaded
            // This happens in the fetchCollections function
            
            // Show conversation list when chat is first opened
            fetchConversations();
            showConversationList.value = true;
        });
        
        // Watch for changes to selectedCollection and save to localStorage
        watch(selectedCollection, (newValue) => {
            if (newValue) {
                localStorage.setItem(STORAGE_KEY_COLLECTION, newValue);
            }
        });
        
        // Watch for changes to selectedModel and save to localStorage
        watch(selectedModel, (newValue) => {
            if (newValue) {
                localStorage.setItem(STORAGE_KEY_MODEL, newValue);
            }
        });
        
        // Fetch collections from API
        const fetchCollections = async () => {
            try {
                const response = await fetch('/api/v1/collections/');
                if (response.ok) {
                    const data = await response.json();
                    collections.value = data.collections || [];
                    
                    // Check if we have collections
                    if (data.collections && data.collections.length > 0) {
                        // Try to load saved collection preference
                        const savedCollection = localStorage.getItem(STORAGE_KEY_COLLECTION);
                        
                        if (savedCollection && data.collections.includes(savedCollection)) {
                            // Use saved collection if it exists
                            selectedCollection.value = savedCollection;
                        } else {
                            // Otherwise use the first collection
                            selectedCollection.value = data.collections[0];
                        }
                    }
                } else {
                    console.error('Failed to fetch collections');
                    error.value = 'Failed to fetch collections. Please try again.';
                }
            } catch (err) {
                console.error('Error fetching collections:', err);
                error.value = `Error fetching collections: ${err.message}`;
            }
        };
        
        // Create a new collection
        const createCollection = async () => {
            const collectionName = prompt('Enter a name for the new collection:');
            if (!collectionName) return;
            
            try {
                const response = await fetch('/api/v1/collections/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: collectionName,
                        description: `Collection created on ${new Date().toLocaleString()}`
                    })
                });
                
                if (response.ok) {
                    await fetchCollections();
                    selectedCollection.value = collectionName;
                } else {
                    const errorData = await response.json();
                    error.value = `Failed to create collection: ${errorData.detail || 'Unknown error'}`;
                }
            } catch (err) {
                console.error('Error creating collection:', err);
                error.value = `Error creating collection: ${err.message}`;
            }
        };
        
        // Fetch conversations from API
        const fetchConversations = async () => {
            isLoadingConversations.value = true;
            error.value = '';
            
            try {
                const response = await fetch('/api/v1/conversations/');
                if (response.ok) {
                    const data = await response.json();
                    conversations.value = data.conversations || [];
                } else {
                    console.error('Failed to fetch conversations');
                    error.value = 'Failed to fetch conversations. Please try again.';
                }
            } catch (err) {
                console.error('Error fetching conversations:', err);
                error.value = `Error fetching conversations: ${err.message}`;
            } finally {
                isLoadingConversations.value = false;
            }
        };
        
        // Select a conversation
        const selectConversation = async (conversationId) => {
            try {
                const response = await fetch(`/api/v1/conversations/${conversationId}`);
                if (response.ok) {
                    const conversation = await response.json();
                    
                    // Set the current conversation ID
                    currentConversationId.value = conversationId;
                    
                    // Set the conversation history
                    conversationHistory.value = conversation.messages;
                    
                    // Set the collection and model if available
                    if (conversation.collection_name) {
                        selectedCollection.value = conversation.collection_name;
                    }
                    
                    if (conversation.model) {
                        selectedModel.value = conversation.model;
                    }
                    
                    // Hide the conversation list
                    showConversationList.value = false;
                    
                    // Scroll to the bottom of the conversation container
                    setTimeout(() => {
                        const container = document.querySelector('.conversation-container');
                        if (container) {
                            container.scrollTop = container.scrollHeight;
                        }
                    }, 50);
                } else {
                    const errorData = await response.json();
                    error.value = `Failed to load conversation: ${errorData.detail || 'Unknown error'}`;
                }
            } catch (err) {
                console.error('Error loading conversation:', err);
                error.value = `Error loading conversation: ${err.message}`;
            }
        };
        
        // Start a new conversation
        const startNewConversation = () => {
            // Clear the current conversation
            currentConversationId.value = null;
            conversationHistory.value = [];
            
            // Hide the conversation list
            showConversationList.value = false;
        };
        
        // Toggle conversation list
        const toggleConversationList = () => {
            showConversationList.value = !showConversationList.value;
            
            // If showing the conversation list, fetch the latest conversations
            if (showConversationList.value) {
                fetchConversations();
            }
        };
        
        // Handle Enter key press
        const handleEnterKey = (event) => {
            // Only submit if not pressing shift+enter (which should create a new line)
            if (!event.shiftKey && queryText.value.trim()) {
                submitQuery();
            }
        };
        
        // Submit query to API
        const submitQuery = async () => {
            if (!canSubmit.value) return;
            
            isLoading.value = true;
            error.value = '';
            
            // We don't need to add the user message to conversation history here
            // because the backend will add it to the history it returns
            
            // Scroll to the bottom of the conversation container
            setTimeout(() => {
                const container = document.querySelector('.conversation-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }, 50);
            
            try {
                // Prepare request data
                const requestData = {
                    collection_name: selectedCollection.value,
                    query: queryText.value,
                    history: conversationHistory.value
                };
                
                // Add model if selected
                if (selectedModel.value) {
                    requestData.model = selectedModel.value;
                }
                
                // Add conversation ID if we're continuing a conversation
                if (currentConversationId.value) {
                    requestData.conversation_id = currentConversationId.value;
                }
                
                // Clear the query text
                const currentQuery = queryText.value;
                queryText.value = '';
                
                // Send request to chat API
                const response = await fetch('/api/v1/chat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (response.ok) {
                    const data = await response.json();
                    results.value = data;
                    
                    // Update conversation history with the response
                    conversationHistory.value = data.history;
                    
                    // Update last sources
                    lastSources.value = data.sources;
                    
                    // Update current conversation ID if provided
                    if (data.conversation_id) {
                        currentConversationId.value = data.conversation_id;
                    }
                    
                    // Scroll to the bottom of the conversation container
                    setTimeout(() => {
                        const container = document.querySelector('.conversation-container');
                        if (container) {
                            container.scrollTop = container.scrollHeight;
                        }
                    }, 50);
                    
                    // Clear the results container (we're now using the conversation history)
                    const resultsContainer = document.getElementById('results-container');
                    if (resultsContainer) {
                        resultsContainer.innerHTML = '';
                    }
                } else {
                    // Restore the query text
                    queryText.value = currentQuery;
                    
                    const errorData = await response.json();
                    error.value = errorData.detail || 'Failed to process query. Please try again.';
                }
            } catch (err) {
                console.error('Error submitting query:', err);
                error.value = `Error submitting query: ${err.message}`;
            } finally {
                isLoading.value = false;
            }
        };
        
        // Rename a conversation
        const renameConversation = async (conversation) => {
            // Prompt for new title
            const newTitle = prompt('Enter a new title for the conversation:', conversation.title);
            
            // If user cancels or enters an empty title, do nothing
            if (!newTitle || newTitle.trim() === '') return;
            
            try {
                // Send request to update the conversation
                const response = await fetch(`/api/v1/conversations/${conversation.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: newTitle.trim()
                    })
                });
                
                if (response.ok) {
                    // Update the conversation in the list
                    const updatedConversation = await response.json();
                    const index = conversations.value.findIndex(c => c.id === conversation.id);
                    if (index !== -1) {
                        conversations.value[index] = updatedConversation;
                    }
                    
                    // If this is the current conversation, update the title in the header
                    if (currentConversationId.value === conversation.id) {
                        // The title will be updated automatically through the conversations array
                    }
                } else {
                    const errorData = await response.json();
                    error.value = `Failed to rename conversation: ${errorData.detail || 'Unknown error'}`;
                }
            } catch (err) {
                console.error('Error renaming conversation:', err);
                error.value = `Error renaming conversation: ${err.message}`;
            }
        };
        
        // Confirm deletion of a conversation
        const confirmDeleteConversation = (conversation) => {
            if (confirm(`Are you sure you want to delete the conversation "${conversation.title}"? This action cannot be undone.`)) {
                deleteConversation(conversation.id);
            }
        };
        
        // Delete a conversation
        const deleteConversation = async (conversationId) => {
            try {
                // Send request to delete the conversation
                const response = await fetch(`/api/v1/conversations/${conversationId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    // Remove the conversation from the list
                    conversations.value = conversations.value.filter(c => c.id !== conversationId);
                    
                    // If this is the current conversation, clear it
                    if (currentConversationId.value === conversationId) {
                        currentConversationId.value = null;
                        conversationHistory.value = [];
                    }
                } else {
                    const errorData = await response.json();
                    error.value = `Failed to delete conversation: ${errorData.detail || 'Unknown error'}`;
                }
            } catch (err) {
                console.error('Error deleting conversation:', err);
                error.value = `Error deleting conversation: ${err.message}`;
            }
        };
        
        return {
            collections,
            selectedCollection,
            models,
            selectedModel,
            queryText,
            isLoading,
            error,
            results,
            conversationHistory,
            lastSources,
            conversations,
            currentConversationId,
            showConversationList,
            isLoadingConversations,
            canSubmit,
            submitQuery,
            handleEnterKey,
            createCollection,
            fetchConversations,
            selectConversation,
            startNewConversation,
            toggleConversationList,
            renameConversation,
            confirmDeleteConversation
        };
    }
};

// Create and mount the Vue app
const app = createApp({
    components: {
        'model-query-component': ModelQueryComponent
    }
});

app.mount('#model-query-container');