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
const { createApp, ref, onMounted, onUnmounted, computed, watch, nextTick } = Vue;

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
                                <div v-if="message.role === 'user'">{{ message.content }}</div>
                                <div v-else v-html="parseMarkdown(message.content)" class="markdown-content"></div>
                            </div>
                        </div>
                        
                        <!-- Typing indicator -->
                        <div v-if="isLoading && conversationHistory.length > 0" class="message mb-2 p-2 rounded assistant-message">
                            <div class="message-header mb-1">
                                <small class="fw-bold">
                                    <i class="bi bi-robot me-1"></i>
                                    Assistant
                                </small>
                            </div>
                            <div class="message-content">
                                <div class="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
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
                <!-- Inline selection controls above query input -->
                <div class="selection-controls mb-2 d-flex gap-2 align-items-center">
                    <!-- Model selection -->
                    <div class="model-selection-inline">
                        <select id="model-select" class="form-select form-select-sm" v-model="selectedModel" style="min-width: 180px;">
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
                    
                    <!-- Tag selection -->
                    <div class="tag-selection-inline">
                        <div class="dropdown" :class="{ show: tagDropdownOpen }">
                            <button 
                                type="button" 
                                class="btn btn-outline-secondary btn-sm dropdown-toggle"
                                @click="toggleTagDropdown"
                                style="min-width: 120px;"
                            >
                                <i class="bi bi-tags me-1"></i>
                                <span v-if="selectedTags.length === 0">All docs</span>
                                <span v-else>{{ selectedTags.length }} tag{{ selectedTags.length !== 1 ? 's' : '' }}</span>
                            </button>
                            
                            <!-- Dropdown menu -->
                            <div v-if="tagDropdownOpen" class="dropdown-menu show" style="min-width: 300px;">
                                <!-- Search Input -->
                                <div class="px-3 py-2">
                                    <input 
                                        ref="tagSearchInput"
                                        type="text" 
                                        class="form-control form-control-sm" 
                                        placeholder="Search tags..."
                                        v-model="tagSearchQuery"
                                        @input="onTagSearch"
                                        @mousedown="$event.stopPropagation()"
                                    >
                                </div>
                                
                                <div class="dropdown-divider"></div>
                                
                                <!-- Include untagged option -->
                                <div class="px-3 py-1">
                                    <div class="form-check form-check-sm">
                                        <input 
                                            class="form-check-input" 
                                            type="checkbox" 
                                            id="includeUntaggedCheck"
                                            v-model="includeUntagged"
                                            @mousedown="$event.stopPropagation()"
                                        >
                                        <label class="form-check-label small" for="includeUntaggedCheck">
                                            Include untagged documents
                                        </label>
                                    </div>
                                </div>
                                
                                <div v-if="selectedTags.length > 0 || availableTagsForSelection.length > 0" class="dropdown-divider"></div>
                                
                                <!-- Selected tags -->
                                <div v-if="selectedTags.length > 0" class="px-3 py-1">
                                    <div class="small text-muted mb-1">Selected:</div>
                                    <div class="d-flex flex-wrap gap-1">
                                        <span 
                                            v-for="tag in selectedTags" 
                                            :key="'selected-' + tag"
                                            class="badge bg-primary d-flex align-items-center gap-1"
                                            style="cursor: pointer;"
                                            @click="removeTag(tag)"
                                            @mousedown="$event.stopPropagation()"
                                            title="Click to remove"
                                        >
                                            {{ tag }}
                                            <i class="bi bi-x"></i>
                                        </span>
                                    </div>
                                </div>
                                
                                <!-- Available tags -->
                                <div v-if="availableTagsForSelection.length > 0" class="px-3 py-1">
                                    <div v-if="selectedTags.length > 0" class="small text-muted mb-1">Available:</div>
                                    <div class="tag-list" style="max-height: 200px; overflow-y: auto;">
                                        <button
                                            v-for="tagResult in availableTagsForSelection.slice(0, 20)" 
                                            :key="'available-' + tagResult.item"
                                            type="button"
                                            class="btn btn-sm btn-outline-secondary me-1 mb-1"
                                            @click="addTag(tagResult.item)"
                                            @mousedown="$event.stopPropagation()"
                                        >
                                            {{ tagResult.item }} <small class="text-muted">({{ tagCounts[tagResult.item] || 0 }})</small>
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- No tags message -->
                                <div v-if="availableTags.length === 0" class="px-3 py-2 text-muted small">
                                    No tags found. Upload documents with tags first.
                                </div>
                                
                                <!-- No results -->
                                <div v-if="tagSearchQuery && availableTagsForSelection.length === 0 && availableTags.length > 0" class="px-3 py-2 text-muted small">
                                    No tags found matching "{{ tagSearchQuery }}"
                                </div>
                            </div>
                        </div>
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
        const tagSearchQuery = ref('');
        const tagDropdownOpen = ref(false);
        const tagSearchInput = ref(null);
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
        
        // Initialize Fuse.js for fuzzy search
        let fuse = null;
        
        // Available tags for selection with fuzzy search
        const availableTagsForSelection = computed(() => {
            const unselectedTags = availableTags.value.filter(tag => !selectedTags.value.includes(tag));
            
            if (!tagSearchQuery.value.trim()) {
                // No search query - return all unselected tags sorted by count
                return unselectedTags
                    .sort((a, b) => {
                        const countDiff = (tagCounts.value[b] || 0) - (tagCounts.value[a] || 0);
                        if (countDiff !== 0) return countDiff;
                        return a.localeCompare(b);
                    })
                    .map(tag => ({ item: tag }));
            }
            
            // Use Fuse.js for fuzzy search
            try {
                if (!fuse || !fuse.list || fuse.list.length !== unselectedTags.length) {
                    console.log('Initializing Fuse.js with', unselectedTags.length, 'tags');
                    fuse = new Fuse(unselectedTags, {
                        threshold: 0.4, // More lenient matching
                        distance: 100,
                        minMatchCharLength: 1,
                        includeScore: true
                    });
                }
                
                const searchResults = fuse.search(tagSearchQuery.value);
                console.log('Fuse search for "' + tagSearchQuery.value + '" found', searchResults.length, 'results');
                
                return searchResults.map(result => ({ 
                    item: result.item,
                    score: result.score 
                }));
            } catch (error) {
                console.error('Fuse.js error:', error);
                // Fallback to simple string matching
                const query = tagSearchQuery.value.toLowerCase();
                return unselectedTags
                    .filter(tag => tag.toLowerCase().includes(query))
                    .map(tag => ({ item: tag }));
            }
        });
        
        // Handle click outside to close dropdown
        const handleClickOutside = (event) => {
            if (!tagDropdownOpen.value) return;
            
            const dropdown = document.querySelector('.tag-selection-inline');
            if (dropdown && !dropdown.contains(event.target)) {
                tagDropdownOpen.value = false;
            }
        };
        
        // Fetch tags and load saved preferences on component mount
        onMounted(async () => {
            await fetchTags();
            
            // Add click outside listener
            document.addEventListener('click', handleClickOutside);
            
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
            
            // Listen for when the user switches to chat interface
            document.addEventListener('tabSwitch', (event) => {
                if (event.detail && event.detail.tab === 'chat') {
                    fetchTags(); // Refresh tags when switching to chat
                }
            });
            
            // Listen for window focus events (user returning from another tab/window)
            window.addEventListener('focus', () => {
                fetchTags(); // Refresh tags when user returns to the window
            });
            
            // Listen for visibility change events
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) {
                    fetchTags(); // Refresh tags when page becomes visible
                }
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
        
        // Tag dropdown methods
        const toggleTagDropdown = () => {
            tagDropdownOpen.value = !tagDropdownOpen.value;
            if (tagDropdownOpen.value) {
                // Check dropdown positioning and focus search input
                nextTick(() => {
                    // Focus the search input
                    if (tagSearchInput.value) {
                        tagSearchInput.value.focus();
                    }
                    
                    // Check if dropdown would extend beyond viewport for inline Bootstrap dropdown
                    const dropdownContainer = document.querySelector('.tag-selection-inline .dropdown');
                    const dropdownMenu = document.querySelector('.tag-selection-inline .dropdown-menu');
                    if (dropdownContainer && dropdownMenu) {
                        const rect = dropdownContainer.getBoundingClientRect();
                        const dropdownHeight = 400; // max height
                        const spaceBelow = window.innerHeight - rect.bottom;
                        const spaceAbove = rect.top;
                        
                        if (spaceBelow < dropdownHeight && spaceAbove > spaceBelow) {
                            dropdownContainer.classList.add('dropup');
                        } else {
                            dropdownContainer.classList.remove('dropup');
                        }
                    }
                });
            }
        };
        
        const handleTagDropdownBlur = (event) => {
            // Small delay to allow clicks inside dropdown to register
            setTimeout(() => {
                if (!tagDropdownOpen.value) return;
                
                // Check if focus moved to an element outside the dropdown
                const activeElement = document.activeElement;
                const dropdownContainer = event.currentTarget.closest('.tag-selection-inline');
                
                if (!dropdownContainer || !dropdownContainer.contains(activeElement)) {
                    tagDropdownOpen.value = false;
                }
            }, 150);
        };
        
        const onTagSearch = (event) => {
            // Force reactivity update for the search query
            const newValue = event.target.value;
            tagSearchQuery.value = newValue;
            console.log('Search query updated to:', newValue);
        };
        
        const addTag = (tag) => {
            if (!selectedTags.value.includes(tag)) {
                selectedTags.value.push(tag);
                tagSearchQuery.value = ''; // Clear search after selection
            }
        };
        
        const removeTag = (tag) => {
            const index = selectedTags.value.indexOf(tag);
            if (index > -1) {
                selectedTags.value.splice(index, 1);
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
                    
                    // Refresh tags first to get any newly added tags
                    await fetchTags();
                    
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
        const startNewConversation = async () => {
            // Clear the current conversation
            currentConversationId.value = null;
            conversationHistory.value = [];
            
            // Refresh tags to get any newly added tags
            await fetchTags();
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
            
            const currentQuery = queryText.value;
            
            // Add user message to conversation history immediately
            conversationHistory.value.push({
                role: 'user',
                content: currentQuery
            });
            
            // Clear the query text immediately
            queryText.value = '';
            
            // Set loading state
            isLoading.value = true;
            error.value = '';
            
            // Scroll to the bottom of the conversation container
            setTimeout(() => {
                const container = document.querySelector('.conversation-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }, 50);
            
            try {
                // Prepare request data for tag-based system
                // Use the conversation history minus the user message we just added for the request
                const requestData = {
                    query: currentQuery,
                    history: conversationHistory.value.slice(0, -1), // Exclude the user message we just added
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
                    // Remove the user message we added and restore the query text
                    conversationHistory.value.pop();
                    queryText.value = currentQuery;
                    
                    const errorData = await response.json();
                    error.value = errorData.detail || 'Failed to process query. Please try again.';
                }
            } catch (err) {
                // Remove the user message we added and restore the query text
                conversationHistory.value.pop();
                queryText.value = currentQuery;
                
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
        
        // Parse markdown content
        const parseMarkdown = (content) => {
            if (!content) return '';
            
            // Configure marked.js for security and formatting
            marked.setOptions({
                breaks: true, // Convert line breaks to <br>
                gfm: true, // GitHub flavored markdown
                sanitize: false, // We'll handle XSS protection through DOMPurify if needed
                smartLists: true,
                smartypants: false
            });
            
            return marked.parse(content);
        };
        
        // Cleanup event listener
        onUnmounted(() => {
            document.removeEventListener('click', handleClickOutside);
        });
        
        return {
            collections,  // Deprecated but kept for compatibility
            selectedCollection,  // Deprecated
            availableTags,
            tagCounts,
            selectedTags,
            includeUntagged,
            tagSearchQuery,
            tagDropdownOpen,
            tagSearchInput,
            availableTagsForSelection,
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
            toggleTagDropdown,
            handleTagDropdownBlur,
            onTagSearch,
            addTag,
            removeTag,
            createCollection,  // Deprecated
            fetchTags,
            fetchConversations,
            selectConversation,
            startNewConversation,
            loadConversation,
            updateConversationTagPreferences,
            renameConversation,
            confirmDeleteConversation,
            parseMarkdown
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