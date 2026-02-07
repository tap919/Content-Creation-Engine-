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
        connections: {},
        preferences: {}
    },
    contentQueue: [],
    uploadProgress: 0,
    activeUploads: 0
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
    initializePlatformSelector();
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
    
    if (menuToggle && sidebar) {
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
        'settings': 'Settings',
        'campaigns': 'Campaign Workflows',
        'video': 'Video Studio',
        'audio': 'Audio Studio',
        'images': 'Image Generator',
        'automation': 'Automation',
        'evolution': 'Evolution Loop',
        'avatar-studio': 'Avatar Studio',
        'creative-spark': 'Creative Spark',
        'repurpose': 'Repurpose Content',
        'brand-dna': 'Brand DNA Settings'
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
    } else if (page === 'campaigns') {
        loadCampaignsList();
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
    
    // Track active uploads to prevent race conditions
    DashboardState.activeUploads++;
    
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
    
    // Decrement active uploads counter
    DashboardState.activeUploads--;
    
    // Only hide progress when all uploads are complete
    if (DashboardState.activeUploads === 0) {
        setTimeout(() => {
            if (progressContainer && DashboardState.activeUploads === 0) {
                progressContainer.classList.add('hidden');
            }
            if (progressFill) {
                progressFill.style.width = '0%';
            }
        }, 2000);
    }
}

// Upload timeout constant (5 minutes)
const UPLOAD_TIMEOUT_MS = 5 * 60 * 1000;

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
            reject(new Error('Upload failed due to network error. Please check your connection and try again.'));
        });
        
        xhr.addEventListener('timeout', () => {
            reject(new Error('Upload timed out. The file may be too large or the server is taking too long to respond.'));
        });
        
        // Set upload timeout
        xhr.timeout = UPLOAD_TIMEOUT_MS;
        
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
        replicate: document.querySelector('#replicate-key')?.value || '',
        twitter: document.querySelector('#twitter-bearer')?.value || '',
        youtube: document.querySelector('#youtube-key')?.value || ''
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
            // Don't store API keys in client-side state for security
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
    
    // Clear existing content
    contentList.innerHTML = '';

    // Safely build DOM elements to avoid XSS when items come from backend
    items.forEach(item => {
        const itemEl = document.createElement('div');
        itemEl.classList.add('content-item');
        itemEl.dataset.id = String(item.id);

        const thumbnailEl = document.createElement('div');
        thumbnailEl.classList.add('content-thumbnail');
        // getFileIcon returns trusted emoji content
        thumbnailEl.textContent = getFileIcon(item.type);

        const infoEl = document.createElement('div');
        infoEl.classList.add('content-info');

        const nameEl = document.createElement('div');
        nameEl.classList.add('content-name');
        nameEl.textContent = item.name;

        const metaEl = document.createElement('div');
        metaEl.classList.add('content-meta');
        metaEl.textContent = item.date;

        infoEl.appendChild(nameEl);
        infoEl.appendChild(metaEl);

        const statusEl = document.createElement('span');
        statusEl.classList.add('content-status');
        statusEl.classList.add(item.status);
        statusEl.textContent = capitalizeFirst(item.status);

        itemEl.appendChild(thumbnailEl);
        itemEl.appendChild(infoEl);
        itemEl.appendChild(statusEl);

        contentList.appendChild(itemEl);
    });
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

    const iconSpan = document.createElement('span');
    iconSpan.className = 'toast-icon ' + type;
    iconSpan.textContent = icons[type] || '';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'toast-content';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'toast-title';
    titleDiv.textContent = title != null ? title : '';

    const messageDiv = document.createElement('div');
    messageDiv.className = 'toast-message';
    messageDiv.textContent = message != null ? message : '';

    contentDiv.appendChild(titleDiv);
    contentDiv.appendChild(messageDiv);

    const closeButton = document.createElement('button');
    closeButton.className = 'toast-close';
    closeButton.type = 'button';
    closeButton.textContent = '✕';
    closeButton.addEventListener('click', () => {
        toast.remove();
    });

    toast.appendChild(iconSpan);
    toast.appendChild(contentDiv);
    toast.appendChild(closeButton);
    
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

// Settings Tab Function (moved from inline script)
function showSettingsTab(tab, e) {
    const settingsPage = document.getElementById('page-settings');
    if (!settingsPage) {
        return;
    }

    // Update active tab styling
    settingsPage.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));

    // Prefer currentTarget (the element with the event listener) over target
    const tabElement = (e && e.currentTarget && e.currentTarget.classList && e.currentTarget.classList.contains('tab'))
        ? e.currentTarget
        : (e && e.target && e.target.classList && e.target.classList.contains('tab'))
            ? e.target
            : null;

    if (tabElement) {
        tabElement.classList.add('active');
    }
    
    // Note: In the current grid layout, all settings sections are always visible
    // This function updates only the active tab styling for visual feedback
}

