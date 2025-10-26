/**
 * Frontend Configuration for AIMHSA
 * Handles API endpoints and environment-specific settings
 */

class AppConfig {
    constructor() {
        // Detect environment
        this.environment = this.detectEnvironment();
        
        // Set API base URL based on environment
        this.apiBaseUrl = this.getApiBaseUrl();
        
        // API endpoints
        this.endpoints = {
            // Chat endpoints
            ask: '/ask',
            session: '/session',
            history: '/history',
            conversations: '/conversations',
            
            // User endpoints
            register: '/register',
            login: '/login',
            logout: '/logout',
            forgotPassword: '/forgot_password',
            resetPassword: '/reset_password',
            
            // Professional endpoints
            professionalLogin: '/professional/login',
            professionalProfile: '/professional/profile',
            professionalSessions: '/professional/sessions',
            professionalUsers: '/professional/users',
            professionalNotifications: '/professional/notifications',
            professionalDashboard: '/professional/dashboard-stats',
            
            // Admin endpoints
            adminLogin: '/admin/login',
            adminProfessionals: '/admin/professionals',
            adminBookings: '/admin/bookings',
            adminUsers: '/admin/users',
            
            // Utility endpoints
            uploadPdf: '/upload_pdf',
            clearChat: '/clear_chat',
            reset: '/reset',
            healthz: '/healthz'
        };
        
        // App settings
        this.settings = {
            defaultTimeout: 30000,
            maxRetries: 3,
            debounceDelay: 300,
            autoSaveDelay: 1000
        };
    }
    
    detectEnvironment() {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        const port = window.location.port;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'development';
        } else if (hostname.includes('test') || hostname.includes('staging')) {
            return 'testing';
        } else {
            return 'production';
        }
    }
    
    getApiBaseUrl() {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        const port = window.location.port;
        
        // Check if API_BASE_URL is set in environment
        if (window.API_BASE_URL) {
            return window.API_BASE_URL;
        }
        
        // Environment-specific API URLs
        switch (this.environment) {
            case 'development':
                // In development, API might be on different port
                if (port === '8000' || port === '3000') {
                    return `${protocol}//${hostname}:7860`;
                }
                return ''; // Same origin
                
            case 'testing':
                return ''; // Same origin for testing
                
            case 'production':
                // In production, use same origin (standard hosting setup)
                return '';
                
            default:
                return '';
        }
    }
    
    getFullUrl(endpoint) {
        const baseUrl = this.apiBaseUrl;
        const path = this.endpoints[endpoint] || endpoint;
        
        if (baseUrl) {
            return `${baseUrl}${path}`;
        } else {
            return path; // Relative URL
        }
    }
    
    // Convenience methods for common endpoints
    getChatUrl() { return this.getFullUrl('ask'); }
    getLoginUrl() { return this.getFullUrl('login'); }
    getRegisterUrl() { return this.getFullUrl('register'); }
    getProfessionalLoginUrl() { return this.getFullUrl('professionalLogin'); }
    getAdminLoginUrl() { return this.getFullUrl('adminLogin'); }
    
    // Environment checks
    isDevelopment() { return this.environment === 'development'; }
    isProduction() { return this.environment === 'production'; }
    isTesting() { return this.environment === 'testing'; }
}

// Global configuration instance
window.AppConfig = new AppConfig();

// Debug information in development
if (window.AppConfig.isDevelopment()) {
    console.log('🔧 AIMHSA Development Mode');
    console.log('API Base URL:', window.AppConfig.apiBaseUrl);
    console.log('Environment:', window.AppConfig.environment);
}
