/**
 * Frontend Configuration Management
 * Centralized configuration for the AIMHSA chatbot frontend
 */

(() => {
    'use strict';

    // Default configuration
    const DEFAULT_CONFIG = {
        // API Configuration
        api: {
            baseUrl: window.location.origin,
            timeout: 10000,
            retryAttempts: 3,
            retryDelay: 1000
        },
        
        // UI Configuration
        ui: {
            theme: 'dark',
            language: 'en',
            autoRefreshInterval: 30000,
            animationDuration: 300
        },
        
        // Chat Configuration
        chat: {
            maxMessageLength: 5000,
            typingIndicatorDelay: 1000,
            autoScroll: true,
            saveConversations: true
        },
        
        // Professional Dashboard Configuration
        professional: {
            defaultPageSize: 25,
            autoRefreshBookings: true,
            notificationSound: true
        },
        
        // Admin Dashboard Configuration
        admin: {
            defaultPageSize: 50,
            enableDataExport: true,
            showAdvancedStats: true
        }
    };

    // Environment-specific configurations
    const ENVIRONMENT_CONFIGS = {
        development: { api: { baseUrl: window.location.origin } },
        production:  { api: { baseUrl: window.location.origin } },
        staging:     { api: { baseUrl: window.location.origin } }
    };

    class ConfigManager {
        constructor() {
            this.config = { ...DEFAULT_CONFIG };
            this.environment = this.detectEnvironment();
            this.loadConfiguration();
        }

        /**
         * Detect current environment
         */
        detectEnvironment() {
            const hostname = window.location.hostname;
            const port = window.location.port;
            
            if (hostname === 'localhost' || hostname === '127.0.0.1') {
                return 'development';
            } else if (hostname.includes('staging')) {
                return 'staging';
            } else {
                return 'production';
            }
        }

        /**
         * Load configuration from multiple sources
         */
        loadConfiguration() {
            try {
                // 1. Apply environment-specific config
                this.applyEnvironmentConfig();
                
                // 2. Load from localStorage (user preferences)
                this.loadFromLocalStorage();
                
                // 3. Load from URL parameters
                this.loadFromUrlParams();
                
                // 4. Auto-detect API URL based on current location
                this.autoDetectApiUrl();
                
                console.log('🔧 Configuration loaded:', this.config);
                
            } catch (error) {
                console.error('❌ Error loading configuration:', error);
                // Fallback to default config
                this.config = { ...DEFAULT_CONFIG };
            }
        }

        /**
         * Apply environment-specific configuration
         */
        applyEnvironmentConfig() {
            const envConfig = ENVIRONMENT_CONFIGS[this.environment];
            if (envConfig) {
                this.config = this.deepMerge(this.config, envConfig);
                console.log(`🌍 Applied ${this.environment} environment config`);
            }
        }

        /**
         * Load configuration from localStorage
         */
        loadFromLocalStorage() {
            try {
                const savedConfig = localStorage.getItem('aimhsa_config');
                if (savedConfig) {
                    const parsedConfig = JSON.parse(savedConfig);
                    this.config = this.deepMerge(this.config, parsedConfig);
                    console.log('💾 Loaded config from localStorage');
                }
            } catch (error) {
                console.warn('⚠️ Failed to load config from localStorage:', error);
            }
        }

        /**
         * Load configuration from URL parameters
         */
        loadFromUrlParams() {
            const urlParams = new URLSearchParams(window.location.search);
            
            // API Base URL override
            const apiUrl = urlParams.get('api_url') || urlParams.get('baseUrl');
            if (apiUrl) {
                this.config.api.baseUrl = apiUrl;
                console.log('🔗 API URL overridden from URL params:', apiUrl);
            }
            
            // Environment override
            const env = urlParams.get('env') || urlParams.get('environment');
            if (env && ENVIRONMENT_CONFIGS[env]) {
                this.environment = env;
                this.applyEnvironmentConfig();
                console.log('🌍 Environment overridden from URL params:', env);
            }
            
            // Theme override
            const theme = urlParams.get('theme');
            if (theme) {
                this.config.ui.theme = theme;
                console.log('🎨 Theme overridden from URL params:', theme);
            }
        }

        /**
         * Auto-detect API URL based on current page location
         */
        autoDetectApiUrl() {
            const currentLocation = window.location;
            
            // Smart API URL detection
            if (currentLocation.port === '8000') {
                // Development server (likely Python/Django)
                this.config.api.baseUrl = `${currentLocation.protocol}//${currentLocation.hostname}:7860`;
            } else if (currentLocation.port === '3000') {
                // React development server
                this.config.api.baseUrl = `${currentLocation.protocol}//${currentLocation.hostname}:7860`;
            } else if (currentLocation.port === '7860') {
                // Running on API port
                this.config.api.baseUrl = currentLocation.origin;
            } else if (currentLocation.port === '80' || currentLocation.port === '443' || !currentLocation.port) {
                // Production environment
                this.config.api.baseUrl = currentLocation.origin;
            }
            
            console.log('🔍 Auto-detected API URL:', this.config.api.baseUrl);
        }

        /**
         * Get configuration value
         */
        get(path, defaultValue = null) {
            return this.getNestedValue(this.config, path, defaultValue);
        }

        /**
         * Set configuration value
         */
        set(path, value) {
            this.setNestedValue(this.config, path, value);
            this.saveToLocalStorage();
        }

        /**
         * Get API base URL
         */
        getApiBaseUrl() {
            return this.config.api.baseUrl;
        }

        /**
         * Set API base URL
         */
        setApiBaseUrl(url) {
            this.config.api.baseUrl = url;
            this.saveToLocalStorage();
            console.log('🔗 API Base URL updated:', url);
        }

        /**
         * Get full API URL for an endpoint
         */
        getApiUrl(endpoint = '') {
            const baseUrl = this.config.api.baseUrl;
            const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
            return `${baseUrl}${cleanEndpoint}`;
        }

        /**
         * Save current configuration to localStorage
         */
        saveToLocalStorage() {
            try {
                localStorage.setItem('aimhsa_config', JSON.stringify(this.config));
                console.log('💾 Configuration saved to localStorage');
            } catch (error) {
                console.warn('⚠️ Failed to save config to localStorage:', error);
            }
        }

        /**
         * Reset configuration to defaults
         */
        reset() {
            this.config = { ...DEFAULT_CONFIG };
            localStorage.removeItem('aimhsa_config');
            this.loadConfiguration();
            console.log('🔄 Configuration reset to defaults');
        }

        /**
         * Deep merge objects
         */
        deepMerge(target, source) {
            const result = { ...target };
            
            for (const key in source) {
                if (source.hasOwnProperty(key)) {
                    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                        result[key] = this.deepMerge(result[key] || {}, source[key]);
                    } else {
                        result[key] = source[key];
                    }
                }
            }
            
            return result;
        }

        /**
         * Get nested object value by path
         */
        getNestedValue(obj, path, defaultValue = null) {
            const keys = path.split('.');
            let current = obj;
            
            for (const key of keys) {
                if (current && current.hasOwnProperty(key)) {
                    current = current[key];
                } else {
                    return defaultValue;
                }
            }
            
            return current;
        }

        /**
         * Set nested object value by path
         */
        setNestedValue(obj, path, value) {
            const keys = path.split('.');
            let current = obj;
            
            for (let i = 0; i < keys.length - 1; i++) {
                const key = keys[i];
                if (!current[key] || typeof current[key] !== 'object') {
                    current[key] = {};
                }
                current = current[key];
            }
            
            current[keys[keys.length - 1]] = value;
        }

        /**
         * Validate API connection
         */
        async validateApiConnection() {
            try {
                const response = await fetch(`${this.config.api.baseUrl}/health`, {
                    method: 'GET',
                    timeout: this.config.api.timeout
                });
                
                if (response.ok) {
                    console.log('✅ API connection validated');
                    return true;
                } else {
                    console.warn('⚠️ API responded but not healthy:', response.status);
                    return false;
                }
            } catch (error) {
                console.error('❌ API connection failed:', error);
                return false;
            }
        }

        /**
         * Get environment info
         */
        getEnvironmentInfo() {
            return {
                environment: this.environment,
                hostname: window.location.hostname,
                port: window.location.port,
                protocol: window.location.protocol,
                apiBaseUrl: this.config.api.baseUrl,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            };
        }
    }

    // Create global configuration manager instance
    const configManager = new ConfigManager();

    // Export to global scope
    window.AIMHSA = window.AIMHSA || {};
    window.AIMHSA.Config = configManager;
    
    // Legacy support
    window.getApiBaseUrl = () => configManager.getApiBaseUrl();
    window.getApiUrl = (endpoint) => configManager.getApiUrl(endpoint);
    
    console.log('⚙️ AIMHSA Configuration Manager initialized');
    console.log('🌍 Environment:', configManager.environment);
    console.log('🔗 API Base URL:', configManager.getApiBaseUrl());

})();
