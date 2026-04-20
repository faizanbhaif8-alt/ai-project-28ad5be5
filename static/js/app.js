// static/js/app.js
// BotManager V2.5 - Enhanced AI Project Generator with Multi-Bot Support
// Main application JavaScript file

// Import dependencies (assuming they are loaded via script tags in HTML)
// Chart.js, FileSaver.js, etc. are loaded externally

// Global state management
const AppState = {
    currentBot: null,
    bots: [],
    projects: [],
    activeTab: 'dashboard',
    isLoading: false,
    apiKeys: {
        openai: '',
        anthropic: '',
        gemini: '',
        groq: '',
        replicate: '',
        huggingface: '',
        cohere: '',
        together: ''
    },
    settings: {
        autoSave: true,
        theme: 'dark',
        notifications: true
    }
};

// DOM Elements cache
const DOM = {
    // Tabs
    dashboardTab: document.getElementById('dashboard-tab'),
    botManagerTab: document.getElementById('bot-manager-tab'),
    projectGeneratorTab: document.getElementById('project-generator-tab'),
    apiConfigTab: document.getElementById('api-config-tab'),
    settingsTab: document.getElementById('settings-tab'),
    
    // Content sections
    dashboardContent: document.getElementById('dashboard-content'),
    botManagerContent: document.getElementById('bot-manager-content'),
    projectGeneratorContent: document.getElementById('project-generator-content'),
    apiConfigContent: document.getElementById('api-config-content'),
    settingsContent: document.getElementById('settings-content'),
    
    // Dashboard elements
    totalBotsEl: document.getElementById('total-bots'),
    totalProjectsEl: document.getElementById('total-projects'),
    apiUsageEl: document.getElementById('api-usage'),
    recentActivityEl: document.getElementById('recent-activity'),
    usageChart: document.getElementById('usage-chart'),
    
    // Bot Manager elements
    botList: document.getElementById('bot-list'),
    createBotBtn: document.getElementById('create-bot-btn'),
    botModal: document.getElementById('bot-modal'),
    botForm: document.getElementById('bot-form'),
    botNameInput: document.getElementById('bot-name'),
    botTypeSelect: document.getElementById('bot-type'),
    botDescriptionInput: document.getElementById('bot-description'),
    botConfigTextarea: document.getElementById('bot-config'),
    
    // Project Generator elements
    projectTypeSelect: document.getElementById('project-type'),
    projectNameInput: document.getElementById('project-name'),
    projectDescriptionInput: document.getElementById('project-description'),
    projectComplexitySelect: document.getElementById('project-complexity'),
    generateProjectBtn: document.getElementById('generate-project-btn'),
    projectOutput: document.getElementById('project-output'),
    downloadProjectBtn: document.getElementById('download-project-btn'),
    
    // API Config elements
    apiForm: document.getElementById('api-form'),
    saveApiBtn: document.getElementById('save-api-btn'),
    testApiBtn: document.getElementById('test-api-btn'),
    
    // Settings elements
    settingsForm: document.getElementById('settings-form'),
    autoSaveToggle: document.getElementById('auto-save-toggle'),
    themeSelect: document.getElementById('theme-select'),
    notificationsToggle: document.getElementById('notifications-toggle'),
    
    // Common elements
    loadingOverlay: document.getElementById('loading-overlay'),
    notificationContainer: document.getElementById('notification-container')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('BotManager V2.5 Initializing...');
    
    // Load saved state from localStorage
    loadAppState();
    
    // Initialize UI components
    initializeTabs();
    initializeBotManager();
    initializeProjectGenerator();
    initializeAPIConfig();
    initializeSettings();
    
    // Load initial data
    loadDashboardData();
    
    // Set up auto-save if enabled
    if (AppState.settings.autoSave) {
        setupAutoSave();
    }
    
    // Apply theme
    applyTheme(AppState.settings.theme);
    
    console.log('BotManager V2.5 Initialized Successfully');
});

// Load application state from localStorage
function loadAppState() {
    try {
        const savedState = localStorage.getItem('botmanager_state');
        if (savedState) {
            const parsed = JSON.parse(savedState);
            Object.assign(AppState, parsed);
            console.log('App state loaded from localStorage');
        }
        
        // Load API keys from localStorage (separate for security)
        loadAPIKeys();
        
        // Load bots and projects
        loadBots();
        loadProjects();
    } catch (error) {
        console.error('Error loading app state:', error);
        showNotification('Error loading saved data', 'error');
    }
}

