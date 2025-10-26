#!/usr/bin/env python3
"""
Setup script for AIMHSA without Ollama
Configures alternative AI providers
"""

import os
from dotenv import load_dotenv

def setup_openai_compatible():
    """Setup OpenAI-compatible API configuration"""
    print("🔧 Setting up OpenAI-compatible API configuration...")
    
    # Check if .env exists
    env_file = '.env'
    if not os.path.exists(env_file):
        print("Creating .env file...")
        with open(env_file, 'w') as f:
            f.write("# AIMHSA Configuration without Ollama\n\n")
    
    # Load existing environment
    load_dotenv()
    
    print("\nChoose your AI provider:")
    print("1. OpenAI GPT (Recommended)")
    print("2. Anthropic Claude")
    print("3. Google Gemini")
    print("4. Groq")
    print("5. Together AI")
    print("6. Cohere")
    print("7. Local Hugging Face Model")
    
    choice = input("\nEnter your choice (1-7): ").strip()
    
    config_lines = []
    
    if choice == "1":
        # OpenAI Configuration
        api_key = input("Enter your OpenAI API key: ").strip()
        model = input("Enter model name (default: gpt-3.5-turbo): ").strip() or "gpt-3.5-turbo"
        embed_model = input("Enter embedding model (default: text-embedding-ada-002): ").strip() or "text-embedding-ada-002"
        
        config_lines.extend([
            "# OpenAI Configuration",
            f"OPENAI_API_KEY={api_key}",
            "OLLAMA_BASE_URL=https://api.openai.com/v1",
            f"OLLAMA_API_KEY={api_key}",
            f"CHAT_MODEL={model}",
            f"EMBED_MODEL={embed_model}",
            f"SENT_EMBED_MODEL={embed_model}",
            ""
        ])
        
    elif choice == "2":
        # Anthropic Configuration
        api_key = input("Enter your Anthropic API key: ").strip()
        model = input("Enter model name (default: claude-3-sonnet-20240229): ").strip() or "claude-3-sonnet-20240229"
        
        config_lines.extend([
            "# Anthropic Configuration",
            f"ANTHROPIC_API_KEY={api_key}",
            "OLLAMA_BASE_URL=https://api.anthropic.com/v1",
            f"OLLAMA_API_KEY={api_key}",
            f"CHAT_MODEL={model}",
            "EMBED_MODEL=text-embedding-ada-002",
            "SENT_EMBED_MODEL=text-embedding-ada-002",
            "AI_PROVIDER=anthropic",
            ""
        ])
        
    elif choice == "3":
        # Google Gemini Configuration
        api_key = input("Enter your Google AI API key: ").strip()
        model = input("Enter model name (default: gemini-pro): ").strip() or "gemini-pro"
        
        config_lines.extend([
            "# Google AI Configuration",
            f"GOOGLE_AI_API_KEY={api_key}",
            "OLLAMA_BASE_URL=https://generativelanguage.googleapis.com/v1",
            f"OLLAMA_API_KEY={api_key}",
            f"CHAT_MODEL={model}",
            "EMBED_MODEL=text-embedding-ada-002",
            "SENT_EMBED_MODEL=text-embedding-ada-002",
            "AI_PROVIDER=google",
            ""
        ])
        
    elif choice == "4":
        # Groq Configuration
        api_key = input("Enter your Groq API key: ").strip()
        model = input("Enter model name (default: mixtral-8x7b-32768): ").strip() or "mixtral-8x7b-32768"
        
        config_lines.extend([
            "# Groq Configuration",
            f"GROQ_API_KEY={api_key}",
            "OLLAMA_BASE_URL=https://api.groq.com/openai/v1",
            f"OLLAMA_API_KEY={api_key}",
            f"CHAT_MODEL={model}",
            "EMBED_MODEL=text-embedding-ada-002",
            "SENT_EMBED_MODEL=text-embedding-ada-002",
            "AI_PROVIDER=groq",
            ""
        ])
        
    elif choice == "5":
        # Together AI Configuration
        api_key = input("Enter your Together AI API key: ").strip()
        model = input("Enter model name (default: meta-llama/Llama-2-70b-chat-hf): ").strip() or "meta-llama/Llama-2-70b-chat-hf"
        
        config_lines.extend([
            "# Together AI Configuration",
            f"TOGETHER_API_KEY={api_key}",
            "OLLAMA_BASE_URL=https://api.together.xyz/v1",
            f"OLLAMA_API_KEY={api_key}",
            f"CHAT_MODEL={model}",
            "EMBED_MODEL=text-embedding-ada-002",
            "SENT_EMBED_MODEL=text-embedding-ada-002",
            "AI_PROVIDER=together",
            ""
        ])
        
    elif choice == "6":
        # Cohere Configuration
        api_key = input("Enter your Cohere API key: ").strip()
        
        config_lines.extend([
            "# Cohere Configuration",
            f"COHERE_API_KEY={api_key}",
            "OLLAMA_BASE_URL=https://api.cohere.ai/v1",
            f"OLLAMA_API_KEY={api_key}",
            "CHAT_MODEL=command",
            "EMBED_MODEL=embed-english-v2.0",
            "SENT_EMBED_MODEL=embed-english-v2.0",
            "AI_PROVIDER=cohere",
            ""
        ])
        
    elif choice == "7":
        # Local Hugging Face Model
        model = input("Enter Hugging Face model name (default: microsoft/DialoGPT-medium): ").strip() or "microsoft/DialoGPT-medium"
        
        config_lines.extend([
            "# Local Hugging Face Configuration",
            "OLLAMA_BASE_URL=http://localhost:5000/v1",
            "OLLAMA_API_KEY=local",
            f"CHAT_MODEL={model}",
            "EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2",
            "SENT_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2",
            "AI_PROVIDER=huggingface",
            ""
        ])
        
    else:
        print("Invalid choice. Setting up with OpenAI defaults.")
        config_lines.extend([
            "# Default OpenAI Configuration",
            "OPENAI_API_KEY=your-openai-api-key-here",
            "OLLAMA_BASE_URL=https://api.openai.com/v1",
            "OLLAMA_API_KEY=your-openai-api-key-here",
            "CHAT_MODEL=gpt-3.5-turbo",
            "EMBED_MODEL=text-embedding-ada-002",
            "SENT_EMBED_MODEL=text-embedding-ada-002",
            ""
        ])
    
    # Add common configuration
    config_lines.extend([
        "# Server Configuration",
        "SERVER_HOST=0.0.0.0",
        "SERVER_PORT=7860",
        "FLASK_ENV=development",
        "DEBUG=True",
        "",
        "# Database Configuration",
        "DB_FILE=storage/conversations.db",
        "STORAGE_DIR=storage",
        "DATA_DIR=data",
        "",
        "# Email Configuration (Optional)",
        "SMTP_SERVER=smtp.gmail.com",
        "SMTP_PORT=587",
        "SMTP_USERNAME=your-email@gmail.com",
        "SMTP_PASSWORD=your-app-password",
        "FROM_EMAIL=noreply@aimhsa.rw",
        "",
        "# SMS Configuration (Optional)",
        "HDEV_SMS_API_ID=your-sms-api-id",
        "HDEV_SMS_API_KEY=your-sms-api-key",
        ""
    ])
    
    # Write configuration to .env file
    with open(env_file, 'a') as f:
        f.write('\n'.join(config_lines))
    
    print(f"\n✅ Configuration saved to {env_file}")
    print("\n🔑 Next steps:")
    print("1. Update your API keys in the .env file")
    print("2. Run: pip install -r requirements.txt")
    print("3. Run: python init_database.py")
    print("4. Run: python app.py")
    