// Campaign Wizard State
const CampaignWizard = {
    currentStep: 1,
    totalSteps: 4,
    data: {
        name: '',
        goal: '',
        audience: '',
        platforms: [],
        contentCount: 10,
        contentTypes: [],
        tone: 'professional',
        startDate: '',
        endDate: '',
        frequency: 'every-other-day',
        autoPublish: false
    }
};

// Show global help modal
function showGlobalHelp() {
    openModal('global-help-modal');
}

// Open Campaign Wizard
function openCampaignWizard() {
    // Reset wizard state
    CampaignWizard.currentStep = 1;
    CampaignWizard.data = {
        name: '',
        goal: '',
        audience: '',
        platforms: [],
        contentCount: 10,
        contentTypes: [],
        tone: 'professional',
        startDate: '',
        endDate: '',
        frequency: 'every-other-day',
        autoPublish: false
    };
    
    // Reset wizard UI
    updateWizardUI();
    
    // Set default dates (start: today, end: 2 weeks from now)
    const today = new Date();
    const twoWeeksLater = new Date(today);
    twoWeeksLater.setDate(today.getDate() + 14);

    // Helper to format a Date as YYYY-MM-DD in local time for date inputs
    function formatDateForInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    const startInput = document.getElementById('campaign-start');
    const endInput = document.getElementById('campaign-end');
    if (startInput) startInput.value = formatDateForInput(today);
    if (endInput) endInput.value = formatDateForInput(twoWeeksLater);
    
    openModal('campaign-wizard-modal');
}

// Next wizard step
function nextWizardStep() {
    // Save current step data
    saveWizardStepData();
    
    if (CampaignWizard.currentStep < CampaignWizard.totalSteps) {
        CampaignWizard.currentStep++;
        updateWizardUI();
    } else {
        // Submit campaign
        createCampaign();
    }
}

// Previous wizard step
function prevWizardStep() {
    if (CampaignWizard.currentStep > 1) {
        CampaignWizard.currentStep--;
        updateWizardUI();
    }
}

// Save current step data
function saveWizardStepData() {
    switch (CampaignWizard.currentStep) {
        case 1:
            CampaignWizard.data.name = document.getElementById('campaign-name')?.value || '';
            CampaignWizard.data.goal = document.getElementById('campaign-goal')?.value || '';
            CampaignWizard.data.audience = document.getElementById('campaign-audience')?.value || '';
            break;
        case 2:
            CampaignWizard.data.platforms = [];
            document.querySelectorAll('input[name="platform"]:checked').forEach(input => {
                CampaignWizard.data.platforms.push(input.value);
            });
            break;
        case 3:
            CampaignWizard.data.contentCount = document.getElementById('campaign-content-count')?.value || '10';
            CampaignWizard.data.tone = document.getElementById('campaign-tone')?.value || 'professional';
            break;
        case 4:
            CampaignWizard.data.startDate = document.getElementById('campaign-start')?.value || '';
            CampaignWizard.data.endDate = document.getElementById('campaign-end')?.value || '';
            CampaignWizard.data.frequency = document.getElementById('campaign-frequency')?.value || 'every-other-day';
            CampaignWizard.data.autoPublish = document.getElementById('campaign-auto-publish')?.checked || false;
            break;
    }
}

