#!/usr/bin/env python3
"""
Simple Database Initialization for AIMHSA
"""

import os
import sqlite3
import time
from werkzeug.security import generate_password_hash

# Database file path
DB_FILE = "storage/conversations.db"

def init_database():
    """Initialize database with all required tables"""
    
    print("Initializing AIMHSA Database...")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    
    try:
        current_time = time.time()
        
        # Create tables
        print("Creating tables...")
        
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_ts REAL NOT NULL,
                email TEXT,
                fullname TEXT,
                telephone TEXT,
                province TEXT,
                district TEXT
            )
        """)
        print("Users table created")
        
        # Professionals table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS professionals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                specialization TEXT NOT NULL,
                expertise_areas TEXT NOT NULL,
                languages TEXT NOT NULL,
                qualifications TEXT NOT NULL,
                district TEXT,
                consultation_fee REAL,
                experience_years INTEGER,
                bio TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_ts REAL NOT NULL,
                updated_ts REAL NOT NULL
            )
        """)
        print("Professionals table created")
        
        # Admin users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                created_ts REAL NOT NULL
            )
        """)
        print("Admin users table created")
        
        # Messages table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ts REAL NOT NULL
            )
        """)
        print("Messages table created")
        
        # Sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                conv_id TEXT NOT NULL,
                ts REAL NOT NULL
            )
        """)
        print("Sessions table created")
        
        # Conversations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conv_id TEXT PRIMARY KEY,
                owner_key TEXT,
                preview TEXT,
                ts REAL,
                archived INTEGER DEFAULT 0,
                archive_pw_hash TEXT,
                booking_prompt_shown INTEGER DEFAULT 0
            )
        """)
        print("Conversations table created")
        
        conn.commit()
        print("Database initialized successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False
    finally:
        conn.close()

def create_sample_users():
    """Create sample users for all types"""
    
    print("\nCreating sample users...")
    
    conn = sqlite3.connect(DB_FILE)
    
    try:
        current_time = time.time()
        
        # Create Regular Users
        print("Creating regular users...")
        
        regular_users = [
            ('testuser', 'testuser@example.com', 'password123', 'Test User', '+250788123456', 'Kigali', 'Gasabo'),
            ('john_doe', 'john.doe@example.com', 'password123', 'John Doe', '+250788234567', 'Kigali', 'Nyarugenge'),
            ('jane_smith', 'jane.smith@example.com', 'password123', 'Jane Smith', '+250788345678', 'Eastern', 'Kirehe'),
            ('rwanda_user', 'rwanda.user@example.com', 'password123', 'Rwanda User', '+250788456789', 'Southern', 'Huye')
        ]
        
        for username, email, password, fullname, telephone, province, district in regular_users:
            password_hash = generate_password_hash(password)
            conn.execute("""
                INSERT OR REPLACE INTO users (
                    username, password_hash, email, fullname, telephone, 
                    province, district, created_ts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, password_hash, email, fullname, telephone, province, district, current_time))
            print(f"  Created user: {fullname} ({email})")
        
        # Create Professionals
        print("Creating professionals...")
        
        professionals = [
            ('dr_mukamana', 'dr.mukamana@aimhsa.rw', 'password123', 'Marie', 'Mukamana', '+250788567890', 'Psychiatrist', 'Depression, Anxiety, PTSD', 'English, French, Kinyarwanda', 'MD Psychiatry', 'Kigali', 50000, 10),
            ('counselor_ntwari', 'jean.ntwari@aimhsa.rw', 'password123', 'Jean', 'Ntwari', '+250788678901', 'Counselor', 'Family Therapy, Youth Counseling', 'English, French, Kinyarwanda', 'MA Counseling Psychology', 'Kigali', 30000, 7),
            ('psychologist_umutoni', 'grace.umutoni@aimhsa.rw', 'password123', 'Grace', 'Umutoni', '+250788789012', 'Psychologist', 'Cognitive Behavioral Therapy, Trauma', 'English, French, Kinyarwanda', 'PhD Clinical Psychology', 'Kigali', 40000, 8),
            ('social_worker_nyiraneza', 'claudine.nyiraneza@aimhsa.rw', 'password123', 'Claudine', 'Nyiraneza', '+250788890123', 'Social Worker', 'Community Mental Health, Crisis Intervention', 'English, French, Kinyarwanda', 'MSW Social Work', 'Kigali', 25000, 6)
        ]
        
        for username, email, password, first_name, last_name, phone, specialization, expertise_areas, languages, qualifications, district, consultation_fee, experience_years in professionals:
            password_hash = generate_password_hash(password)
            conn.execute("""
                INSERT OR REPLACE INTO professionals (
                    username, password_hash, first_name, last_name, email, phone,
                    specialization, expertise_areas, languages, qualifications,
                    district, consultation_fee, experience_years, bio,
                    is_active, created_ts, updated_ts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username, password_hash, first_name, last_name, email, phone,
                specialization, expertise_areas, languages, qualifications,
                district, consultation_fee, experience_years,
                f"Experienced {specialization} with {experience_years} years of experience.",
                1, current_time, current_time
            ))
            print(f"  Created professional: Dr. {first_name} {last_name} ({email})")
        
        # Create Admin Users
        print("Creating admin users...")
        
        admin_users = [
            ('admin', 'admin@aimhsa.rw', 'admin123', 'admin'),
            ('eliasfeza@gmail.com', 'eliasfeza@gmail.com', 'EliasFeza@12301', 'admin'),
            ('superadmin', 'superadmin@aimhsa.rw', 'superadmin123', 'super_admin')
        ]
        
        for username, email, password, role in admin_users:
            password_hash = generate_password_hash(password)
            conn.execute("""
                INSERT OR REPLACE INTO admin_users (
                    username, password_hash, email, role, created_ts
                ) VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, email, role, current_time))
            print(f"  Created admin: {username} ({email})")
        
        conn.commit()
        print("\nAll users created successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error creating users: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    """Main function"""
    print("="*60)
    print("AIMHSA Database and User Setup")
    print("="*60)
    
    # Initialize database
    if init_database():
        # Create sample users
        if create_sample_users():
            print("\n" + "="*60)
            print("SETUP COMPLETE!")
            print("="*60)
            
            print("\nLOGIN CREDENTIALS:")
            print("\nRegular Users:")
            print("  testuser@example.com | password123")
            print("  john.doe@example.com | password123")
            print("  jane.smith@example.com | password123")
            print("  rwanda.user@example.com | password123")
            
            print("\nMental Health Professionals:")
            print("  dr.mukamana@aimhsa.rw | password123")
            print("  jean.ntwari@aimhsa.rw | password123")
            print("  grace.umutoni@aimhsa.rw | password123")
            print("  claudine.nyiraneza@aimhsa.rw | password123")
            
            print("\nAdmin Users:")
            print("  admin | admin123")
            print("  eliasfeza@gmail.com | EliasFeza@12301")
            print("  superadmin | superadmin123")
            
            print("\nNEXT STEPS:")
            print("  1. Start your AIMHSA server: python app.py")
            print("  2. Go to: http://localhost:7860/login")
            print("  3. Test login with any of the credentials above")
            print("  4. The system will automatically detect your user type")
            
        else:
            print("\nFailed to create users!")
    else:
        print("\nFailed to initialize database!")

if __name__ == "__main__":
    main()
