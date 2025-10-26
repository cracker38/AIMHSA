// AIMHSA API Helper
window.AIMHSA = window.AIMHSA || {};

// API helper class for making HTTP requests
class AIMHSAAPI {
    constructor() {
        this.baseUrl = this.getApiBaseUrl();
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }
    
    getApiBaseUrl() {
        if (window.AIMHSA && window.AIMHSA.Config) {
            return window.AIMHSA.Config.getApiBaseUrl();
        }
        // Fallback to auto-detection
        return `${window.location.protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}`;
    }
    
    async request(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const config = {
            method: 'GET',
            headers: { ...this.defaultHeaders },
            ...options
        };
        
        // Add body if provided and method supports it
        if (options.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            config.body = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
        }
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error(`API request failed: ${config.method} ${url}`, error);
            throw error;
        }
    }
    
    // Convenience methods
    get(path, options = {}) {
        return this.request(path, { ...options, method: 'GET' });
    }
    
    post(path, body, options = {}) {
        return this.request(path, { ...options, method: 'POST', body });
    }
    
    put(path, body, options = {}) {
        return this.request(path, { ...options, method: 'PUT', body });
    }
    
    delete(path, options = {}) {
        return this.request(path, { ...options, method: 'DELETE' });
    }
    
    // Authentication helpers
    setAuthToken(token) {
        this.defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    clearAuthToken() {
        delete this.defaultHeaders['Authorization'];
    }
    
    // Professional-specific helper
    setProfessionalId(professionalId) {
        this.defaultHeaders['X-Professional-ID'] = professionalId;
    }
    
    clearProfessionalId() {
        delete this.defaultHeaders['X-Professional-ID'];
    }
}

// Initialize global API instance
window.AIMHSA.API = new AIMHSAAPI();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIMHSAAPI;
}