// Update wizard UI based on current step
function updateWizardUI() {
    // Update step indicators
    for (let i = 1; i <= CampaignWizard.totalSteps; i++) {
        const stepEl = document.getElementById(`wizard-step-${i}`);
        const contentEl = document.getElementById(`wizard-content-${i}`);
        
        if (stepEl) {
            stepEl.classList.remove('active', 'completed');
            if (i < CampaignWizard.currentStep) {
                stepEl.classList.add('completed');
            } else if (i === CampaignWizard.currentStep) {
                stepEl.classList.add('active');
            }
        }
        
        if (contentEl) {
            if (i === CampaignWizard.currentStep) {
                contentEl.classList.remove('hidden');
            } else {
                contentEl.classList.add('hidden');
            }
        }
    }
    
    // Update buttons
    const prevBtn = document.getElementById('wizard-prev-btn');
    const nextBtn = document.getElementById('wizard-next-btn');
    
    if (prevBtn) {
        prevBtn.style.display = CampaignWizard.currentStep > 1 ? 'block' : 'none';
    }
    
    if (nextBtn) {
        if (CampaignWizard.currentStep === CampaignWizard.totalSteps) {
            nextBtn.textContent = '🚀 Create Campaign';
        } else {
            nextBtn.textContent = 'Next →';
        }
    }

    // Restore form field values from saved wizard data when navigating between steps
    if (typeof CampaignWizard !== 'undefined' && CampaignWizard.data) {
        switch (CampaignWizard.currentStep) {
            case 1:
                // Restore campaign basic information (e.g., name)
                {
                    const nameInput = document.getElementById('campaign-name-input');
                    if (nameInput && typeof CampaignWizard.data.name !== 'undefined') {
                        nameInput.value = CampaignWizard.data.name;
                    }
                }
                break;
            case 2:
                // Restore platform selections from CampaignWizard.data.platforms
                {
                    if (Array.isArray(CampaignWizard.data.platforms)) {
                        const platformInputs = document.querySelectorAll('input[name="campaign-platform"]');
                        platformInputs.forEach(function (input) {
                            if (input && typeof input.value !== 'undefined') {
                                input.checked = CampaignWizard.data.platforms.indexOf(input.value) !== -1;
                            }
                        });
                    }
                }
                break;
            default:
                // Additional steps can restore their fields here as needed
                break;
        }
    }
}

