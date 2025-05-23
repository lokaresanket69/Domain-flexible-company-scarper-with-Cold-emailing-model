// LinkedIn Company Scraper - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize chart rendering if on results page
    if (document.getElementById('analyticsChart')) {
        renderAnalyticsChart();
    }
    
    // Initialize auto-save for form inputs
    initializeAutoSave();
    
    console.log('LinkedIn Company Scraper initialized successfully');
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Custom validation for scraper form
    const scraperForm = document.getElementById('scraperForm');
    if (scraperForm) {
        scraperForm.addEventListener('submit', function(event) {
            if (!validateScraperForm()) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    }
}

function validateScraperForm() {
    let isValid = true;
    const errors = [];
    
    // Validate keywords
    const keywords = document.getElementById('keywords').value.trim();
    if (!keywords) {
        errors.push('Keywords are required');
        isValid = false;
    }
    
    // Validate max results
    const maxResults = parseInt(document.getElementById('max_results').value);
    if (maxResults < 1 || maxResults > 50) {
        errors.push('Max results must be between 1 and 50');
        isValid = false;
    }
    
    // Validate sleep time
    const sleepTime = parseFloat(document.getElementById('sleep_time').value);
    if (sleepTime < 0.5 || sleepTime > 10) {
        errors.push('Sleep time must be between 0.5 and 10 seconds');
        isValid = false;
    }
    
    // Display errors if any
    if (!isValid) {
        showAlert('danger', 'Validation Error', errors.join('<br>'));
    }
    
    return isValid;
}

function initializeSearch() {
    const searchInput = document.getElementById('searchFilter');
    if (searchInput) {
        // Debounce search input
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterCompanies();
            }, 300);
        });
    }
}

function initializeAutoSave() {
    const formInputs = document.querySelectorAll('#scraperForm input, #scraperForm select');
    
    formInputs.forEach(input => {
        // Load saved values
        const savedValue = localStorage.getItem(`scraper_${input.name}`);
        if (savedValue && !input.value) {
            input.value = savedValue;
        }
        
        // Save on change
        input.addEventListener('change', function() {
            localStorage.setItem(`scraper_${input.name}`, input.value);
        });
    });
}

function showAlert(type, title, message) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <strong>${title}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertContainer = document.querySelector('main .container');
    alertContainer.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = alertContainer.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

function renderAnalyticsChart() {
    const ctx = document.getElementById('analyticsChart');
    if (!ctx) return;
    
    // Sample data - in real implementation, this would come from the server
    const data = {
        labels: ['Financial Services', 'Technology', 'Healthcare', 'Manufacturing', 'Consulting'],
        datasets: [{
            label: 'Companies by Industry',
            data: [12, 19, 8, 5, 7],
            backgroundColor: [
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 99, 132, 0.8)',
                'rgba(255, 205, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)',
                'rgba(153, 102, 255, 0.8)'
            ],
            borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 205, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)'
            ],
            borderWidth: 1
        }]
    };
    
    new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

// Utility functions
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('success', 'Copied', 'Text copied to clipboard');
    }, function() {
        showAlert('danger', 'Error', 'Failed to copy text');
    });
}

function downloadData(data, filename, type = 'text/csv') {
    const blob = new Blob([data], { type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Progress tracking for scraping operations
function updateProgress(current, total, message = '') {
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        const percentage = Math.round((current / total) * 100);
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);
        progressBar.textContent = `${percentage}%`;
    }
    
    const statusMessage = document.querySelector('.status-message');
    if (statusMessage && message) {
        statusMessage.textContent = message;
    }
}

// WebSocket connection for real-time updates (if needed)
function initializeWebSocket() {
    if (typeof WebSocket === 'undefined') {
        console.log('WebSocket not supported');
        return;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    try {
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onclose = function() {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(initializeWebSocket, 5000);
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        return ws;
    } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'scraping_progress':
            updateProgress(data.current, data.total, data.message);
            break;
        case 'scraping_complete':
            showAlert('success', 'Scraping Complete', `Found ${data.count} companies`);
            location.reload();
            break;
        case 'error':
            showAlert('danger', 'Error', data.message);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// Export functions for use in other scripts
window.ScraperApp = {
    showAlert,
    formatNumber,
    formatDate,
    copyToClipboard,
    downloadData,
    updateProgress
};

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to submit forms
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const activeForm = document.activeElement.closest('form');
        if (activeForm) {
            const submitBtn = activeForm.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.click();
            }
        }
    }
    
    // Escape to close modals
    if (event.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modalInstance = bootstrap.Modal.getInstance(openModal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }
});

// Performance monitoring
function logPerformanceMetrics() {
    if (typeof performance !== 'undefined' && performance.timing) {
        const timing = performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;
        console.log(`Page load time: ${loadTime}ms`);
    }
}

// Log performance metrics when page is fully loaded
window.addEventListener('load', logPerformanceMetrics);
