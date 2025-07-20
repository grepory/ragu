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
            <!-- Conversation history - Primary visual element -->
            <div class="conversation-wrapper">
                
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
                <!-- Small dropdowns for model and tag selection -->
                <div class="dropdowns-container">
                    <!-- Tag selection -->
                    <div class="dropdown-item tag-dropdown">
                        <label for="tag-select" class="form-label small-label">
                            <i class="bi bi-tags me-1"></i> Tags
                        </label>
                        <div class="tag-selection-container">
                            <div class="tag-checkboxes" v-if="availableTags.length > 0">
                                <div class="tag-checkbox" v-for="tag in availableTags" :key="tag">
                                    <input 
                                        type="checkbox" 
                                        :id="'tag-' + tag" 
                                        :value="tag" 
                                        v-model="selectedTags"
                                        class="form-check-input"
                                    >
                                    <label :for="'tag-' + tag" class="form-check-label">
                                        {{ tag }} <span class="tag-count">({{ tagCounts[tag] || 0 }})</span>
                                    </label>
                                </div>
                            </div>
                            <div class="tag-options" v-if="availableTags.length > 0">
                                <div class="form-check">
                                    <input 
                                        type="checkbox" 
                                        id="include-untagged" 
                                        v-model="includeUntagged"
                                        class="form-check-input"
                                    >
                                    <label for="include-untagged" class="form-check-label small-text">
                                        Include untagged documents
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="form-text small-text" v-if="availableTags.length === 0">
                            No tags found. Upload documents with tags first.
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
                
                <!-- Model and tag info -->
                <div class="model-info text-end">
                    <small class="text-muted">
                        <i class="bi bi-info-circle me-1"></i>
                        Model: {{ selectedModel || 'Default' }}
                        <span v-if="selectedTags.length > 0"> | Tags: {{ selectedTags.join(', ') }}</span>
                        <span v-if="includeUntagged && selectedTags.length > 0"> + untagged</span>
                        <span v-if="selectedTags.length === 0 && includeUntagged"> | All documents</span>
                    </small>
                </div>
            </div>
        </div>
    `,
    setup() {
        // Reactive state
        const collections = ref([]);  // Deprecated but kept for compatibility
        const selectedCollection = ref('');  // Deprecated
        const availableTags = ref([]);
        const tagCounts = ref({});
        const selectedTags = ref([]);
        const includeUntagged = ref(true);
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
        const isLoadingConversations = ref(false);
        
        // Local storage keys for persistence
        const STORAGE_KEY_COLLECTION = 'ragu_selected_collection';  // Deprecated
        const STORAGE_KEY_MODEL = 'ragu_selected_model';
        const STORAGE_KEY_TAGS = 'ragu_selected_tags';
        const STORAGE_KEY_INCLUDE_UNTAGGED = 'ragu_include_untagged';
        
        // Computed properties
        const canSubmit = computed(() => {
            return queryText.value.trim().length > 0;  // No longer require collection selection
        });
        
        // Fetch tags and load saved preferences on component mount
        onMounted(async () => {
            await fetchTags();
            
            // Load saved model preference
            const savedModel = localStorage.getItem(STORAGE_KEY_MODEL);
            if (savedModel) {
                // Check if the saved model exists in available models
                const modelExists = models.value.some(model => model.value === savedModel);
                if (modelExists) {
                    selectedModel.value = savedModel;
                }
            }
            
            // Load saved tag preferences
            const savedTags = localStorage.getItem(STORAGE_KEY_TAGS);
            if (savedTags) {
                try {
                    selectedTags.value = JSON.parse(savedTags);
                } catch (e) {
                    console.warn('Failed to parse saved tags:', e);
                }
            }
            
            const savedIncludeUntagged = localStorage.getItem(STORAGE_KEY_INCLUDE_UNTAGGED);
            if (savedIncludeUntagged !== null) {
                includeUntagged.value = savedIncludeUntagged === 'true';
            }
            
            // Load conversations for the sidebar
            fetchConversations();
            
            // Listen for custom events from sidebar
            document.addEventListener('loadConversation', (event) => {
                const conversationId = event.detail.conversationId;
                selectConversation(conversationId);
            });
            
            document.addEventListener('startNewConversation', () => {
                startNewConversation();
            });
        });
        
        // Watch for changes to selectedTags and save to localStorage and update conversation
        watch(selectedTags, (newValue) => {
            localStorage.setItem(STORAGE_KEY_TAGS, JSON.stringify(newValue));
            // Update conversation tag preferences if we have a current conversation (debounced)
            if (currentConversationId.value) {
                debouncedUpdateConversationTagPreferences(currentConversationId.value);
            }
        }, { deep: true });
        
        // Watch for changes to includeUntagged and save to localStorage and update conversation
        watch(includeUntagged, (newValue) => {
            localStorage.setItem(STORAGE_KEY_INCLUDE_UNTAGGED, newValue.toString());
            // Update conversation tag preferences if we have a current conversation (debounced)
            if (currentConversationId.value) {
                debouncedUpdateConversationTagPreferences(currentConversationId.value);
            }
        });
        
        // Watch for changes to selectedModel and save to localStorage
        watch(selectedModel, (newValue) => {
            if (newValue) {
                localStorage.setItem(STORAGE_KEY_MODEL, newValue);
            }
        });
        
        // Fetch available tags from API
        const fetchTags = async () => {
            try {
                const response = await fetch('/api/v1/tags/');
                if (response.ok) {
                    const data = await response.json();
                    availableTags.value = data.tags || [];
                    tagCounts.value = data.tag_counts || {};
                } else {
                    console.error('Failed to fetch tags');
                    error.value = 'Failed to fetch tags. Please try again.';
                }
            } catch (err) {
                console.error('Error fetching tags:', err);
                error.value = `Error fetching tags: ${err.message}`;
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
                    
                    // Set the tags and model if available
                    if (conversation.tags) {
                        selectedTags.value = conversation.tags;
                        console.log(`Loaded conversation with tags: ${conversation.tags.join(', ')}`);
                    } else {
                        selectedTags.value = [];
                    }
                    
                    // Set the include_untagged preference
                    if (conversation.include_untagged !== undefined) {
                        includeUntagged.value = conversation.include_untagged;
                        console.log(`Loaded conversation with include_untagged: ${conversation.include_untagged}`);
                    } else {
                        includeUntagged.value = true;  // Default to true for backward compatibility
                    }
                    
                    if (conversation.model) {
                        selectedModel.value = conversation.model;
                    }
                    
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
        };
        
        // Load a conversation (called from sidebar)
        const loadConversation = (conversationId) => {
            selectConversation(conversationId);
        };
        
        // Debounce timer for tag preference updates
        let tagUpdateTimeout = null;
        
        // Update conversation tag preferences with debouncing
        const updateConversationTagPreferences = async (conversationId) => {
            try {
                const updateData = {
                    tags: selectedTags.value,
                    include_untagged: includeUntagged.value
                };
                
                const response = await fetch(`/api/v1/conversations/${conversationId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(updateData)
                });
                
                if (response.ok) {
                    console.log('Updated conversation tag preferences');
                } else {
                    console.warn('Failed to update conversation tag preferences');
                }
            } catch (err) {
                console.warn('Error updating conversation tag preferences:', err);
            }
        };
        
        // Debounced version of the update function
        const debouncedUpdateConversationTagPreferences = (conversationId) => {
            if (tagUpdateTimeout) {
                clearTimeout(tagUpdateTimeout);
            }
            tagUpdateTimeout = setTimeout(() => {
                updateConversationTagPreferences(conversationId);
            }, 500); // Wait 500ms after the last change
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
                // Prepare request data for tag-based system
                const requestData = {
                    query: queryText.value,
                    history: conversationHistory.value,
                    tags: selectedTags.value,
                    include_untagged: includeUntagged.value
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
                        
                        // Update conversation with current tag preferences
                        // This ensures the conversation maintains the current tag selection state
                        updateConversationTagPreferences(currentConversationId.value);
                    }
                    
                    // Refresh sidebar conversations if function is available
                    if (window.refreshSidebarConversations) {
                        window.refreshSidebarConversations();
                    }
                    
                    // Refresh tags in case new ones were created
                    fetchTags();
                    
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
            collections,  // Deprecated but kept for compatibility
            selectedCollection,  // Deprecated
            availableTags,
            tagCounts,
            selectedTags,
            includeUntagged,
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
            isLoadingConversations,
            canSubmit,
            submitQuery,
            handleEnterKey,
            createCollection,  // Deprecated
            fetchTags,
            fetchConversations,
            selectConversation,
            startNewConversation,
            loadConversation,
            updateConversationTagPreferences,
            renameConversation,
            confirmDeleteConversation
        };
    }
};

// Create and mount the Vue app with error handling
try {
    console.log('Initializing Vue app...');
    
    const app = createApp({
        components: {
            'model-query-component': ModelQueryComponent
        }
    });
    
    const container = document.getElementById('model-query-container');
    if (container) {
        app.mount('#model-query-container');
        console.log('Vue app mounted successfully');
    } else {
        console.error('Vue container #model-query-container not found');
    }
    
} catch (error) {
    console.error('Error initializing Vue app:', error);
    
    // Fallback: Create basic functionality without Vue
    const fallbackContainer = document.getElementById('model-query-container');
    if (fallbackContainer) {
        fallbackContainer.innerHTML = `
            <div class="alert alert-warning" role="alert">
                <h4 class="alert-heading">Chat Interface Error</h4>
                <p>The chat interface failed to load. Please refresh the page or contact support.</p>
                <hr>
                <p class="mb-0">Error: ${error.message}</p>
            </div>
        `;
    }
}