def create_docker_compose():
    """Create docker-compose.yml for easy deployment"""
    docker_compose_content = """# filepath: c:\xampp\htdocs\Ai_Mental_Health_Chatbot\docker-compose.yml
version: '3.8'

services:
  aimhsa:
    build: .
    ports:
      - "7860:7860"
    environment:
      - FLASK_ENV=production
      - DEBUG=False
    volumes:
      - ./storage:/app/storage
      - ./data:/app/data
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./chatbot:/usr/share/nginx/html
    depends_on:
      - aimhsa
    restart: unless-stopped
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose_content)
    print("✅ Created docker-compose.yml")

def create_dockerfile():
    """Create Dockerfile for containerization"""
    dockerfile_content = """# filepath: c:\xampp\htdocs\Ai_Mental_Health_Chatbot\Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    tesseract-ocr \\
    poppler-utils \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p storage data

# Initialize database
RUN python init_database.py

# Expose port
EXPOSE 7860

# Run application
CMD ["python", "app.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    print("✅ Created Dockerfile")

if __name__ == "__main__":
    print("🚀 AIMHSA Setup Without Ollama")
    print("=" * 50)
    
    setup_openai_compatible()
    
    create_docker = input("\nCreate Docker configuration? (y/n): ").strip().lower()
    if create_docker == 'y':
        create_dockerfile()
        create_docker_compose()
    
    print("\n🎉 Setup complete!")
    print("Your AIMHSA application is now configured to run without Ollama.")
