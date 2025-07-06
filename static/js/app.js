// Smart Cafe JavaScript Functions

// Global variables
let notificationTimeout;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notification
    const existingNotification = document.querySelector('.notification-toast');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto remove after duration
    clearTimeout(notificationTimeout);
    notificationTimeout = setTimeout(() => {
        if (notification && notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Loading states
function showLoading(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.classList.add('loading');
        const spinner = document.createElement('span');
        spinner.className = 'spinner-border spinner-border-sm me-2 loading-spinner';
        element.insertBefore(spinner, element.firstChild);
    }
}

function hideLoading(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.classList.remove('loading');
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

// Form validation
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    });

    return isValid;
}

// Real-time form validation
function setupFormValidation(formSelector) {
    const form = document.querySelector(formSelector);
    if (!form) return;

    const fields = form.querySelectorAll('input, select, textarea');
    
    fields.forEach(field => {
        field.addEventListener('blur', function() {
            if (this.hasAttribute('required')) {
                if (!this.value.trim()) {
                    this.classList.add('is-invalid');
                    this.classList.remove('is-valid');
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            }
        });

        field.addEventListener('input', function() {
            if (this.classList.contains('is-invalid') && this.value.trim()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    });
}

// Confirm dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Auto-refresh functionality
class AutoRefresh {
    constructor(url, callback, interval = 5000) {
        this.url = url;
        this.callback = callback;
        this.interval = interval;
        this.timeoutId = null;
        this.isActive = false;
    }

    start() {
        if (this.isActive) return;
        
        this.isActive = true;
        this.refresh();
    }

    stop() {
        this.isActive = false;
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
    }

    refresh() {
        if (!this.isActive) return;

        fetch(this.url)
            .then(response => response.json())
            .then(data => {
                this.callback(data);
                if (this.isActive) {
                    this.timeoutId = setTimeout(() => this.refresh(), this.interval);
                }
            })
            .catch(error => {
                console.error('Auto-refresh error:', error);
                if (this.isActive) {
                    this.timeoutId = setTimeout(() => this.refresh(), this.interval * 2); // Double interval on error
                }
            });
    }
}

// Local storage helpers
const Storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Failed to set localStorage item:', e);
        }
    },

    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Failed to get localStorage item:', e);
            return defaultValue;
        }
    },

    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('Failed to remove localStorage item:', e);
        }
    }
};

// Format currency
function formatCurrency(amount, currency = '₺') {
    return currency + parseFloat(amount).toFixed(2);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Handle network errors
function handleNetworkError(error) {
    console.error('Network error:', error);
    showNotification('Bağlantı hatası. Lütfen tekrar deneyin.', 'danger');
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Panoya kopyalandı!', 'success', 2000);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Panoya kopyalandı!', 'success', 2000);
    }
}

// Print function
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        showNotification('Yazdırılacak içerik bulunamadı.', 'danger');
        return;
    }

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Yazdır</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { font-family: Arial, sans-serif; }
                @media print {
                    .no-print { display: none !important; }
                }
            </style>
        </head>
        <body>
            ${element.outerHTML}
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Initialize page-specific functionality
function initPageSpecific() {
    const page = document.body.getAttribute('data-page');
    
    switch(page) {
        case 'orders':
            initOrdersPage();
            break;
        case 'menu':
            initMenuPage();
            break;
        case 'customer-menu':
            initCustomerMenuPage();
            break;
        default:
            break;
    }
}

// Orders page initialization
function initOrdersPage() {
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    if (autoRefreshCheckbox) {
        const refresher = new AutoRefresh('/api/orders/' + window.restaurantId, updateOrdersDisplay, 3000);
        
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                refresher.start();
            } else {
                refresher.stop();
            }
        });

        if (autoRefreshCheckbox.checked) {
            refresher.start();
        }
    }
}

// Menu page initialization
function initMenuPage() {
    setupFormValidation('#menuForm');
}

// Customer menu page initialization
function initCustomerMenuPage() {
    // This would be handled in the customer_menu.html template
}

// Export functions for global use
window.SmartCafe = {
    showNotification,
    showLoading,
    hideLoading,
    validateForm,
    confirmAction,
    AutoRefresh,
    Storage,
    formatCurrency,
    formatDate,
    copyToClipboard,
    printElement,
    handleNetworkError
};

// Call page-specific initialization
document.addEventListener('DOMContentLoaded', initPageSpecific);