// Save application state to localStorage
function saveAppState() {
    try {
        // Don't save API keys to general state (they're saved separately)
        const stateToSave = {
            ...AppState,
            apiKeys: {} // Clear API keys from general state
        };
        
        localStorage.setItem('botmanager_state', JSON.stringify(stateToSave));
        console.log('App state saved to localStorage');
    } catch (error) {
        console.error('Error saving app state:', error);
    }
}

// Load API keys from localStorage
function loadAPIKeys() {
    try {
        const savedKeys = localStorage.getItem('botmanager_api_keys');
        if (savedKeys) {
            AppState.apiKeys = JSON.parse(savedKeys);
            console.log('API keys loaded from localStorage');
        }
    } catch (error) {
        console.error('Error loading API keys:', error);
    }
}

// Save API keys to localStorage
function saveAPIKeys() {
    try {
        localStorage.setItem('botmanager_api_keys', JSON.stringify(AppState.apiKeys));
        console.log('API keys saved to localStorage');
    } catch (error) {
        console.error('Error saving API keys:', error);
    }
}

// Load bots from localStorage
function loadBots() {
    try {
        const savedBots = localStorage.getItem('botmanager_bots');
        if (savedBots) {
            AppState.bots = JSON.parse(savedBots);
            console.log(`Loaded ${AppState.bots.length} bots from localStorage`);
        }
    } catch (error) {
        console.error('Error loading bots:', error);
    }
}

// Save bots to localStorage
function saveBots() {
    try {
        localStorage.setItem('botmanager_bots', JSON.stringify(AppState.bots));
        console.log(`Saved ${AppState.bots.length} bots to localStorage`);
    } catch (error) {
        console.error('Error saving bots:', error);
    }
}

// Load projects from localStorage
function loadProjects() {
    try {
        const savedProjects = localStorage.getItem('botmanager_projects');
        if (savedProjects) {
            AppState.projects = JSON.parse(savedProjects);
            console.log(`Loaded ${AppState.projects.length} projects from localStorage`);
        }
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

// Save projects to localStorage
function saveProjects() {
    try {
        localStorage.setItem('botmanager_projects', JSON.stringify(AppState.projects));
        console.log(`Saved ${AppState.projects.length} projects to localStorage`);
    } catch (error) {
        console.error('Error saving projects:', error);
    }
}

// Initialize tab navigation
function initializeTabs() {
    const tabs = [
        { element: DOM.dashboardTab, content: DOM.dashboardContent, id: 'dashboard' },
        { element: DOM.botManagerTab, content: DOM.botManagerContent, id: 'bot-manager' },
        { element: DOM.projectGeneratorTab, content: DOM.projectGeneratorContent, id: 'project-generator' },
        { element: DOM.apiConfigTab, content: DOM.apiConfigContent, id: 'api-config' },
        { element: DOM.settingsTab, content: DOM.settingsContent, id: 'settings' }
    ];
    
    tabs.forEach(tab => {
        tab.element.addEventListener('click', () => {
            // Update active tab state
            AppState.activeTab = tab.id;
            
            // Update UI
            tabs.forEach(t => {
                t.element.classList.remove('active');
                t.content.classList.remove('active');
            });
            
            tab.element.classList.add('active');
            tab.content.classList.add('active');
            
            // Load data for the tab if needed
            if (tab.id === 'dashboard') {
                loadDashboardData();
            } else if (tab.id === 'bot-manager') {
                refreshBotList();
            }
            
            // Save state
            if (AppState.settings.autoSave) {
                saveAppState();
            }
        });
    });
}

// Initialize bot manager functionality
function initializeBotManager() {
    // Create bot button
    DOM.createBotBtn.addEventListener('click', () => {
        openBotModal();
    });
    
    // Bot form submission
    DOM.botForm.addEventListener('submit', (e) => {
        e.preventDefault();
        saveBot();
    });
    
    // Close modal on outside click
    DOM.botModal.addEventListener('click', (e) => {
        if (e.target === DOM.botModal) {
            closeBotModal();
        }
    });
    
    // Close modal on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && DOM.botModal.classList.contains('active')) {
            closeBotModal();
        }
    });
}

