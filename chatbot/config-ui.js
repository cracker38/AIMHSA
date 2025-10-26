/**
 * AIMHSA Configuration UI Management
 * Provides UI components for managing frontend configuration
 */

window.AIMHSA = window.AIMHSA || {};

// Configuration UI class for managing settings interface
class AIMHSAConfigUI {
    constructor() {
        this.isInitialized = false;
        this.settingsModal = null;
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.createSettingsModal();
        this.bindEvents();
        this.isInitialized = true;
    }
    
    createSettingsModal() {
        // Create settings modal HTML
        const modalHTML = `
            <div id="aimhsa-settings-modal" class="modal fade" tabindex="-1" role="dialog">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">AIMHSA Settings</h5>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <form id="aimhsa-settings-form">
                                <div class="form-group">
                                    <label for="api-base-url">API Base URL</label>
                                    <input type="url" class="form-control" id="api-base-url" 
                                           placeholder="https://your-domain.com">
                                    <small class="form-text text-muted">
                                        Base URL for API requests. Leave empty for auto-detection.
                                    </small>
                                </div>
                                
                                <div class="form-group">
                                    <label for="environment">Environment</label>
                                    <select class="form-control" id="environment">
                                        <option value="production">Production</option>
                                        <option value="development">Development</option>
                                        <option value="staging">Staging</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <div class="custom-control custom-checkbox">
                                        <input type="checkbox" class="custom-control-input" id="debug-mode">
                                        <label class="custom-control-label" for="debug-mode">
                                            Enable Debug Mode
                                        </label>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-danger" id="reset-config">Reset to Defaults</button>
                            <button type="button" class="btn btn-primary" id="save-config">Save Changes</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Append to body if not exists
        if (!document.getElementById('aimhsa-settings-modal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
        
        this.settingsModal = document.getElementById('aimhsa-settings-modal');
    }
    
    bindEvents() {
        // Save configuration
        const saveBtn = document.getElementById('save-config');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveConfiguration());
        }
        
        // Reset configuration
        const resetBtn = document.getElementById('reset-config');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetConfiguration());
        }
        
        // Load configuration when modal opens
        if (this.settingsModal) {
            this.settingsModal.addEventListener('show.bs.modal', () => this.loadConfiguration());
        }
    }
    
    loadConfiguration() {
        const config = window.AIMHSA.Config;
        
        // Populate form fields
        const apiUrlField = document.getElementById('api-base-url');
        const environmentField = document.getElementById('environment');
        const debugModeField = document.getElementById('debug-mode');
        
        if (apiUrlField) apiUrlField.value = config.get('apiBaseUrl') || '';
        if (environmentField) environmentField.value = config.get('environment') || 'production';
        if (debugModeField) debugModeField.checked = config.get('debugMode') || false;
    }
    
    saveConfiguration() {
        const config = window.AIMHSA.Config;
        
        // Get form values
        const apiUrl = document.getElementById('api-base-url')?.value?.trim();
        const environment = document.getElementById('environment')?.value;
        const debugMode = document.getElementById('debug-mode')?.checked;
        
        // Update configuration
        if (apiUrl) config.set('apiBaseUrl', apiUrl);
        config.set('environment', environment);
        config.set('debugMode', debugMode);
        
        // Show success message
        this.showNotification('Configuration saved successfully!', 'success');
        
        // Close modal
        if (window.jQuery && window.jQuery.fn.modal) {
            window.jQuery(this.settingsModal).modal('hide');
        }
        
        // Refresh page to apply changes
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }
    
    resetConfiguration() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            window.AIMHSA.Config.reset();
            this.loadConfiguration();
            this.showNotification('Configuration reset to defaults!', 'info');
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    openSettings() {
        if (!this.isInitialized) this.init();
        
        if (window.jQuery && window.jQuery.fn.modal) {
            window.jQuery(this.settingsModal).modal('show');
        } else {
            // Fallback for non-Bootstrap environments
            this.settingsModal.style.display = 'block';
        }
    }
}

// Initialize global configuration UI
window.AIMHSA.ConfigUI = new AIMHSAConfigUI();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.AIMHSA.ConfigUI.init();
});

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIMHSAConfigUI;
}
