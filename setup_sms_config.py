#!/usr/bin/env python3
"""
AIMHSA SMS Configuration Setup Script
This script helps you configure SMS service properly.
"""

import os

def create_env_file():
    """Create .env file with SMS credentials"""
    
    print("🔧 Setting up AIMHSA SMS configuration...")
    
    # Your SMS credentials
    api_id = "HDEV-87743753-35bb-45da-8103-37d4bb6bfeb6-ID"
    api_key = "HDEV-d07e9d3e-6d1a-4863-84e8-2d43f0a0b64a-KEY"
    
    env_content = f"""# AIMHSA Environment Configuration
# Copy this file and update with your actual credentials

# Environment
FLASK_ENV=development
DEBUG=True

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=7860

# API Configuration
API_BASE_URL=
FRONTEND_URL=

# Database Configuration
DB_FILE=storage/conversations.db
STORAGE_DIR=storage
DATA_DIR=data

# AI Configuration
CHAT_MODEL=llama3.2:3b
EMBED_MODEL=nomic-embed-text
SENT_EMBED_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama

# Email Configuration (UPDATE WITH YOUR VALUES)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=it.elias38@gmail.com
SMTP_PASSWORD=your-app-password-here
FROM_EMAIL=noreply@aimhsa.rw

# SMS Configuration (YOUR CREDENTIALS)
HDEV_SMS_API_ID={api_id}
HDEV_SMS_API_KEY={api_key}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print(f"📱 SMS API ID: {api_id}")
        print(f"🔑 SMS API Key: {api_key[:10]}...")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {str(e)}")
        return False

def verify_sms_setup():
    """Verify SMS setup is correct"""
    print("\n🔍 Verifying SMS setup...")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_id = os.getenv('HDEV_SMS_API_ID')
    api_key = os.getenv('HDEV_SMS_API_KEY')
    
    if api_id and api_key:
        print("✅ SMS credentials found in .env file")
        print(f"   API ID: {api_id}")
        print(f"   API Key: {api_key[:10]}...")
        return True
    else:
        print("❌ SMS credentials not found in .env file")
        return False

def main():
    print("="*60)
    print("AIMHSA SMS Configuration Setup")
    print("="*60)
    
    # Create .env file
    if create_env_file():
        print("\n✅ Configuration file created successfully!")
        
        # Verify setup
        if verify_sms_setup():
            print("\n🎉 SMS configuration is ready!")
            print("\n📋 Next steps:")
            print("   1. Restart your AIMHSA application")
            print("   2. Run: python test_sms_fix.py")
            print("   3. Test booking a session to trigger SMS")
        else:
            print("\n❌ Configuration verification failed")
    else:
        print("\n❌ Failed to create configuration file")

if __name__ == "__main__":
    main()
