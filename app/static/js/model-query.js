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
<!--            <h3><i class="bi bi-chat-left-text me-2"></i>Chat with Documents</h3>-->
            
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
            canSubmit,
            submitQuery,
            handleEnterKey,
            createCollection
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