// Create campaign from wizard data
async function createCampaign() {
    saveWizardStepData();
    
    // Validate required fields
    if (!CampaignWizard.data.name) {
        showToast('error', 'Missing Information', 'Please enter a campaign name');
        CampaignWizard.currentStep = 1;
        updateWizardUI();
        return;
    }
    
    if (CampaignWizard.data.platforms.length === 0) {
        showToast('error', 'Missing Information', 'Please select at least one platform');
        CampaignWizard.currentStep = 2;
        updateWizardUI();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/campaigns`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(CampaignWizard.data)
        });
        
        if (response.ok) {
            await response.json();
            showToast('success', 'Campaign Created', `"${CampaignWizard.data.name}" is ready to go!`);
            closeModal('campaign-wizard-modal');
            
            // Refresh campaigns list
            if (DashboardState.currentPage === 'campaigns') {
                loadCampaignsList();
            }
        } else {
            // Handle HTTP error responses by showing an error toast
            let errorMessage = 'Failed to create campaign. Please try again.';
            try {
                const errorData = await response.json();
                if (errorData && (errorData.message || errorData.error)) {
                    errorMessage = errorData.message || errorData.error;
                }
            } catch (parseError) {
                // Ignore JSON parsing errors and fall back to generic message
            }
            showToast('error', 'Campaign Error', errorMessage);
        }
    } catch (error) {
        // Distinguish network/API-unavailable errors from other exceptions
        const errorMessage = (error && error.message) ? error.message : String(error);
        const lowerMessage = errorMessage.toLowerCase();
        const isNetworkError =
            lowerMessage.includes('failed to fetch') ||
            lowerMessage.includes('network') ||
            lowerMessage.includes('connection');

        if (isNetworkError) {
            // For demo purposes, simulate a successful campaign creation when API is unavailable
            showToast('success', 'Campaign Created (Simulated)', `"${CampaignWizard.data.name}" has been created (API unavailable, simulated in demo).`);
            closeModal('campaign-wizard-modal');
        } else {
            console.error('Error creating campaign:', error);
            showToast('error', 'Campaign Error', 'An unexpected error occurred while creating the campaign. Please try again.');
        }
    }
}

// Create campaign from template
function createCampaignFromTemplate(templateType) {
    // Pre-fill wizard data based on template
    const templates = {
        'launch': {
            name: 'Product Launch Campaign',
            goal: 'Generate buzz and awareness for new product launch',
            contentCount: '10',
            tone: 'professional',
            frequency: 'daily'
        },
        'evergreen': {
            name: 'Evergreen Content Series',
            goal: 'Build consistent brand presence with always-relevant content',
            contentCount: '20',
            tone: 'educational',
            frequency: 'twice-weekly'
        },
        'event': {
            name: 'Event Promotion Campaign',
            goal: 'Drive registrations and engagement before, during, and after event',
            contentCount: '15',
            tone: 'inspirational',
            frequency: 'daily'
        }
    };
    
    const template = templates[templateType];
    if (template) {
        // Open the campaign wizard before accessing its form fields
        openCampaignWizard();

        // Pre-fill form fields after wizard is opened
        const nameInput = document.getElementById('campaign-name');
        const goalInput = document.getElementById('campaign-goal');
        const contentCountInput = document.getElementById('campaign-content-count');
        const toneInput = document.getElementById('campaign-tone');
        const frequencyInput = document.getElementById('campaign-frequency');

        if (nameInput) nameInput.value = template.name;
        if (goalInput) goalInput.value = template.goal;
        if (contentCountInput) contentCountInput.value = template.contentCount;
        if (toneInput) toneInput.value = template.tone;
        if (frequencyInput) frequencyInput.value = template.frequency;
        
        showToast('info', 'Template Applied', `Using "${templateType}" template`);
    }
}

// Load campaigns list
async function loadCampaignsList() {
    try {
        const response = await fetch(`${API_BASE}/api/campaigns`);
        if (response.ok) {
            await response.json();
            // Update campaigns list UI
            // For now, the static demo data is shown
        }
    } catch (error) {
        // API might not exist yet, use demo data
        console.log('Using demo campaign data');
    }
}

// Initialize platform selector interactions
function initializePlatformSelector() {
    document.querySelectorAll('.platform-option').forEach(option => {
        // Sync selected class with checkbox state on page load and checkbox change
        const checkbox = option.querySelector('input[type="checkbox"]');
        if (checkbox) {
            // Ensure initial visual state matches the checkbox checked state
            option.classList.toggle('selected', checkbox.checked);
            
            checkbox.addEventListener('change', () => {
                option.classList.toggle('selected', checkbox.checked);
            });
        }
    });
}

// Export for global access
window.Dashboard = {
    navigateTo,
    generateContent,
    triggerEvolution,
    openModal,
    closeModal,
    showToast,
    showSettingsTab,
    showGlobalHelp,
    openCampaignWizard,
    nextWizardStep,
    prevWizardStep,
    createCampaignFromTemplate,
    // New functions for enhanced features
    generateIdeas,
    generateHooks,
    saveBrandDNA,
    repurposeContent,
    selectAvatar,
    editAvatar,
    useAvatar,
    createAvatar,
    showModal
};

// === New Feature Functions ===

// Generate creative ideas
async function generateIdeas() {
    const niche = document.getElementById('spark-niche').value;
    const contentType = document.getElementById('spark-content-type').value;
    const numIdeas = document.getElementById('spark-num-ideas').value;
    
    if (!niche) {
        showToast('warning', 'Missing Input', 'Please enter your niche or topic');
        return;
    }
    
    const resultsContainer = document.getElementById('generated-ideas');
    resultsContainer.innerHTML = '<div style="text-align: center; padding: 48px;"><div style="font-size: 24px; margin-bottom: 12px;">⚡</div><div>Generating ideas...</div></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/ideas/generate?niche=${encodeURIComponent(niche)}&content_type=${contentType}&num_ideas=${numIdeas}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Display ideas
            let html = '';
            data.ideas.forEach((idea, index) => {
                html += `
                    <div class="glass-card" style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 12px;">
                            <div style="flex: 1;">
                                <div style="font-weight: 600; font-size: 16px; margin-bottom: 4px;">${idea.title}</div>
                                <div style="font-size: 13px; color: #94a3b8; margin-bottom: 8px;">${idea.format} • ${idea.estimated_time}</div>
                            </div>
                            <button class="btn-primary" style="padding: 6px 12px; font-size: 13px;" onclick="Dashboard.generateOutline('${idea.id}')">
                                📝 Outline
                            </button>
                        </div>
                        <div style="padding: 12px; background: rgba(139, 92, 246, 0.05); border-radius: 8px; margin-bottom: 8px;">
                            <div style="font-size: 13px; font-weight: 500; margin-bottom: 4px;">Hook:</div>
                            <div style="font-size: 14px; font-style: italic;">"${idea.hook}"</div>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn-secondary" onclick="Dashboard.useIdea('${idea.id}')" style="flex: 1;">Use This Idea</button>
                            <button class="btn-secondary" onclick="Dashboard.generateVariations('${idea.id}')" style="flex: 1;">Variations</button>
                        </div>
                    </div>
                `;
            });
            
            resultsContainer.innerHTML = html;
            showToast('success', 'Ideas Generated', `${data.ideas.length} creative ideas generated!`);
        } else {
            throw new Error('Failed to generate ideas');
        }
    } catch (error) {
        console.error('Error generating ideas:', error);
        resultsContainer.innerHTML = '<div style="text-align: center; padding: 48px; color: #ef4444;"><div>Failed to generate ideas. Please try again.</div></div>';
        showToast('error', 'Error', 'Failed to generate ideas');
    }
}

// Generate hooks for a topic
async function generateHooks(topic) {
    try {
        const response = await fetch(`${API_BASE}/api/ideas/hooks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, platform: 'tiktok', num_hooks: 5 })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Generated hooks:', data.hooks);
            showToast('success', 'Hooks Generated', `${data.hooks.length} hook ideas ready`);
        }
    } catch (error) {
        console.error('Error generating hooks:', error);
    }
}

