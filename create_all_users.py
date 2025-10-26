#!/usr/bin/env python3
"""
AIMHSA Complete User Setup Script
Creates sample users for all user types (admin, professional, regular users)
"""

import os
import sys
import sqlite3
import time
import hashlib
from werkzeug.security import generate_password_hash

# Database file path
DB_FILE = "storage/conversations.db"

def create_sample_users():
    """Create sample users for all user types"""
    
    print("="*60)
    print("🧠 AIMHSA COMPLETE USER SETUP")
    print("="*60)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    
    try:
        current_time = time.time()
        
        print("📝 Creating sample users...")
        
        # 1. Create Regular Users
        print("\n👤 Creating Regular Users:")
        
        regular_users = [
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'password123',
                'fullname': 'Test User',
                'telephone': '+250788123456',
                'province': 'Kigali',
                'district': 'Gasabo'
            },
            {
                'username': 'john_doe',
                'email': 'john.doe@example.com',
                'password': 'password123',
                'fullname': 'John Doe',
                'telephone': '+250788234567',
                'province': 'Kigali',
                'district': 'Nyarugenge'
            },
            {
                'username': 'jane_smith',
                'email': 'jane.smith@example.com',
                'password': 'password123',
                'fullname': 'Jane Smith',
                'telephone': '+250788345678',
                'province': 'Eastern',
                'district': 'Kirehe'
            },
            {
                'username': 'rwanda_user',
                'email': 'rwanda.user@example.com',
                'password': 'password123',
                'fullname': 'Rwanda User',
                'telephone': '+250788456789',
                'province': 'Southern',
                'district': 'Huye'
            }
        ]
        
        for user in regular_users:
            password_hash = generate_password_hash(user['password'])
            conn.execute("""
                INSERT OR REPLACE INTO users (
                    username, password_hash, email, fullname, telephone, 
                    province, district, created_ts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user['username'], password_hash, user['email'], 
                user['fullname'], user['telephone'], 
                user['province'], user['district'], current_time
            ))
            print(f"   ✅ {user['fullname']} ({user['email']}) - Password: {user['password']}")
        
        # 2. Create Professionals
        print("\n👨‍⚕️ Creating Mental Health Professionals:")
        
        professionals = [
            {
                'username': 'dr_mukamana',
                'email': 'dr.mukamana@aimhsa.rw',
                'password': 'password123',
                'first_name': 'Marie',
                'last_name': 'Mukamana',
                'phone': '+250788567890',
                'specialization': 'Psychiatrist',
                'expertise_areas': 'Depression, Anxiety, PTSD',
                'languages': 'English, French, Kinyarwanda',
                'qualifications': 'MD Psychiatry, PhD Clinical Psychology',
                'district': 'Kigali',
                'consultation_fee': 50000,
                'experience_years': 10
            },
            {
                'username': 'counselor_ntwari',
                'email': 'jean.ntwari@aimhsa.rw',
                'password': 'password123',
                'first_name': 'Jean',
                'last_name': 'Ntwari',
                'phone': '+250788678901',
                'specialization': 'Counselor',
                'expertise_areas': 'Family Therapy, Youth Counseling',
                'languages': 'English, French, Kinyarwanda',
                'qualifications': 'MA Counseling Psychology',
                'district': 'Kigali',
                'consultation_fee': 30000,
                'experience_years': 7
            },
            {
                'username': 'psychologist_umutoni',
                'email': 'grace.umutoni@aimhsa.rw',
                'password': 'password123',
                'first_name': 'Grace',
                'last_name': 'Umutoni',
                'phone': '+250788789012',
                'specialization': 'Psychologist',
                'expertise_areas': 'Cognitive Behavioral Therapy, Trauma',
                'languages': 'English, French, Kinyarwanda',
                'qualifications': 'PhD Clinical Psychology',
                'district': 'Kigali',
                'consultation_fee': 40000,
                'experience_years': 8
            },
            {
                'username': 'social_worker_nyiraneza',
                'email': 'claudine.nyiraneza@aimhsa.rw',
                'password': 'password123',
                'first_name': 'Claudine',
                'last_name': 'Nyiraneza',
                'phone': '+250788890123',
                'specialization': 'Social Worker',
                'expertise_areas': 'Community Mental Health, Crisis Intervention',
                'languages': 'English, French, Kinyarwanda',
                'qualifications': 'MSW Social Work',
                'district': 'Kigali',
                'consultation_fee': 25000,
                'experience_years': 6
            }
        ]
        
        for prof in professionals:
            password_hash = generate_password_hash(prof['password'])
            conn.execute("""
                INSERT OR REPLACE INTO professionals (
                    username, password_hash, first_name, last_name, email, phone,
                    specialization, expertise_areas, languages, qualifications,
                    district, consultation_fee, experience_years, bio,
                    is_active, created_ts, updated_ts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prof['username'], password_hash, prof['first_name'], prof['last_name'],
                prof['email'], prof['phone'], prof['specialization'], prof['expertise_areas'],
                prof['languages'], prof['qualifications'], prof['district'], 
                prof['consultation_fee'], prof['experience_years'],
                f"Experienced {prof['specialization']} with {prof['experience_years']} years of experience.",
                1, current_time, current_time
            ))
            print(f"   ✅ Dr. {prof['first_name']} {prof['last_name']} ({prof['email']}) - Password: {prof['password']}")
        
        # 3. Create Admin Users
        print("\n👑 Creating Admin Users:")
        
        admin_users = [
            {
                'username': 'admin',
                'email': 'admin@aimhsa.rw',
                'password': 'admin123',
                'role': 'admin'
            },
            {
                'username': 'eliasfeza@gmail.com',
                'email': 'eliasfeza@gmail.com',
                'password': 'EliasFeza@12301',
                'role': 'admin'
            },
            {
                'username': 'superadmin',
                'email': 'superadmin@aimhsa.rw',
                'password': 'superadmin123',
                'role': 'super_admin'
            }
        ]
        
        for admin in admin_users:
            password_hash = generate_password_hash(admin['password'])
            conn.execute("""
                INSERT OR REPLACE INTO admin_users (
                    username, password_hash, email, role, created_ts
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                admin['username'], password_hash, admin['email'], 
                admin['role'], current_time
            ))
            print(f"   ✅ {admin['username']} ({admin['email']}) - Password: {admin['password']}")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ ALL USERS CREATED SUCCESSFULLY!")
        print("="*60)
        
        print("\n🔐 LOGIN CREDENTIALS SUMMARY:")
        print("\n👤 Regular Users:")
        for user in regular_users:
            print(f"   Email: {user['email']} | Password: {user['password']}")
        
        print("\n👨‍⚕️ Mental Health Professionals:")
        for prof in professionals:
            print(f"   Email: {prof['email']} | Password: {prof['password']}")
        
        print("\n👑 Admin Users:")
        for admin in admin_users:
            print(f"   Username: {admin['username']} | Password: {admin['password']}")
        
        print("\n💡 LOGIN INSTRUCTIONS:")
        print("   1. Go to: http://localhost:7860/login")
        print("   2. Use any of the email addresses above")
        print("   3. Enter the corresponding password")
        print("   4. The system will automatically detect your user type")
        print("   5. You'll be redirected to the appropriate dashboard")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users: {str(e)}")
        return False
    finally:
        conn.close()

def test_login_endpoints():
    """Test all login endpoints"""
    print("\n🧪 Testing Login Endpoints...")
    
    import requests
    
    base_url = "http://localhost:7860"
    
    # Test data
    test_cases = [
        {
            'type': 'Regular User',
            'endpoint': '/api/login',
            'data': {'email': 'testuser@example.com', 'password': 'password123'}
        },
        {
            'type': 'Professional',
            'endpoint': '/professional/login',
            'data': {'email': 'dr.mukamana@aimhsa.rw', 'password': 'password123'}
        },
        {
            'type': 'Admin',
            'endpoint': '/admin/login',
            'data': {'username': 'admin', 'password': 'admin123'}
        }
    ]
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{base_url}{test_case['endpoint']}",
                json=test_case['data'],
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ {test_case['type']} login: SUCCESS")
            else:
                print(f"   ❌ {test_case['type']} login: FAILED ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ {test_case['type']} login: ERROR - {str(e)}")

def main():
    """Main function"""
    print("🚀 Starting AIMHSA Complete User Setup...")
    
    # Create all users
    if create_sample_users():
        print("\n🎉 User setup completed successfully!")
        
        # Test login endpoints if server is running
        try:
            test_login_endpoints()
        except Exception as e:
            print(f"\n⚠️  Could not test login endpoints: {str(e)}")
            print("   Make sure your AIMHSA server is running on localhost:7860")
        
        print("\n📋 NEXT STEPS:")
        print("   1. Start your AIMHSA server: python app.py")
        print("   2. Go to: http://localhost:7860/login")
        print("   3. Test login with any of the credentials above")
        print("   4. Verify you're redirected to the correct dashboard")
        
    else:
        print("\n❌ User setup failed!")

if __name__ == "__main__":
    main()
