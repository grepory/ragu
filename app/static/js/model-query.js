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
            <h3><i class="bi bi-chat-left-text me-2"></i>Chat with Documents</h3>
            
            <!-- Collection selection -->
            <div class="mb-3 model-selection">
                <label for="collection-select" class="form-label">
                    <i class="bi bi-collection me-1"></i> Collection
                </label>
                <div class="input-group">
                    <select 
                        id="collection-select"
                        class="form-select"
                        v-model="selectedCollection"
                    >
                        <option value="">Select a collection</option>
                        <option v-for="collection in collections" :key="collection" :value="collection">
                            {{ collection }}
                        </option>
                    </select>
                    <button 
                        class="btn btn-outline-secondary" 
                        type="button"
                        @click="createCollection"
                    >
                        New
                    </button>
                </div>
                <div class="form-text" v-if="collections.length === 0">
                    No collections found. Please upload documents first.
                </div>
            </div>
            
            <!-- Model selection -->
            <div class="mb-3 model-selection">
                <label for="model-select" class="form-label">
                    <i class="bi bi-cpu me-1"></i> Model
                </label>
                <select 
                    id="model-select"
                    class="form-select"
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
            
            <!-- Conversation history -->
            <div v-if="conversationHistory.length > 0" class="mb-3 conversation-history">
                <h5><i class="bi bi-chat-dots me-2"></i>Conversation</h5>
                <div class="conversation-container p-3 border rounded bg-light" style="max-height: 300px; overflow-y: auto;">
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
            
            <!-- Query input -->
            <div class="mb-3 query-input">
                <label for="query-textarea" class="form-label">
                    <i class="bi bi-question-circle me-1"></i> Your Message
                </label>
                <textarea
                    id="query-textarea"
                    class="form-control"
                    v-model="queryText"
                    placeholder="Type your message here..."
                    rows="3"
                    @keydown.enter.prevent="handleEnterKey"
                ></textarea>
                <div class="form-text">
                    Ask a question about the documents in the selected collection. Press Enter to send.
                </div>
            </div>
            
            <!-- Submit button -->
            <button 
                class="btn btn-primary"
                @click="submitQuery"
                :disabled="isLoading || !canSubmit"
            >
                <i v-if="!isLoading" class="bi bi-send me-1"></i>
                <span v-if="isLoading" class="loading-spinner me-2"></span>
                {{ isLoading ? 'Processing...' : 'Send Message' }}
            </button>
            
            <!-- Error message -->
            <div v-if="error" class="alert alert-danger mt-3">
                {{ error }}
            </div>
            
            <!-- Model info -->
            <div class="mt-3 text-end">
                <small class="text-muted">
                    <i class="bi bi-info-circle me-1"></i>
                    Model used: {{ selectedModel || 'Default model' }}
                </small>
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
            
            // Add user message to conversation history
            const userMessage = {
                role: 'user',
                content: queryText.value
            };
            conversationHistory.value.push(userMessage);
            
            // Scroll to the bottom of the conversation container
            setTimeout(() => {
                const container = document.querySelector('.conversation-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }, 0);
            
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
                    }, 0);
                    
                    // Clear the results container (we're now using the conversation history)
                    const resultsContainer = document.getElementById('results-container');
                    if (resultsContainer) {
                        resultsContainer.innerHTML = '';
                    }
                } else {
                    // If there's an error, remove the user message from history
                    conversationHistory.value.pop();
                    
                    // Restore the query text
                    queryText.value = currentQuery;
                    
                    const errorData = await response.json();
                    error.value = errorData.detail || 'Failed to process query. Please try again.';
                }
            } catch (err) {
                // If there's an error, remove the user message from history
                conversationHistory.value.pop();
                
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