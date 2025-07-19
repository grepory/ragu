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
const { createApp, ref, onMounted, computed } = Vue;

const ModelQueryComponent = {
    template: `
        <div class="model-query-component">
            <h3><i class="bi bi-chat-left-text me-2"></i>Query Model</h3>
            
            <!-- Collection selection -->
            <div class="mb-3 model-selection">
                <label for="collection-select" class="form-label">
                    <i class="bi bi-collection me-1"></i> Collection
                </label>
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
            
            <!-- Query input -->
            <div class="mb-3 query-input">
                <label for="query-textarea" class="form-label">
                    <i class="bi bi-question-circle me-1"></i> Query
                </label>
                <textarea
                    id="query-textarea"
                    class="form-control"
                    v-model="queryText"
                    placeholder="Enter your question here..."
                    rows="4"
                ></textarea>
                <div class="form-text">
                    Ask a question about the documents in the selected collection.
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
                {{ isLoading ? 'Processing...' : 'Submit Query' }}
            </button>
            
            <!-- Error message -->
            <div v-if="error" class="alert alert-danger mt-3">
                {{ error }}
            </div>
            
            <!-- Results -->
            <div v-if="results" class="mt-4">
                <h4><i class="bi bi-lightbulb me-2"></i>Results</h4>
                <div class="result-content p-3 border rounded bg-light">
                    <div class="mb-3">
                        <div class="fw-bold mb-2">
                            <i class="bi bi-robot me-1"></i> Answer:
                        </div>
                        <p class="mb-0">{{ results.answer }}</p>
                    </div>
                    
                    <div v-if="results.sources && results.sources.length > 0" class="mt-4">
                        <div class="fw-bold mb-2">
                            <i class="bi bi-journal-text me-1"></i> Sources:
                        </div>
                        <ul class="list-group">
                            <li v-for="(source, index) in results.sources" :key="index" class="list-group-item">
                                <div>{{ source.text }}</div>
                                <div class="result-source">
                                    <small>
                                        <i class="bi bi-file-earmark me-1"></i>
                                        {{ source.metadata.source || 'Unknown' }}
                                        <span v-if="source.metadata.page">
                                            <i class="bi bi-file-earmark-text ms-2 me-1"></i>
                                            Page: {{ source.metadata.page }}
                                        </span>
                                    </small>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
                
                <div class="mt-3 text-end">
                    <small class="text-muted">
                        <i class="bi bi-info-circle me-1"></i>
                        Model used: {{ selectedModel || 'Default model' }}
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
        
        // Computed properties
        const canSubmit = computed(() => {
            return selectedCollection.value && queryText.value.trim().length > 0;
        });
        
        // Fetch collections on component mount
        onMounted(async () => {
            await fetchCollections();
        });
        
        // Fetch collections from API
        const fetchCollections = async () => {
            try {
                const response = await fetch('/api/v1/collections/');
                if (response.ok) {
                    const data = await response.json();
                    collections.value = data.collections || [];
                    if (data.collections && data.collections.length > 0) {
                        selectedCollection.value = data.collections[0];
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
        
        // Submit query to API
        const submitQuery = async () => {
            if (!canSubmit.value) return;
            
            isLoading.value = true;
            error.value = '';
            results.value = null;
            
            try {
                // Prepare request data
                const requestData = {
                    collection_name: selectedCollection.value,
                    query: queryText.value
                };
                
                // Add model if selected
                if (selectedModel.value) {
                    requestData.model = selectedModel.value;
                }
                
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
                    
                    // Display results in the results container
                    const resultsContainer = document.getElementById('results-container');
                    if (resultsContainer) {
                        resultsContainer.innerHTML = `
                            <h4><i class="bi bi-lightbulb me-2"></i>Results</h4>
                            <div class="result-content p-3 border rounded bg-light">
                                <div class="mb-3">
                                    <div class="fw-bold mb-2">
                                        <i class="bi bi-robot me-1"></i> Answer:
                                    </div>
                                    <p class="mb-0">${data.answer}</p>
                                </div>
                                
                                ${data.sources && data.sources.length > 0 ? `
                                    <div class="mt-4">
                                        <div class="fw-bold mb-2">
                                            <i class="bi bi-journal-text me-1"></i> Sources:
                                        </div>
                                        <ul class="list-group">
                                            ${data.sources.map((source, index) => `
                                                <li class="list-group-item">
                                                    <div>${source.text}</div>
                                                    <div class="result-source">
                                                        <small>
                                                            <i class="bi bi-file-earmark me-1"></i>
                                                            ${source.metadata.source || 'Unknown'}
                                                            ${source.metadata.page ? `
                                                                <span>
                                                                    <i class="bi bi-file-earmark-text ms-2 me-1"></i>
                                                                    Page: ${source.metadata.page}
                                                                </span>
                                                            ` : ''}
                                                        </small>
                                                    </div>
                                                </li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                            </div>
                            
                            <div class="mt-3 text-end">
                                <small class="text-muted">
                                    <i class="bi bi-info-circle me-1"></i>
                                    Model used: ${selectedModel.value || 'Default model'}
                                </small>
                            </div>
                        `;
                    }
                } else {
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
            canSubmit,
            submitQuery
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