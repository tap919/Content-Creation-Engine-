/**
 * Agentic Content Factory - Dashboard JavaScript
 * Handles UI interactions and API communication
 */

// Dashboard State
const DashboardState = {
    currentPage: 'dashboard',
    user: {
        name: 'User',
        email: 'user@example.com'
    },
    settings: {
        apiKeys: {},
        connections: {},
        preferences: {}
    },
    contentQueue: [],
    uploadProgress: 0
};

// API Base URL
const API_BASE = window.location.origin;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeFileUpload();
    initializeSettings();
    loadInitialData();
    initializeToggles();
});

// Navigation
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            if (page) {
                navigateTo(page);
            }
        });
    });
    
    // Initialize mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
}

function navigateTo(page) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });
    
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(p => {
        p.classList.add('hidden');
    });
    
    // Show selected page
    const pageElement = document.getElementById(`page-${page}`);
    if (pageElement) {
        pageElement.classList.remove('hidden');
    }
    
    // Update page title
    const pageTitles = {
        'dashboard': 'Dashboard',
        'content': 'Content Manager',
        'create': 'Create Content',
        'analytics': 'Analytics',
        'trends': 'Trend Analysis',
        'settings': 'Settings'
    };
    
    const titleElement = document.querySelector('.page-title');
    if (titleElement) {
        titleElement.textContent = pageTitles[page] || 'Dashboard';
    }
    
    DashboardState.currentPage = page;
    
    // Load page-specific data
    if (page === 'dashboard') {
        loadDashboardData();
    } else if (page === 'content') {
        loadContentList();
    } else if (page === 'settings') {
        loadSettingsData();
    }
}

// File Upload
function initializeFileUpload() {
    const uploadZone = document.querySelector('.upload-zone');
    const uploadInput = document.querySelector('.upload-input');
    
    if (!uploadZone || !uploadInput) return;
    
    // Drag and drop handlers
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files);
        }
    });
    
    // File input change handler
    uploadInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files);
        }
    });
}

async function handleFileUpload(files) {
    const progressContainer = document.querySelector('.progress-container');
    const progressFill = document.querySelector('.progress-fill');
    const progressLabel = document.querySelector('.progress-label');
    const progressPercent = document.querySelector('.progress-percent');
    
    if (progressContainer) {
        progressContainer.classList.remove('hidden');
    }
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        if (progressLabel) {
            progressLabel.textContent = `Uploading: ${file.name}`;
        }
        
        try {
            await uploadFile(file, (progress) => {
                if (progressFill) {
                    progressFill.style.width = `${progress}%`;
                }
                if (progressPercent) {
                    progressPercent.textContent = `${Math.round(progress)}%`;
                }
            });
            
            showToast('success', 'Upload Complete', `${file.name} uploaded successfully`);
            
        } catch (error) {
            showToast('error', 'Upload Failed', error.message);
        }
    }
    
    // Reset progress
    setTimeout(() => {
        if (progressContainer) {
            progressContainer.classList.add('hidden');
        }
        if (progressFill) {
            progressFill.style.width = '0%';
        }
    }, 2000);
}

async function uploadFile(file, onProgress) {
    return new Promise((resolve, reject) => {
        const formData = new FormData();
        formData.append('file', file);
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const progress = (e.loaded / e.total) * 100;
                onProgress(progress);
            }
        });
        
        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error('Upload failed'));
            }
        });
        
        xhr.addEventListener('error', () => {
            reject(new Error('Network error'));
        });
        
        xhr.open('POST', `${API_BASE}/api/upload`);
        xhr.send(formData);
    });
}

// Settings
function initializeSettings() {
    // API Key form handlers
    const saveApiKeysBtn = document.querySelector('#save-api-keys');
    if (saveApiKeysBtn) {
        saveApiKeysBtn.addEventListener('click', saveApiKeys);
    }
    
    // Connection buttons
    document.querySelectorAll('.connect-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const service = e.target.dataset.service;
            handleConnection(service);
        });
    });
}