// Initialize project generator functionality
function initializeProjectGenerator() {
    DOM.generateProjectBtn.addEventListener('click', generateProject);
    DOM.downloadProjectBtn.addEventListener('click', downloadProject);
    
    // Update UI based on project type selection
    DOM.projectTypeSelect.addEventListener('change', updateProjectUI);
}

// Initialize API configuration functionality
function initializeAPIConfig() {
    // Load API keys into form
    populateAPIForm();
    
    // Save API keys
    DOM.saveApiBtn.addEventListener('click', saveAPIKeysToStorage);
    
    // Test API connections
    DOM.testApiBtn.addEventListener('click', testAPIConnections);
    
    // Form submission
    DOM.apiForm.addEventListener('submit', (e) => {
        e.preventDefault();
        saveAPIKeysToStorage();
    });
}

// Initialize settings functionality
function initializeSettings() {
    // Load settings into form
    populateSettingsForm();
    
    // Form submission
    DOM.settingsForm.addEventListener('submit', (e) => {
        e.preventDefault();
        saveSettings();
    });
    
    // Real-time updates for toggles
    DOM.autoSaveToggle.addEventListener('change', (e) => {
        AppState.settings.autoSave = e.target.checked;
        if (AppState.settings.autoSave) {
            setupAutoSave();
        }
        saveSettings();
    });
    
    DOM.themeSelect.addEventListener('change', (e) => {
        AppState.settings.theme = e.target.value;
        applyTheme(e.target.value);
        saveSettings();
    });
    
    DOM.notificationsToggle.addEventListener('change', (e) => {
        AppState.settings.notifications = e.target.checked;
        saveSettings();
    });
}

// Load dashboard data
function loadDashboardData() {
    // Update counters
    DOM.totalBotsEl.textContent = AppState.bots.length;
    DOM.totalProjectsEl.textContent = AppState.projects.length;
    
    // Calculate API usage (mock data for now)
    const apiUsage = calculateAPIUsage();
    DOM.apiUsageEl.textContent = `${apiUsage.totalCalls} calls ($${apiUsage.totalCost.toFixed(2)})`;
    
    // Load recent activity
    loadRecentActivity();
    
    // Initialize chart if it exists
    if (DOM.usageChart) {
        initializeUsageChart();
    }
}

// Calculate API usage statistics
function calculateAPIUsage() {
    // Mock calculation - in a real app, this would come from backend
    const totalCalls = AppState.projects.length * 3 + AppState.bots.length * 2;
    const totalCost = totalCalls * 0.002; // Mock cost per call
    
    return {
        totalCalls,
        totalCost,
        byService: {
            openai: { calls: Math.floor(totalCalls * 0.4), cost: totalCost * 0.4 },
            anthropic: { calls: Math.floor(totalCalls * 0.3), cost: totalCost * 0.3 },
            gemini: { calls: Math.floor(totalCalls * 0.2), cost: totalCost * 0.2 },
            others: { calls: Math.floor(totalCalls * 0.1), cost: totalCost * 0.1 }
        }
    };
}

