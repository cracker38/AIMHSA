"""
AIMHSA Configuration Management
Handles environment-specific configuration for hosting
"""

import os
from dotenv import load_dotenv

# Load environment variables (override=True ensures .env values override system env)
load_dotenv(override=True)

class Config:
    """Base configuration class"""
    
    # Server Configuration
    HOST = os.getenv('SERVER_HOST', '0.0.0.0')
    PORT = int(os.getenv('SERVER_PORT', '7860'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # API Configuration
    API_BASE_URL = os.getenv('API_BASE_URL', '')  # Empty means relative URLs
    FRONTEND_URL = os.getenv('FRONTEND_URL', '')  # Empty means same origin
    
    # Database Configuration
    DB_FILE = os.getenv('DB_FILE', 'storage/conversations.db')
    
    # Ollama/OpenRouter Configuration
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'https://openrouter.ai/api/v1')
    OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', '')
    
    # AI Models (OpenRouter defaults)
    CHAT_MODEL = os.getenv('CHAT_MODEL', 'meta-llama/llama-3.1-8b-instruct')
    EMBED_MODEL = os.getenv('EMBED_MODEL', 'openai/text-embedding-3-small')
    SENT_EMBED_MODEL = os.getenv('SENT_EMBED_MODEL', 'openai/text-embedding-3-small')
    
    # Email Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@aimhsa.rw')
    
    # SMS Configuration
    HDEV_SMS_API_ID = os.getenv('HDEV_SMS_API_ID', '')
    HDEV_SMS_API_KEY = os.getenv('HDEV_SMS_API_KEY', '')
    
    # Storage Configuration
    STORAGE_DIR = os.getenv('STORAGE_DIR', 'storage')
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    EMBED_FILE = os.path.join(STORAGE_DIR, 'embeddings.json')

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 7860

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', '8000'))  # Common for hosting services

class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    HOST = '127.0.0.1'
    PORT = 5058
    DB_FILE = 'test_conversations.db'

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)

# Export current config
current_config = get_config()