async function saveApiKeys() {
    const apiKeys = {
        openai: document.querySelector('#openai-key')?.value || '',
        elevenlabs: document.querySelector('#elevenlabs-key')?.value || '',
        replicate: document.querySelector('#replicate-key')?.value || ''
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/settings/api-keys`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiKeys)
        });
        
        if (response.ok) {
            showToast('success', 'Saved', 'API keys saved successfully');
            DashboardState.settings.apiKeys = apiKeys;
        } else {
            throw new Error('Failed to save API keys');
        }
    } catch (error) {
        showToast('error', 'Error', error.message);
    }
}

async function handleConnection(service) {
    const btn = document.querySelector(`[data-service="${service}"]`);
    const isConnected = btn?.classList.contains('connected');
    
    if (isConnected) {
        // Disconnect
        try {
            await fetch(`${API_BASE}/api/connections/${service}/disconnect`, {
                method: 'POST'
            });
            
            btn.classList.remove('connected');
            btn.textContent = 'Connect';
            showToast('info', 'Disconnected', `${service} disconnected`);
        } catch (error) {
            showToast('error', 'Error', `Failed to disconnect ${service}`);
        }
    } else {
        // Connect - Open OAuth flow
        window.open(`${API_BASE}/api/oauth/${service}`, '_blank', 'width=500,height=600');
    }
}

// Toggle switches
function initializeToggles() {
    document.querySelectorAll('.toggle input').forEach(toggle => {
        toggle.addEventListener('change', async (e) => {
            const setting = e.target.dataset.setting;
            const value = e.target.checked;
            
            try {
                await fetch(`${API_BASE}/api/settings/preferences`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ [setting]: value })
                });
                
                DashboardState.settings.preferences[setting] = value;
            } catch (error) {
                // Revert toggle on error
                e.target.checked = !value;
                showToast('error', 'Error', 'Failed to update setting');
            }
        });
    });
}

// Load Data
async function loadInitialData() {
    try {
        const [healthResponse, paramsResponse] = await Promise.all([
            fetch(`${API_BASE}/health`).catch(() => null),
            fetch(`${API_BASE}/parameters`).catch(() => null)
        ]);
        
        if (healthResponse?.ok) {
            const health = await healthResponse.json();
            updateHealthStatus(health);
        }
        
        if (paramsResponse?.ok) {
            const params = await paramsResponse.json();
            updateParametersDisplay(params);
        }
    } catch (error) {
        console.error('Failed to load initial data:', error);
    }
}

async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            const data = await response.json();
            updateHealthStatus(data);
        }
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

async function loadContentList() {
    // Placeholder - would load content from backend
    const contentList = document.querySelector('.content-list');
    if (!contentList) return;
    
    // Example content items
    const items = [
        { id: 1, name: 'Tech Trends Video', type: 'video', status: 'completed', date: '2 hours ago' },
        { id: 2, name: 'Biotech Newsletter', type: 'document', status: 'processing', date: '1 hour ago' },
        { id: 3, name: 'Social Media Post', type: 'image', status: 'queued', date: 'Just now' }
    ];
    
    contentList.innerHTML = items.map(item => `
        <div class="content-item" data-id="${item.id}">
            <div class="content-thumbnail">
                ${getFileIcon(item.type)}
            </div>
            <div class="content-info">
                <div class="content-name">${item.name}</div>
                <div class="content-meta">${item.date}</div>
            </div>
            <span class="content-status ${item.status}">${capitalizeFirst(item.status)}</span>
        </div>
    `).join('');
}

async function loadSettingsData() {
    // Load saved settings from backend
    try {
        const response = await fetch(`${API_BASE}/api/settings`);
        if (response.ok) {
            const settings = await response.json();
            populateSettingsForm(settings);
        }
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

function populateSettingsForm(settings) {
    if (settings.apiKeys) {
        const openaiInput = document.querySelector('#openai-key');
        const elevenlabsInput = document.querySelector('#elevenlabs-key');
        const replicateInput = document.querySelector('#replicate-key');
        
        if (openaiInput && settings.apiKeys?.openai && settings.apiKeys.openai.length >= 4) {
            openaiInput.value = '••••••••' + settings.apiKeys.openai.slice(-4);
        }
        if (elevenlabsInput && settings.apiKeys?.elevenlabs && settings.apiKeys.elevenlabs.length >= 4) {
            elevenlabsInput.value = '••••••••' + settings.apiKeys.elevenlabs.slice(-4);
        }
        if (replicateInput && settings.apiKeys?.replicate && settings.apiKeys.replicate.length >= 4) {
            replicateInput.value = '••••••••' + settings.apiKeys.replicate.slice(-4);
        }
    }
}

// Update UI
function updateHealthStatus(health) {
    const statusIndicator = document.querySelector('.system-status');
    if (statusIndicator) {
        statusIndicator.textContent = health.status === 'healthy' ? 'All systems operational' : 'Issues detected';
        statusIndicator.classList.toggle('healthy', health.status === 'healthy');
    }
}

function updateParametersDisplay(params) {
    const elements = {
        'generation-count': params.generation,
        'fitness-avg': params.fitness_average?.toFixed(2) || '0.00',
        'music-tempo': params.music_tempo?.toFixed(1) || '0.0',
        'music-energy': params.music_energy?.toFixed(1) || '0.0'
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const el = document.querySelector(`#${id}`);
        if (el) el.textContent = value;
    });
}

// Toast Notifications
function showToast(type, title, message) {
    const container = document.querySelector('.toast-container') || createToastContainer();
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <span class="toast-icon ${type}">${icons[type]}</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Modal Functions
function openModal(modalId) {
    const modal = document.querySelector(`#${modalId}`);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.querySelector(`#${modalId}`);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Content Generation
async function generateContent(options = {}) {
    const generateBtn = document.querySelector('#generate-btn');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="spinner"></span> Generating...';
    }
    
    try {
        const response = await fetch(`${API_BASE}/content/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                force_generation: true,
                ...options
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('success', 'Content Generated', `Created: ${result.topic || 'New content'}`);
            
            // Refresh content list
            if (DashboardState.currentPage === 'content') {
                loadContentList();
            }
        } else {
            throw new Error('Generation failed');
        }
    } catch (error) {
        showToast('error', 'Error', error.message);
    } finally {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '⚡ Generate Content';
        }
    }
}

// Trigger Evolution
async function triggerEvolution() {
    try {
        const response = await fetch(`${API_BASE}/evolve`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'evolved') {
                showToast('success', 'Evolution Complete', `New generation: ${result.new_generation}`);
            } else {
                showToast('info', 'No Evolution', 'No pending content to evolve');
            }
        }
    } catch (error) {
        showToast('error', 'Error', 'Failed to trigger evolution');
    }
}

// Utility Functions
function getFileIcon(type) {
    const icons = {
        video: '🎬',
        image: '🖼️',
        audio: '🎵',
        document: '📄',
        default: '📁'
    };
    return icons[type] || icons.default;
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Export for global access
window.Dashboard = {
    navigateTo,
    generateContent,
    triggerEvolution,
    openModal,
    closeModal,
    showToast
};
