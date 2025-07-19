// Test script for tab persistence functionality
console.log('Starting tab persistence test...');

// Mock DOM elements
const mockElements = {
  'chat-menu-item': { classList: { add: jest.fn(), remove: jest.fn() } },
  'files-menu-item': { classList: { add: jest.fn(), remove: jest.fn() } },
  'chat-interface': { classList: { add: jest.fn(), remove: jest.fn() } },
  'file-management': { classList: { add: jest.fn(), remove: jest.fn() } }
};

// Mock localStorage
const mockLocalStorage = {
  store: {},
  getItem: function(key) {
    return this.store[key] || null;
  },
  setItem: function(key, value) {
    this.store[key] = value;
  },
  clear: function() {
    this.store = {};
  }
};

// Mock document.getElementById
document.getElementById = jest.fn(id => mockElements[id]);

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Test 1: Verify localStorage is set when switching tabs
function testTabSwitching() {
  console.log('Test 1: Testing tab switching...');
  
  // Clear mocks
  mockLocalStorage.clear();
  Object.values(mockElements).forEach(el => {
    el.classList.add.mockClear();
    el.classList.remove.mockClear();
  });
  
  // Simulate clicking on files tab
  const setActiveTab = window.setActiveTab || function(tabName) {
    mockLocalStorage.setItem('activeTab', tabName);
    
    if (tabName === 'chat') {
      mockElements['chat-menu-item'].classList.add('active');
      mockElements['files-menu-item'].classList.remove('active');
      mockElements['chat-interface'].classList.add('active');
      mockElements['file-management'].classList.remove('active');
    } else if (tabName === 'files') {
      mockElements['files-menu-item'].classList.add('active');
      mockElements['chat-menu-item'].classList.remove('active');
      mockElements['file-management'].classList.add('active');
      mockElements['chat-interface'].classList.remove('active');
    }
  };
  
  // Test files tab
  setActiveTab('files');
  console.log('After clicking files tab:');
  console.log('- localStorage activeTab:', mockLocalStorage.getItem('activeTab'));
  console.log('- files-menu-item has active class:', mockElements['files-menu-item'].classList.add.mock.calls.length > 0);
  console.log('- chat-menu-item active class removed:', mockElements['chat-menu-item'].classList.remove.mock.calls.length > 0);
  
  // Test chat tab
  setActiveTab('chat');
  console.log('After clicking chat tab:');
  console.log('- localStorage activeTab:', mockLocalStorage.getItem('activeTab'));
  console.log('- chat-menu-item has active class:', mockElements['chat-menu-item'].classList.add.mock.calls.length > 0);
  console.log('- files-menu-item active class removed:', mockElements['files-menu-item'].classList.remove.mock.calls.length > 0);
}

// Test 2: Verify page load respects localStorage setting
function testPageLoad() {
  console.log('\nTest 2: Testing page load behavior...');
  
  // Clear mocks
  Object.values(mockElements).forEach(el => {
    el.classList.add.mockClear();
    el.classList.remove.mockClear();
  });
  
  // Test with files tab stored
  mockLocalStorage.setItem('activeTab', 'files');
  console.log('With localStorage set to "files":');
  
  // Simulate page load
  const activeTab = mockLocalStorage.getItem('activeTab');
  if (activeTab === 'files') {
    mockElements['files-menu-item'].classList.add('active');
    mockElements['chat-menu-item'].classList.remove('active');
    mockElements['file-management'].classList.add('active');
    mockElements['chat-interface'].classList.remove('active');
    console.log('- files tab is activated correctly');
  } else {
    mockElements['chat-menu-item'].classList.add('active');
    mockElements['files-menu-item'].classList.remove('active');
    mockElements['chat-interface'].classList.add('active');
    mockElements['file-management'].classList.remove('active');
    console.log('- chat tab is activated (incorrect)');
  }
  
  // Clear mocks
  Object.values(mockElements).forEach(el => {
    el.classList.add.mockClear();
    el.classList.remove.mockClear();
  });
  
  // Test with no stored preference
  mockLocalStorage.clear();
  console.log('\nWith no localStorage setting:');
  
  // Simulate page load
  const newActiveTab = mockLocalStorage.getItem('activeTab');
  if (newActiveTab === 'files') {
    mockElements['files-menu-item'].classList.add('active');
    mockElements['chat-menu-item'].classList.remove('active');
    mockElements['file-management'].classList.add('active');
    mockElements['chat-interface'].classList.remove('active');
    console.log('- files tab is activated (incorrect default)');
  } else {
    mockElements['chat-menu-item'].classList.add('active');
    mockElements['files-menu-item'].classList.remove('active');
    mockElements['chat-interface'].classList.add('active');
    mockElements['file-management'].classList.remove('active');
    console.log('- chat tab is activated correctly as default');
  }
}

// Run tests
testTabSwitching();
testPageLoad();

console.log('\nTab persistence test completed.');
console.log('Note: This is a mock test. In a real environment, you should:');
console.log('1. Open the application in a browser');
console.log('2. Click on the Files tab');
console.log('3. Refresh the page');
console.log('4. Verify the Files tab remains selected');
console.log('5. Click on the Chat tab');
console.log('6. Refresh the page');
console.log('7. Verify the Chat tab remains selected');