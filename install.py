#!/usr/bin/env python3
"""
One-click installer for AIMHSA without Ollama
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✅ All packages installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        print("\n🔧 Try installing minimal requirements instead:")
        print("pip install -r requirements-minimal.txt")
        return False

def setup_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ['storage', 'data', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ {directory}/")

def initialize_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    
    try:
        subprocess.check_call([sys.executable, "init_database.py"])
        print("✅ Database initialized!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error initializing database: {e}")
        return False

def main():
    """Main installation process"""
    print("🚀 AIMHSA Installation (No Ollama Required)")
    print("=" * 50)
    
    # Step 1: Setup directories
    setup_directories()
    
    # Step 2: Install requirements
    if not install_requirements():
        return False
    
    # Step 3: Setup configuration
    try:
        from setup_without_ollama import setup_openai_compatible
        setup_openai_compatible()
    except ImportError:
        print("⚠️  Configuration setup not available. Please run setup_without_ollama.py manually.")
    
    # Step 4: Initialize database
    if not initialize_database():
        return False
    
    print("\n🎉 Installation complete!")
    print("\n🔑 Next steps:")
    print("1. Update your API keys in .env file")
    print("2. Run: python app.py")
    print("3. Open: https://fezaflora-aimhsa.hf.space")
    
    return True

if __name__ == "__main__":
    main()
