/**
 * AIMHSA API Client
 * Centralized API communication with automatic configuration
 */

class ApiClient {
    constructor() {
        this.config = window.AppConfig;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }
    
    async request(endpoint, options = {}) {
        const url = this.config.getFullUrl(endpoint);
        
        const defaultOptions = {
            method: 'GET',
            headers: { ...this.defaultHeaders },
            timeout: this.config.settings.defaultTimeout
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        // Add custom headers if provided
        if (options.headers) {
            mergedOptions.headers = { ...mergedOptions.headers, ...options.headers };
        }
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }
    
    // GET request
    async get(endpoint, params = {}) {
        const url = new URL(this.config.getFullUrl(endpoint), window.location.origin);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return await fetch(url.toString(), {
            method: 'GET',
            headers: this.defaultHeaders
        }).then(res => res.json());
    }
    
    // POST request
    async post(endpoint, data = {}, options = {}) {
        return await this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
            ...options
        });
    }
    
    // PUT request
    async put(endpoint, data = {}, options = {}) {
        return await this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
            ...options
        });
    }
    
    // DELETE request
    async delete(endpoint, options = {}) {
        return await this.request(endpoint, {
            method: 'DELETE',
            ...options
        });
    }
    
    // Chat-specific methods
    async sendMessage(query, conversationId = null, account = null) {
        return await this.post('ask', {
            query,
            id: conversationId,
            account
        });
    }
    
    async getSession(account = null) {
        return await this.post('session', { account });
    }
    
    async getHistory(conversationId, password = null) {
        const params = { id: conversationId };
        if (password) params.password = password;
        return await this.get('history', params);
    }
    
    // Auth methods
    async login(email, password) {
        return await this.post('login', { email, password });
    }
    
    async register(userData) {
        return await this.post('register', userData);
    }
    
    async professionalLogin(credentials) {
        return await this.post('professionalLogin', credentials);
    }
    
    async adminLogin(credentials) {
        return await this.post('adminLogin', credentials);
    }
    
    // Professional methods
    async getProfessionalProfile(professionalId) {
        return await this.get('professionalProfile', {}, {
            headers: { 'X-Professional-ID': professionalId }
        });
    }
    
    async getProfessionalSessions(professionalId, limit = 50) {
        return await this.get('professionalSessions', { limit }, {
            headers: { 'X-Professional-ID': professionalId }
        });
    }
    
    // Health check
    async healthCheck() {
        try {
            const response = await this.get('healthz');
            return response.ok === true;
        } catch (error) {
            return false;
        }
    }
}

// Global API client instance
window.ApiClient = new ApiClient();

// Auto-check API connectivity on load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const isHealthy = await window.ApiClient.healthCheck();
        if (!isHealthy && window.AppConfig.isDevelopment()) {
            console.warn('⚠️ API health check failed - backend may not be running');
        }
    } catch (error) {
        if (window.AppConfig.isDevelopment()) {
            console.error('❌ Failed to check API health:', error);
        }
    }
});
