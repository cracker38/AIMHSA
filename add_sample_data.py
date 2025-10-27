#!/usr/bin/env python3
"""
Add Sample Data for Professional Dashboard Testing
"""

import sqlite3
import time
import json
from werkzeug.security import generate_password_hash

def add_sample_data():
    """Add sample users, sessions, and notifications for testing"""
    DB_FILE = "storage/conversations.db"
    
    print("📊 Adding sample data for professional dashboard...")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # Get the test professional (ID: 13)
        cur = conn.execute("SELECT id FROM professionals WHERE username = 'test_prof'")
        professional_row = cur.fetchone()
        
        if not professional_row:
            print("❌ Test professional not found")
            return False
            
        professional_id = professional_row[0]
        print(f"✅ Using test professional ID: {professional_id}")
        
        # Add sample users
        print("\n1️⃣ Adding sample users...")
        sample_users = [
            {
                "username": "testuser1",
                "email": "testuser1@example.com",
                "fullname": "Alice Mukamana",
                "telephone": "+250788123456",
                "province": "Kigali City",
                "district": "Gasabo"
            },
            {
                "username": "testuser2", 
                "email": "testuser2@example.com",
                "fullname": "Jean Ntwari",
                "telephone": "+250788234567",
                "province": "Kigali City",
                "district": "Nyarugenge"
            },
            {
                "username": "testuser3",
                "email": "testuser3@example.com", 
                "fullname": "Grace Umutoni",
                "telephone": "+250788345678",
                "province": "Southern Province",
                "district": "Huye"
            },
            {
                "username": "testuser4",
                "email": "testuser4@example.com",
                "fullname": "Claudine Nyiraneza", 
                "telephone": "+250788456789",
                "province": "Northern Province",
                "district": "Musanze"
            },
            {
                "username": "testuser5",
                "email": "testuser5@example.com",
                "fullname": "Peter Nkurunziza",
                "telephone": "+250788567890",
                "province": "Eastern Province", 
                "district": "Rwamagana"
            }
        ]
        
        for user in sample_users:
            try:
        conn.execute("""
                    INSERT OR REPLACE INTO users 
                    (username, password_hash, email, fullname, telephone, province, district, created_ts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
                    user["username"],
                    generate_password_hash("password123"),
                    user["email"],
                    user["fullname"],
                    user["telephone"],
                    user["province"],
                    user["district"],
                    time.time()
                ))
                print(f"   ✅ Added user: {user['fullname']} ({user['username']})")
            except Exception as e:
                print(f"   ⚠️ User {user['username']} already exists or error: {e}")
        
        conn.commit()
        
        # Add sample automated bookings (sessions)
        print("\n2️⃣ Adding sample sessions...")
        sample_sessions = [
            {
                "user_account": "testuser1",
                "risk_level": "high",
                "risk_score": 0.8,
                "booking_status": "pending",
                "notes": "",
                "conversation_summary": "Patient expressing feelings of hopelessness and isolation."
            },
            {
                "user_account": "testuser2", 
                "risk_level": "medium",
                "risk_score": 0.5,
                "booking_status": "confirmed",
                "notes": "Initial consultation completed. Patient shows signs of anxiety.",
                "conversation_summary": "Patient discussing work stress and relationship issues."
            },
            {
                "user_account": "testuser3",
                "risk_level": "critical", 
                "risk_score": 0.95,
                "booking_status": "pending",
                "notes": "",
                "conversation_summary": "Patient mentioned self-harm thoughts. Immediate intervention needed."
            },
            {
                "user_account": "testuser4",
                "risk_level": "low",
                "risk_score": 0.2,
                "booking_status": "confirmed", 
                "notes": "Patient responding well to treatment. Progress noted.",
                "conversation_summary": "Patient discussing positive changes and coping strategies."
            },
            {
                "user_account": "testuser5",
                "risk_level": "high",
                "risk_score": 0.75,
                "booking_status": "pending",
                "notes": "",
                "conversation_summary": "Patient experiencing severe depression and sleep issues."
            }
        ]
        
        for i, session in enumerate(sample_sessions):
            booking_id = f"booking_{professional_id}_{i+1}_{int(time.time())}"
            conv_id = f"conv_{i+1}_{int(time.time())}"
            conn.execute("""
                INSERT OR REPLACE INTO automated_bookings
                (booking_id, conv_id, user_account, professional_id, risk_level, risk_score, booking_status, 
                 notes, conversation_summary, created_ts, updated_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            booking_id,
            conv_id,
                session["user_account"],
            professional_id,
                session["risk_level"],
                session["risk_score"],
                session["booking_status"],
                session["notes"],
                session["conversation_summary"],
                time.time() - (i * 3600),  # Spread over time
                time.time() - (i * 3600)
            ))
            print(f"   ✅ Added session: {session['user_account']} - {session['risk_level']} - {session['booking_status']}")
        
        conn.commit()
        
        # Add sample notifications
        print("\n3️⃣ Adding sample notifications...")
        sample_notifications = [
            {
                "title": "New High Risk Session Assigned",
                "message": "A new high-risk patient has been assigned to you. Please review and accept the session.",
                "priority": "high",
                "is_read": 0,
                "notification_type": "session_assigned"
            },
            {
                "title": "Session Reminder",
                "message": "You have a session scheduled with Alice Mukamana in 30 minutes.",
                "priority": "medium", 
                "is_read": 0,
                "notification_type": "session_reminder"
            },
            {
                "title": "Patient Progress Update",
                "message": "Jean Ntwari has completed their weekly assessment. Review the progress notes.",
                "priority": "low",
                "is_read": 1,
                "notification_type": "progress_update"
            },
            {
                "title": "Critical Risk Alert",
                "message": "URGENT: Grace Umutoni has been flagged as critical risk. Immediate attention required.",
                "priority": "high",
                "is_read": 0,
                "notification_type": "risk_alert"
            },
            {
                "title": "Monthly Report Available",
                "message": "Your monthly professional report is ready for review.",
                "priority": "low",
                "is_read": 1,
                "notification_type": "report_available"
            }
        ]
        
        for i, notification in enumerate(sample_notifications):
            # Use the booking_id from the corresponding session
            booking_id = f"booking_{professional_id}_{i+1}_{int(time.time())}" if i < len(sample_sessions) else None
            conn.execute("""
                INSERT OR REPLACE INTO professional_notifications
                (professional_id, booking_id, title, message, priority, is_read, notification_type, created_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            professional_id,
            booking_id,
                notification["title"],
                notification["message"],
                notification["priority"],
                notification["is_read"],
                notification["notification_type"],
                time.time() - (i * 1800)  # Spread over time
            ))
            print(f"   ✅ Added notification: {notification['title']}")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("🎉 SAMPLE DATA ADDED SUCCESSFULLY!")
        print("✅ 5 sample users added")
        print("✅ 5 sample sessions added")
        print("✅ 5 sample notifications added")
        print("✅ Professional dashboard now has meaningful data")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    add_sample_data()