// Save brand DNA settings
async function saveBrandDNA() {
    const brandData = {
        primary_color: document.getElementById('brand-primary-color').value,
        secondary_color: document.getElementById('brand-secondary-color').value,
        accent_color: document.getElementById('brand-accent-color').value,
        primary_font: document.getElementById('brand-primary-font').value,
        secondary_font: document.getElementById('brand-secondary-font').value,
        logo_position: document.getElementById('brand-logo-position').value,
        tone_of_voice: document.getElementById('brand-tone').value,
        content_style: document.getElementById('brand-style').value,
        animation_style: document.getElementById('brand-animation').value,
        transition_style: document.getElementById('brand-transition').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/brand`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(brandData)
        });
        
        if (response.ok) {
            showToast('success', 'Brand DNA Saved', 'Your brand identity has been updated');
        } else {
            throw new Error('Failed to save brand DNA');
        }
    } catch (error) {
        console.error('Error saving brand DNA:', error);
        showToast('error', 'Error', 'Failed to save brand DNA settings');
    }
}

// Repurpose content
async function repurposeContent() {
    const selectedPlatforms = Array.from(document.querySelectorAll('input[name="repurpose-platform"]:checked'))
        .map(cb => cb.value);
    
    if (selectedPlatforms.length === 0) {
        showToast('warning', 'No Platforms Selected', 'Please select at least one target platform');
        return;
    }
    
    const previewContainer = document.getElementById('repurpose-preview');
    previewContainer.innerHTML = '<div style="padding: 48px; text-align: center;"><div style="font-size: 24px; margin-bottom: 12px;">⚡</div><div>Repurposing content...</div></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/repurpose`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content_id: 'demo_content',
                platforms: selectedPlatforms
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            let html = `
                <div style="padding: 24px;">
                    <div style="font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #10b981;">
                        ✓ Repurposing Complete!
                    </div>
                    <div style="font-size: 14px; margin-bottom: 16px;">
                        Created ${data.variants_created} optimized versions
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
            `;
            
            selectedPlatforms.forEach(platform => {
                html += `
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: rgba(16, 185, 129, 0.1); border-radius: 8px;">
                        <span style="font-size: 14px; font-weight: 500;">${platform}</span>
                        <button class="btn-secondary" style="padding: 4px 12px; font-size: 12px;">Download</button>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
            
            previewContainer.innerHTML = html;
            showToast('success', 'Content Repurposed', `Created ${data.variants_created} platform-optimized versions`);
        } else {
            throw new Error('Failed to repurpose content');
        }
    } catch (error) {
        console.error('Error repurposing content:', error);
        previewContainer.innerHTML = '<div style="padding: 48px; text-align: center; color: #ef4444;"><div>Failed to repurpose content. Please try again.</div></div>';
        showToast('error', 'Error', 'Failed to repurpose content');
    }
}

// Avatar management functions
function selectAvatar(avatarId) {
    console.log('Selected avatar:', avatarId);
    showToast('info', 'Avatar Selected', 'Avatar ready to use in content creation');
}

function editAvatar(avatarId) {
    console.log('Edit avatar:', avatarId);
    showToast('info', 'Edit Avatar', 'Avatar customization coming soon');
}

function useAvatar(avatarId) {
    console.log('Use avatar:', avatarId);
    navigateTo('create');
    showToast('success', 'Avatar Loaded', 'Avatar ready in content creator');
}

// Generate outline for an idea
function generateOutline(ideaId) {
    console.log('Generate outline for:', ideaId);
    showToast('info', 'Generating Outline', 'Creating detailed script outline...');
}

// Use an idea
function useIdea(ideaId) {
    console.log('Use idea:', ideaId);
    navigateTo('create');
    showToast('success', 'Idea Loaded', 'Idea loaded into content creator');
}

// Generate variations
function generateVariations(ideaId) {
    console.log('Generate variations for:', ideaId);
    showToast('info', 'Generating Variations', 'Creating alternative versions...');
}

// Create avatar
async function createAvatar() {
    showToast('info', 'Creating Avatar', 'Training your AI avatar... This may take a few minutes');
    closeModal('create-avatar-modal');
    
    // Simulate avatar creation
    setTimeout(() => {
        showToast('success', 'Avatar Created', 'Your avatar is ready to use!');
        navigateTo('avatar-studio');
    }, 2000);
}

// Show modal helper
function showModal(modalId) {
    openModal(modalId);
}
