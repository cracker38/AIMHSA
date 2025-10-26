#!/usr/bin/env python3
"""
Check and fix database
"""

import sqlite3
import os

DB_FILE = "storage/conversations.db"

def check_database():
    """Check database status"""
    print("🔍 Checking database...")
    
    if not os.path.exists(DB_FILE):
        print(f"❌ Database file not found: {DB_FILE}")
        return False
    
    try:
        conn = sqlite3.connect(DB_FILE)
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        
        print(f"✅ Database file exists: {DB_FILE}")
        print(f"📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table}")
        
        if len(tables) == 0:
            print("❌ No tables found - database is empty")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def fix_database():
    """Fix database by running init_database.py"""
    print("\n🔧 Fixing database...")
    
    # Remove empty database file
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"🗑️  Removed empty database file")
    
    # Run init_database.py
    import subprocess
    try:
        result = subprocess.run(['python', 'init_database.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            return True
        else:
            print(f"❌ Database initialization failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running init_database.py: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🧠 AIMHSA DATABASE CHECKER")
    print("="*50)
    
    if not check_database():
        if fix_database():
            print("\n✅ Database fixed! Now you can run create_all_users.py")
        else:
            print("\n❌ Failed to fix database")
    else:
        print("\n✅ Database is ready! You can run create_all_users.py")