// Load recent activity
function loadRecentActivity() {
    if (!DOM.recentActivityEl) return;
    
    // Combine bot and project activities
    const activities = [
        ...AppState.bots.slice(-3).map(bot => ({
            type: 'bot',
            name: bot.name,
            action: 'created',
            time: bot.createdAt || new Date().toISOString()
        })),
        ...AppState.projects.slice(-3).map(project => ({
            type: 'project',
            name: project.name,
            action: 'generated',
            time: project.createdAt || new Date().toISOString()
        }))
    ].sort((a, b) => new Date(b.time) - new Date(a.time)).slice(0, 5);
    
    DOM.recentActivityEl.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <span class="activity-icon">${activity.type === 'bot' ? '🤖' : '🚀'}</span>
            <div class="activity-details">
                <span class="activity-text">${activity.name} ${activity.action}</span>
                <span class="activity-time">${formatTime(activity.time)}</span>
            </div>
        </div>
    `).join('');
}

// Initialize usage chart
function initializeUsageChart() {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded');
        return;
    }
    
    const usageData = calculateAPIUsage();
    const ctx = DOM.usageChart.getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['OpenAI', 'Anthropic', 'Gemini', 'Others'],
            datasets: [{
                data: [
                    usageData.byService.openai.calls,
                    usageData.byService.anthropic.calls,
                    usageData.byService.gemini.calls,
                    usageData.byService.others.calls
                ],
                backgroundColor: [
                    '#10B981',
                    '#3B82F6',
                    '#8B5CF6',
                    '#6B7280'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const percentage = Math.round((value / usageData.totalCalls) * 100);
                            return `${label}: ${value} calls (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Open bot creation modal
function openBotModal(bot = null) {
    DOM.botModal.classList.add('active');
    
    if (bot) {
        // Edit existing bot
        AppState.currentBot = bot;
        DOM.botNameInput.value = bot.name;
        DOM.botTypeSelect.value = bot.type;
        DOM.botDescriptionInput.value = bot.description;
        DOM.botConfigTextarea.value = JSON.stringify(bot.config, null, 2);
        document.querySelector('#bot-modal .modal-title').textContent = 'Edit Bot';
    } else {
        // Create new bot
        AppState.currentBot = null;
        DOM.botForm.reset();
        DOM.botConfigTextarea.value = JSON.stringify({
            model: 'gpt-4',
            temperature: 0.7,
            maxTokens: 1000
        }, null, 2);
        document.querySelector('#bot-modal .modal-title').textContent = 'Create New Bot';
    }
}

// Close bot modal
function closeBotModal() {
    DOM.botModal.classList.remove('active');
    AppState.currentBot = null;
}

// Save bot (create or update)
function saveBot() {
    const botData = {
        id: AppState.currentBot ? AppState.currentBot.id : generateId(),
        name: DOM.botNameInput.value.trim(),
        type: DOM.botTypeSelect.value,
        description: DOM.botDescriptionInput.value.trim(),
        config: parseBotConfig(DOM.botConfigTextarea.value),
        createdAt: AppState.currentBot ? AppState.currentBot.createdAt : new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: 'active'
    };
    
    // Validate
    if (!botData.name) {
        showNotification('Bot name is required', 'error');
        return;
    }
    
    try {
        if (AppState.currentBot) {
            // Update existing bot
            const index = AppState.bots.findIndex(b => b.id === AppState.currentBot.id);
            if (index !== -1) {
                AppState.bots[index] = botData;
                showNotification('Bot updated successfully', 'success');
            }
        } else {
            // Add new bot
            AppState.bots.push(botData);
            showNotification('Bot created successfully', 'success');
        }
        
        // Save to localStorage
        saveBots();
        
        // Refresh UI
        refreshBotList();
        
        // Close modal
        closeBotModal();
        
        // Update dashboard if visible
        if (AppState.activeTab === 'dashboard') {
            loadDashboardData();
        }
    } catch (error) {
        console.error('Error saving bot:', error);
        showNotification('Error saving bot', 'error');
    }
}

// Parse bot configuration from JSON
function parseBotConfig(configText) {
    try {
        return JSON.parse(configText);
    } catch (error) {
        console.error('Error parsing bot config:', error);
        showNotification('Invalid JSON configuration', 'error');
        return {};
    }
}

// Refresh bot list UI
function refreshBotList() {
    if (!DOM.botList) return;
    
    DOM.botList.innerHTML = AppState.bots.map(bot => `
        <div class="bot-card" data-bot-id="${bot.id}">
            <div class="bot-header">
                <span class="bot-icon">🤖</span>
                <h3 class="bot-name">${bot.name}</h3>
                <span class="bot-status ${bot.status}">${bot.status}</span>
            </div>
            <div class="bot-body">
                <p class="bot-description">${bot.description || 'No description'}</p>
                <div class="bot-meta">
                    <span class="bot-type">${bot.type}</span>
                    <span class="bot-updated">Updated: ${formatTime(bot.updatedAt)}</span>
                </div>
            </div>
            <div class="bot-actions">
                <button class="btn btn-sm btn-edit" onclick="editBot('${bot.id}')">Edit</button>
                <button class="btn btn-sm btn-delete" onclick="deleteBot('${bot.id}')">Delete</button>
                <button class="btn btn-sm btn-activate" onclick="toggleBotStatus('${bot.id}')">
                    ${bot.status === 'active' ? 'Deactivate' : 'Activate'}
                </button>
            </div>
        </div>
    `).join('');
    
    // Show empty state if no bots
    if (AppState.bots.length === 0) {
        DOM.botList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🤖</div>
                <h3>No Bots Created Yet</h3>
                <p>Create your first bot to get started with AI automation</p>
                <button class="btn btn-primary" onclick="openBotModal()">Create First Bot</button>
            </div>
        `;
    }
}

// Edit bot (called from inline onclick)
window.editBot = function(botId) {
    const bot = AppState.bots.find(b => b.id === botId);
    if (bot) {
        openBotModal(bot);
    }
};

// Delete bot (called from inline onclick)
window.deleteBot = function(botId) {
    if (confirm('Are you sure you want to delete this bot?')) {
        AppState.bots = AppState.bots.filter(b => b.id !== botId);
        saveBots();
        refreshBotList();
        
        if (AppState.activeTab === 'dashboard') {
            loadDashboardData();
        }
        
        showNotification('Bot deleted successfully', 'success');
    }
};

// Toggle bot status (called from inline onclick)
window.toggleBotStatus = function(botId) {
    const bot = AppState.bots.find(b => b.id === botId);
    if (bot) {
        bot.status = bot.status === 'active' ? 'inactive' : 'active';
        bot.updatedAt = new Date().toISOString();
        saveBots();
        refreshBotList();
        showNotification(`Bot ${bot.status === 'active' ? 'activated' : 'deactivated'}`, 'success');
    }
};

// Update project UI based on selected type
function updateProjectUI() {
    const projectType = DOM.projectTypeSelect.value;
    const complexitySelect = DOM.projectComplexitySelect;
    
    // Update complexity options based on project type
    complexitySelect.innerHTML = '';
    
    const complexities = {
        'web-app': ['Beginner', 'Intermediate', 'Advanced', 'Expert'],
        'mobile-app': ['Beginner', 'Intermediate', 'Advanced'],
        'api-service': ['Intermediate', 'Advanced', 'Expert'],
        'automation-bot': ['Beginner', 'Intermediate', 'Advanced'],
        'data-analysis': ['Intermediate', 'Advanced', 'Expert'],
        'machine-learning': ['Advanced', 'Expert']
    };
    
    const options = complexities[projectType] || ['Beginner', 'Intermediate', 'Advanced'];
    
    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option.toLowerCase();
        opt.textContent = option;
        complexitySelect.appendChild(opt);
    });
}

// Generate project using AI
async function generateProject() {
    const projectData = {
        name: DOM.projectNameInput.value.trim(),
        description: DOM.projectDescriptionInput.value.trim(),
        type: DOM.projectTypeSelect.value,
        complexity: DOM.projectComplexitySelect.value,
        createdAt: new Date().toISOString()
    };
    
    // Validate
    if (!projectData.name || !projectData.description) {
        showNotification('Project name and description are required', 'error');
        return;
    }
    
    // Check if we have API keys
    if (!hasAPIKeys()) {
        showNotification('Please configure API keys first', 'error');
        switchToTab('api-config');
        return;
    }
    
    showLoading(true);
    
    try {
        // Generate project using AI (mock implementation)
        const generatedProject = await mockAIGenerateProject(projectData);
        
        // Save project
        generatedProject.id = generateId();
        AppState.projects.push(generatedProject);
        saveProjects();
        
        // Display generated project
        displayGeneratedProject(generatedProject);
        
        // Update dashboard
        if (AppState.activeTab === 'dashboard') {
            loadDashboardData();
        }
        
        showNotification('Project generated successfully!', 'success');
    } catch (error) {
        console.error('Error generating project:', error);
        showNotification('Error generating project: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Mock AI project generation (replace with actual API calls)
async function mockAIGenerateProject(projectData) {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Generate mock project structure based on type and complexity
    const templates = {
        'web-app': {
            files: [
                { name: 'index.html', content: generateHTMLTemplate(projectData) },
                { name: 'styles.css', content: generateCSSTemplate() },
                { name: 'app.js', content: generateJSTemplate() },
                { name: 'README.md', content: generateReadme(projectData) }
            ],
            dependencies: ['express', 'react', 'vue', 'tailwindcss'],
            instructions: 'Run npm install followed by npm start'
        },
        'mobile-app': {
            files: [
                { name: 'App.js', content: generateReactNativeApp(projectData) },
                { name: 'package.json', content: generatePackageJSON(projectData) },
                { name: 'README.md', content: generateReadme(projectData) }
            ],
            dependencies: ['react-native', 'expo', 'react-navigation'],
            instructions: 'Follow React Native setup instructions'
        },
        'api-service': {
            files: [
                { name: 'server.js', content: generateAPIServer(projectData) },
                { name: 'package.json', content: generatePackageJSON(projectData) },
                { name: '.env.example', content: 'API_KEY=your_key_here' },
                { name: 'README.md', content: generateReadme(projectData) }
            ],
            dependencies: ['express', 'cors', 'dotenv', 'axios'],
            instructions: 'Set up environment variables and run node server.js'
        }
    };
    
    const template = templates[projectData.type] || templates['web-app'];
    
    return {
        ...projectData,
        ...template,
        generatedAt: new Date().toISOString()
    };
}

// Display generated project in UI
function displayGeneratedProject(project) {
    DOM.projectOutput.innerHTML = `
        <div class="project-output-header">
            <h3>${project.name}</h3>
            <span class="project-type-badge">${project.type}</span>
            <span class="project-complexity-badge">${project.complexity}</span>
        </div>
        
        <div class="project-description">
            <p>${project.description}</p>
        </div>
        
        <div class="project-files">
            <h4>Generated Files:</h4>
            <div class="files-list">
                ${project.files.map(file => `
                    <div class="file-item">
                        <span class="file-icon">📄</span>
                        <span class="file-name">${file.name}</span>
                        <button class="btn btn-sm btn-copy" onclick="copyFileContent('${file.name}', \`${escapeTemplateLiteral(file.content)}\`)">Copy</button>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="project-dependencies">
            <h4>Dependencies:</h4>
            <div class="dependencies-list">
                ${project.dependencies.map(dep => `<span class="dependency-badge">${dep}</span>`).join('')}
            </div>
        </div>
        
        <div class="project-instructions">
            <h4>Setup Instructions:</h4>
            <pre><code>${project.instructions}</code></pre>
        </div>
    `;
    
    // Enable download button
    DOM.downloadProjectBtn.disabled = false;
    DOM.downloadProjectBtn.dataset.projectId = project.id;
}

// Escape template literal for display
function escapeTemplateLiteral(str) {
    return str.replace(/`/g, '\\`').replace(/\$/g, '\\$');
}

// Copy file content to clipboard
window.copyFileContent = function(fileName, content) {
    navigator.clipboard.writeText(content).then(() => {
        showNotification(`Copied ${fileName} to clipboard`, 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy to clipboard', 'error');
    });
};

// Download project as ZIP
function downloadProject() {
    const projectId = DOM.downloadProjectBtn.dataset.projectId;
    const project = AppState.projects.find(p => p.id === projectId);
    
    if (!project) {
        showNotification('Project not found', 'error');
        return;
    }
    
    // Check if FileSaver is available
    if (typeof JSZip === 'undefined' || typeof saveAs === 'undefined') {
        showNotification('ZIP library not loaded', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const zip = new JSZip();
        
        // Add files to ZIP
        project.files.forEach(file => {
            zip.file(file.name, file.content);
        });
        
        // Add project info file
        zip.file('PROJECT_INFO.json', JSON.stringify({
            name: project.name,
            description: project.description,
            type: project.type,
            complexity: project.complexity,
            generatedAt: project.generatedAt,
            dependencies: project.dependencies,
            instructions: project.instructions
        }, null, 2));
        
        // Generate and download ZIP
        zip.generateAsync({ type: 'blob' }).then(content => {
            saveAs(content, `${project.name.replace(/\s+/g, '_')}_project.zip`);
            showNotification('Project downloaded successfully', 'success');
        });
    } catch (error) {
        console.error('Error creating ZIP:', error);
        showNotification('Error downloading project', 'error');
    } finally {
        showLoading(false);
    }
}

// Populate API form with saved keys
function populateAPIForm() {
    Object.keys(AppState.apiKeys).forEach(key => {
        const input = document.getElementById(`api-${key}`);
        if (input) {
            input.value = AppState.apiKeys[key];
        }
    });
}

// Save API keys from form to storage
function saveAPIKeysToStorage() {
    Object.keys(AppState.apiKeys).forEach(key => {
        const input = document.getElementById(`api-${key}`);
        if (input) {
            AppState.apiKeys[key] = input.value.trim();
        }
    });
    
    saveAPIKeys();
    showNotification('API keys saved successfully', 'success');
}

// Test API connections
async function testAPIConnections() {
    showLoading(true);
    
    try {
        const results = [];
        
        // Test each API that has a key
        for (const [service, key] of Object.entries(AppState.apiKeys)) {
            if (key) {
                const result = await testAPI(service, key);
                results.push({ service, ...result });
            }
        }
        
        // Display results
        displayAPITestResults(results);
    } catch (error) {
        console.error('Error testing APIs:', error);
        showNotification('Error testing API connections', 'error');
    } finally {
        showLoading(false);
    }
}

// Test individual API (mock implementation)
async function testAPI(service, key) {
    // Simulate API test
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock responses based on service
    const mockResponses = {
        openai: { success: key.length > 10, message: 'OpenAI API connected successfully' },
        anthropic: { success: key.length > 10, message: 'Anthropic Claude API connected' },
        gemini: { success: key.length > 10, message: 'Google Gemini API connected' },
        groq: { success: key.length > 10, message: 'Groq API connected' },
        replicate: { success: key.length > 10, message: 'Replicate API connected' },
        huggingface: { success: key.length > 10, message: 'Hugging Face API connected' },
        cohere: { success: key.length > 10, message: 'Cohere API connected' },
        together: { success: key.length > 10, message: 'Together AI API connected' }
    };
    
    return mockResponses[service] || { success: false, message: 'Unknown service' };
}

// Display API test results
function displayAPITestResults(results) {
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'api-test-results';
    
    resultsContainer.innerHTML = `
        <h4>API Test Results:</h4>
        <div class="results-list">
            ${results.map(result => `
                <div class="api-test-result ${result.success ? 'success' : 'error'}">
                    <span class="api-service">${result.service}</span>
                    <span class="api-status">${result.success ? '✅' : '❌'}</span>
                    <span class="api-message">${result.message}</span>
                </div>
            `).join('')}
        </div>
    `;
    
    // Remove existing results
    const existingResults = document.querySelector('.api-test-results');
    if (existingResults) {
        existingResults.remove();
    }
    
    // Add new results
    DOM.apiConfigContent.appendChild(resultsContainer);
}

// Populate settings form
function populateSettingsForm() {
    DOM.autoSaveToggle.checked = AppState.settings.autoSave;
    DOM.themeSelect.value = AppState.settings.theme;
    DOM.notificationsToggle.checked = AppState.settings.notifications;
}

// Save settings
function saveSettings() {
    AppState.settings.autoSave = DOM.autoSaveToggle.checked;
    AppState.settings.theme = DOM.themeSelect.value;
    AppState.settings.notifications = DOM.notificationsToggle.checked;
    
    saveAppState();
    showNotification('Settings saved successfully', 'success');
}

// Apply theme to the application
function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    
    // Update chart colors if theme changes
    if (DOM.usageChart && typeof Chart !== 'undefined') {
        // Re-initialize chart with new theme
        initializeUsageChart();
    }
}

// Switch to a specific tab
function switchToTab(tabId) {
    const tabMap = {
        'dashboard': DOM.dashboardTab,
        'api-config': DOM.apiConfigTab,
        'bot-manager': DOM.botManagerTab,
        'project-generator': DOM.projectGeneratorTab,
        'settings': DOM.settingsTab
    };
    
    const tab = tabMap[tabId];
    if (tab) {
        tab.click();
    }
}

// Check if any API keys are configured
function hasAPIKeys() {
    return Object.values(AppState.apiKeys).some(key => key && key.length > 0);
}

// Show/hide loading overlay
function showLoading(show) {
    if (show) {
        DOM.loadingOverlay.classList.add('active');
        AppState.isLoading = true;
    } else {
        DOM.loadingOverlay.classList.remove('active');
        AppState.isLoading = false;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    if (!AppState.settings.notifications && type !== 'error') {
        return;
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${getNotificationIcon(type)}</span>
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    DOM.notificationContainer.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Get notification icon based on type
function getNotificationIcon(type) {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    return icons[type] || icons.info;
}

// Set up auto-save interval
function setupAutoSave() {
    // Clear any existing interval
    if (window.autoSaveInterval) {
        clearInterval(window.autoSaveInterval);
    }
    
    // Set up new interval (every 30 seconds)
    window.autoSaveInterval = setInterval(() => {
        if (AppState.settings.autoSave) {
            saveAppState();
            saveBots();
            saveProjects();
            console.log('Auto-save completed');
        }
    }, 30000);
}

// Generate unique ID
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Format time for display
function formatTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

// Template generation functions (simplified examples)
function generateHTMLTemplate(project) {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${project.name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>