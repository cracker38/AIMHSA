#!/usr/bin/env python3
"""
AIMHSA Unified Launcher
Runs both backend API and frontend on a single port using Flask
"""

import os
import sys
import time
import webbrowser
import argparse
import re
import uuid
import sqlite3
import json
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, render_template_string, send_file
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import tempfile
import pytesseract
from werkzeug.utils import secure_filename

# Import SMS service
try:
    from sms_service import get_sms_service
except ImportError:
    def get_sms_service():
        return None

# Database helper functions
def load_history(conv_id):
    """Load conversation history from database"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT role, content, ts FROM messages WHERE conv_id = ? ORDER BY ts", (conv_id,))
        rows = cur.fetchall()
        return [{"role": row[0], "content": row[1], "timestamp": row[2]} for row in rows]
    except Exception as e:
        app.logger.error(f"Error loading history: {e}")
        return []
    finally:
        conn.close()

def load_attachments(conv_id):
    """Load attachments for a conversation"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT filename, text FROM attachments WHERE conv_id = ?", (conv_id,))
        rows = cur.fetchall()
        return [{"filename": row[0], "text": row[1]} for row in rows]
    except Exception as e:
        app.logger.error(f"Error loading attachments: {e}")
        return []
    finally:
        conn.close()

def list_conversations(owner_key):
    """List conversations for a user"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT conv_id, preview, ts FROM conversations WHERE owner_key = ? ORDER BY ts DESC", (owner_key,))
        rows = cur.fetchall()
        return [{"id": row[0], "preview": row[1], "timestamp": row[2]} for row in rows]
    except Exception as e:
        app.logger.error(f"Error listing conversations: {e}")
        return []
    finally:
        conn.close()

def create_conversation(owner_key, preview="New chat"):
    """Create a new conversation"""
    conv_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("INSERT INTO conversations (conv_id, owner_key, preview, ts) VALUES (?, ?, ?, ?)", 
                    (conv_id, owner_key, preview, time.time()))
        conn.commit()
        return conv_id
    except Exception as e:
        app.logger.error(f"Error creating conversation: {e}")
        conn.rollback()
        return str(uuid.uuid4())  # Fallback
    finally:
        conn.close()

# Load environment variables
load_dotenv()

# Configuration
EMBED_FILE = "storage/embeddings.json"
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DB_FILE = "storage/conversations.db"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")

# SMS Configuration
HDEV_SMS_API_ID = os.getenv('HDEV_SMS_API_ID', '')
HDEV_SMS_API_KEY = os.getenv('HDEV_SMS_API_KEY', '')

# Get port from .env, fallback to 8000
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client for Ollama (fallback to Hugging Face compatible)
try:
    openai_client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=OLLAMA_API_KEY
    )
    print("✅ Using Ollama OpenAI client")
except Exception as e:
    print(f"⚠️ Ollama not available: {e}")
    # Fallback to Hugging Face compatible client
    try:
        from hf_ai_service import get_ai_service
        ai_service = get_ai_service()
        openai_client = None  # Will use ai_service instead
        print("✅ Using Hugging Face AI service")
    except Exception as hf_error:
        print(f"❌ Hugging Face AI service failed: {hf_error}")
        ai_service = None

# Initialize SMS service if credentials are provided
if HDEV_SMS_API_ID and HDEV_SMS_API_KEY:
    try:
        from sms_service import initialize_sms_service
        initialize_sms_service(HDEV_SMS_API_ID, HDEV_SMS_API_KEY)
        print(f"✅ SMS service initialized successfully")
    except Exception as e:
        print(f"⚠️ SMS service initialization failed: {str(e)}")
else:
    print("⚠️ SMS credentials not found - SMS notifications disabled")

# System prompt for AIMHSA
SYSTEM_PROMPT = """You are AIMHSA, a professional mental health support assistant for Rwanda.

## CRITICAL SCOPE ENFORCEMENT - REJECT OFF-TOPIC QUERIES
- You ONLY provide mental health, emotional well-being, and psychological support
- IMMEDIATELY REJECT any questions about: technology, politics, sports, entertainment, cooking, general knowledge, science, business, or any non-mental health topics
- For rejected queries, respond with: "I'm a mental health support assistant and can only help with emotional well-being and mental health concerns. Let's focus on how you're feeling today - is there anything causing you stress, anxiety, or affecting your mood?"
- NEVER provide detailed answers to non-mental health questions
- Always redirect to mental health topics after rejection

## Professional Guidelines
- Be warm, empathetic, and culturally sensitive
- Provide evidence-based information from the context when available
- Do NOT diagnose or prescribe medications
- Encourage professional care when appropriate
- For emergencies, always mention Rwanda's Mental Health Hotline: 105
- Keep responses professional, concise, and helpful
- Use the provided context to give accurate, relevant information
- Maintain a natural, conversational tone
- Ensure professional mental health support standards

Remember: You are a professional mental health support system. ALWAYS enforce scope boundaries by rejecting non-mental health queries and redirecting to emotional well-being topics.
"""

# Global variables for embeddings
chunk_texts = []
chunk_sources = []
chunk_embeddings = None

def init_storage():
    """Initialize database and load embeddings"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(EMBED_FILE), exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ts REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                text TEXT NOT NULL,
                ts REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                conv_id TEXT NOT NULL,
                ts REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                fullname TEXT,
                telephone TEXT,
                province TEXT,
                district TEXT,
                created_ts REAL NOT NULL
            )
        """)
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
        
        # Add missing tables for full functionality
        conn.execute("""
            CREATE TABLE IF NOT EXISTS professionals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                specialization TEXT NOT NULL,
                expertise_areas TEXT,
                languages TEXT,
                qualifications TEXT,
                district TEXT,
                consultation_fee REAL,
                experience_years INTEGER DEFAULT 0,
                bio TEXT,
                created_ts REAL NOT NULL,
                updated_ts REAL NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS automated_bookings (
                booking_id TEXT PRIMARY KEY,
                conv_id TEXT NOT NULL,
                user_account TEXT,
                professional_id INTEGER,
                risk_level TEXT,
                risk_score REAL,
                detected_indicators TEXT,
                conversation_summary TEXT,
                booking_status TEXT DEFAULT 'pending',
                scheduled_datetime REAL,
                session_type TEXT,
                session_notes TEXT,
                treatment_plan TEXT,
                notes TEXT,
                created_ts REAL NOT NULL,
                updated_ts REAL NOT NULL,
                FOREIGN KEY (professional_id) REFERENCES professionals(id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS professional_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professional_id INTEGER NOT NULL,
                booking_id TEXT,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                is_read INTEGER DEFAULT 0,
                risk_level TEXT,
                created_ts REAL NOT NULL,
                FOREIGN KEY (professional_id) REFERENCES professionals(id),
                FOREIGN KEY (booking_id) REFERENCES automated_bookings(booking_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT NOT NULL,
                user_query TEXT NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                detected_indicators TEXT NOT NULL,
                assessment_timestamp REAL NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                token TEXT NOT NULL,
                expires_ts REAL NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'admin',
                created_ts REAL NOT NULL
            )
        """)
        
        conn.commit()
    finally:
        conn.close()
    
    # Load embeddings with error handling
    global chunk_texts, chunk_sources, chunk_embeddings
    try:
        with open(EMBED_FILE, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        chunk_texts = [c["text"] for c in chunks_data]
        chunk_sources = [{"source": c["source"], "chunk": c["chunk"]} for c in chunks_data]
        chunk_embeddings = np.array([c["embedding"] for c in chunks_data], dtype=np.float32)
        print(f"✅ Loaded {len(chunk_texts)} embedding chunks")
    except FileNotFoundError:
        print("⚠️ Embeddings file not found - RAG features disabled")
        chunk_texts = []
        chunk_sources = []
        chunk_embeddings = None
    except Exception as e:
        print(f"⚠️ Error loading embeddings: {e}")
        chunk_texts = []
        chunk_sources = []
        chunk_embeddings = None

def cosine_similarity(a, b):
    """Calculate cosine similarity between embeddings"""
    a_norm = a / np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    return np.dot(a_norm, b_norm.T)

def retrieve(query: str, k: int = 4):
    """Retrieve relevant chunks using embeddings"""
    if chunk_embeddings is None:
        return []
    
    try:
        # Use available embedding service
        if openai_client:
            # Use OpenAI client for embeddings
            response = openai_client.embeddings.create(
                model=EMBED_MODEL,
                input=query
            )
            q_emb = np.array([response.data[0].embedding], dtype=np.float32)
        elif ai_service:
            # Use Hugging Face embeddings (simplified fallback)
            # For now, return empty to avoid errors
            return []
        else:
            return []
            
        sims = cosine_similarity(chunk_embeddings, q_emb)[:,0]
        top_idx = sims.argsort()[-k:][::-1]
        return [(chunk_texts[i], chunk_sources[i]) for i in top_idx]
    except Exception as e:
        print(f"Error in retrieve: {e}")
        return []

def build_context(snippets):
    """Build context from retrieved snippets"""
    lines = []
    for i, (doc, meta) in enumerate(snippets, 1):
        src = f"{meta.get('source','unknown')}#chunk{meta.get('chunk')}"
        lines.append(f"[{i}] ({src}) {doc}")
    return "\n\n".join(lines)

def save_message(conv_id: str, role: str, content: str):
    """Save message to database"""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute(
            "INSERT INTO messages (conv_id, role, content, ts) VALUES (?, ?, ?, ?)",
            (conv_id, role, content, time.time()),
        )
        conn.commit()
    finally:
        conn.close()

def load_history(conv_id: str):
    """Load conversation history"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute(
            "SELECT role, content FROM messages WHERE conv_id = ? ORDER BY id ASC",
            (conv_id,),
        )
        rows = cur.fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]
    finally:
        conn.close()

# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve main chat interface"""
    return send_from_directory('chatbot', 'index.html')

@app.route('/landing')
@app.route('/landing.html')
def landing():
    """Serve landing page"""
    return send_from_directory('chatbot', 'landing.html')

@app.route('/login')
@app.route('/login.html')
def login():
    """Serve login page"""
    return send_from_directory('chatbot', 'login.html')

@app.route('/favicon.ico')
def favicon():
    return send_file('favicon.svg', mimetype='image/svg+xml')

@app.route('/register')
@app.route('/register.html')
def register():
    """Serve registration page"""
    return send_from_directory('chatbot', 'register.html')

@app.route('/admin_dashboard.html')
def admin_dashboard():
    """Serve admin dashboard"""
    return send_from_directory('chatbot', 'admin_dashboard.html')

@app.route('/professional_dashboard.html')
def professional_dashboard():
    """Serve professional dashboard"""
    return send_from_directory('chatbot', 'professional_dashboard.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, etc.)"""
    return send_from_directory('chatbot', filename)

# ============================================================================
# RISK ASSESSMENT AND AUTOMATED BOOKING FUNCTIONS
# ============================================================================

def assess_conversation_risk(query: str, conversation_history: list) -> dict:
    """Assess risk level based on user query and conversation history"""
    risk_score = 0.0
    detected_indicators = []
    
    # Critical risk indicators
    critical_patterns = [
        r'\b(suicide|kill myself|end my life|not worth living)\b',
        r'\b(harm myself|hurt myself|self harm)\b',
        r'\b(plan to die|want to die|ready to die)\b',
        r'\b(overdose|poison|jump|hang)\b'
    ]
    
    # High risk indicators
    high_patterns = [
        r'\b(depressed|hopeless|worthless|useless)\b',
        r'\b(anxiety|panic|overwhelmed|can\'t cope)\b',
        r'\b(isolated|alone|nobody cares|no one understands)\b',
        r'\b(stress|pressure|breaking down|falling apart)\b'
    ]
    
    # Medium risk indicators
    medium_patterns = [
        r'\b(sad|upset|worried|concerned)\b',
        r'\b(sleep|eating|energy|motivation)\b',
        r'\b(relationship|family|work|school)\b'
    ]
    
    query_lower = query.lower()
    
    # Check for critical patterns
    for pattern in critical_patterns:
        if re.search(pattern, query_lower):
            risk_score += 0.8
            detected_indicators.append('critical_risk')
            break
    
    # Check for high patterns
    for pattern in high_patterns:
        if re.search(pattern, query_lower):
            risk_score += 0.4
            detected_indicators.append('high_risk')
    
    # Check for medium patterns
    for pattern in medium_patterns:
        if re.search(pattern, query_lower):
            risk_score += 0.2
            detected_indicators.append('medium_risk')
    
    # Analyze conversation history for patterns
    if len(conversation_history) > 3:
        recent_messages = conversation_history[-3:]
        negative_sentiment_count = 0
        
        for msg in recent_messages:
            content = msg.get('content', '').lower()
            if any(word in content for word in ['bad', 'terrible', 'awful', 'hate', 'can\'t', 'won\'t']):
                negative_sentiment_count += 1
        
        if negative_sentiment_count >= 2:
            risk_score += 0.3
            detected_indicators.append('persistent_negative')
    
    # Normalize score to 0-1 range
    risk_score = min(1.0, risk_score)
    
    # Determine risk level
    if risk_score >= 0.8:
        risk_level = 'critical'
    elif risk_score >= 0.6:
        risk_level = 'high'
    elif risk_score >= 0.4:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'detected_indicators': list(set(detected_indicators)),
        'assessment_timestamp': time.time()
    }

def find_available_professional(risk_level: str, user_location: str = None) -> dict:
    """Find an available professional based on risk level and location"""
    conn = sqlite3.connect(DB_FILE)
    try:
        # Determine required specialization based on risk level
        if risk_level in ['critical', 'high']:
            # For critical/high risk, prefer psychiatrist or psychologist, but also accept counselor
            specialization_filter = "specialization IN ('psychiatrist', 'psychologist', 'counselor')"
        else:
            # For medium/low risk, any mental health professional
            specialization_filter = "specialization IN ('psychiatrist', 'psychologist', 'counselor', 'social_worker')"
        
        # Enhanced query with location matching and better prioritization
        query = f"""
            SELECT id, username, first_name, last_name, email, phone, 
                   specialization, district, consultation_fee, experience_years,
                   expertise_areas, languages, qualifications, bio
            FROM professionals 
            WHERE is_active = 1 AND {specialization_filter}
            ORDER BY 
                CASE 
                    WHEN specialization IN ('psychiatrist', 'psychologist') THEN 1
                    WHEN specialization = 'counselor' THEN 2
                    ELSE 3
                END,
                CASE 
                    WHEN district = ? THEN 1
                    ELSE 2
                END,
                experience_years DESC, RANDOM()
            LIMIT 1
        """
        
        # Use user location if provided, otherwise use empty string
        location_param = user_location if user_location else ""
        
        cur = conn.execute(query, (location_param,))
        professional = cur.fetchone()
        
        if professional:
            selected_prof = {
                'id': professional[0],
                'username': professional[1],
                'first_name': professional[2],
                'last_name': professional[3],
                'email': professional[4],
                'phone': professional[5],
                'specialization': professional[6],
                'district': professional[7],
                'consultation_fee': professional[8],
                'experience_years': professional[9],
                'expertise_areas': professional[10],
                'languages': professional[11],
                'qualifications': professional[12],
                'bio': professional[13]
            }
            
            # Log selection details
            print(f"✅ Selected Professional: {selected_prof['first_name']} {selected_prof['last_name']}")
            print(f"   Specialization: {selected_prof['specialization']}")
            print(f"   District: {selected_prof['district']}")
            print(f"   Experience: {selected_prof['experience_years']} years")
            print(f"   Risk Level: {risk_level}")
            print(f"   User Location: {user_location or 'Not specified'}")
            
            return selected_prof
        return None
    finally:
        conn.close()

def get_user_data(username: str) -> dict:
    """Get user data for SMS notifications"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("""
            SELECT username, email, fullname, telephone, province, district
            FROM users WHERE username = ?
        """, (username,))
        user = cur.fetchone()
        
        if user:
            return {
                'username': user[0],
                'email': user[1] or 'Not provided',
                'fullname': user[2] or username,
                'telephone': user[3] or 'Not provided',
                'province': user[4] or 'Unknown',
                'district': user[5] or 'Unknown'
            }
        return None
    finally:
        conn.close()

def generate_conversation_summary(conv_id: str) -> str:
    """Generate a summary of the conversation for the professional"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("""
            SELECT role, content FROM messages 
            WHERE conv_id = ? 
            ORDER BY ts ASC 
            LIMIT 10
        """, (conv_id,))
        messages = cur.fetchall()
        
        summary_parts = []
        for role, content in messages:
            if role == 'user':
                summary_parts.append(f"User: {content[:100]}...")
            elif role == 'assistant':
                summary_parts.append(f"Assistant: {content[:100]}...")
        
        return " | ".join(summary_parts[:5])  # Limit to 5 messages
    finally:
        conn.close()

def create_automated_booking(conv_id: str, risk_assessment: dict, user_account: str = None) -> dict:
    """Create an automated booking for high-risk cases"""
    try:
        # Get user data first to extract location
        user_data = None
        user_location = None
        if user_account:
            user_data = get_user_data(user_account)
            # Extract location from user data
            if user_data:
                user_location = user_data.get('district', '')
        
        # Find available professional with location matching
        professional = find_available_professional(risk_assessment['risk_level'], user_location)
        
        if not professional:
            print(f"❌ No available professional found for risk level: {risk_assessment['risk_level']}")
            return None
        
        # Generate booking ID
        booking_id = f"auto_{conv_id}_{int(time.time())}"
        
        # Create conversation summary
        conversation_summary = generate_conversation_summary(conv_id)
        
        # Determine session timing
        if risk_assessment['risk_level'] == 'critical':
            scheduled_datetime = time.time() + 3600  # 1 hour from now
            session_type = 'emergency'
        else:
            scheduled_datetime = time.time() + 86400  # 24 hours from now
            session_type = 'urgent'
        
        # Create booking in database
        conn = sqlite3.connect(DB_FILE)
        try:
            conn.execute("""
                INSERT INTO automated_bookings
                (booking_id, conv_id, user_account, professional_id, risk_level, risk_score,
                 detected_indicators, conversation_summary, booking_status, scheduled_datetime,
                 session_type, notes, created_ts, updated_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_id, conv_id, user_account, professional['id'],
                risk_assessment['risk_level'], risk_assessment['risk_score'],
                json.dumps(risk_assessment['detected_indicators']), conversation_summary,
                'pending', scheduled_datetime, session_type,
                f"Automated booking for {risk_assessment['risk_level']} risk case",
                time.time(), time.time()
            ))
            conn.commit()
            
            # Create professional notification
            conn.execute("""
                INSERT INTO professional_notifications
                (professional_id, booking_id, title, message, priority, is_read, 
                 notification_type, risk_level, created_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                professional['id'], booking_id,
                f"New {risk_assessment['risk_level'].upper()} Risk Booking",
                f"Automated booking created for high-risk case. Risk level: {risk_assessment['risk_level']}",
                'high' if risk_assessment['risk_level'] in ['high', 'critical'] else 'medium',
                0, 'booking_assigned', risk_assessment['risk_level'], time.time()
            ))
            conn.commit()
            
        finally:
            conn.close()
        
        # Send SMS notifications
        sms_results = {'user_sms': None, 'professional_sms': None}
        
        try:
            from sms_service import get_sms_service
            sms_service = get_sms_service()
            
            if sms_service:
                # Send SMS to user if they have a phone number
                if user_data and user_data.get('telephone'):
                    try:
                        user_sms_result = sms_service.send_booking_notification(
                            user_data, professional, {
                                'booking_id': booking_id,
                                'risk_level': risk_assessment['risk_level'],
                                'scheduled_datetime': scheduled_datetime,
                                'session_type': session_type
                            }
                        )
                        sms_results['user_sms'] = user_sms_result
                        print(f"✅ User SMS sent: {user_sms_result.get('success', False)}")
                    except Exception as e:
                        print(f"❌ User SMS failed: {str(e)}")
                
                # Send SMS to professional
                if professional.get('phone'):
                    try:
                        prof_sms_result = sms_service.send_professional_notification(
                            professional, user_data or {}, {
                                'booking_id': booking_id,
                                'risk_level': risk_assessment['risk_level'],
                                'scheduled_datetime': scheduled_datetime,
                                'session_type': session_type,
                                'conversation_summary': conversation_summary
                            }
                        )
                        sms_results['professional_sms'] = prof_sms_result
                        print(f"✅ Professional SMS sent: {prof_sms_result.get('success', False)}")
                    except Exception as e:
                        print(f"❌ Professional SMS failed: {str(e)}")
            else:
                print("⚠️ SMS service not available")
                
        except Exception as e:
            print(f"❌ SMS notification error: {str(e)}")
        
        print(f"✅ Automated booking created: {booking_id}")
        print(f"   Professional: {professional['first_name']} {professional['last_name']}")
        print(f"   Risk Level: {risk_assessment['risk_level']}")
        print(f"   SMS Results: User={sms_results['user_sms']}, Professional={sms_results['professional_sms']}")
        
        return {
            'booking_id': booking_id,
            'professional': professional,
            'professional_name': f"{professional['first_name']} {professional['last_name']}",
            'specialization': professional.get('specialization', 'counselor'),
            'professional_id': professional['id'],
            'risk_level': risk_assessment['risk_level'],
            'session_type': session_type,
            'scheduled_datetime': scheduled_datetime,
            'sms_results': sms_results
        }
        
    except Exception as e:
        print(f"❌ Error creating automated booking: {str(e)}")
        return None

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/healthz')
def healthz():
    """Health check endpoint"""
    return {"ok": True}

@app.route('/ask', methods=['POST'])
def ask():
    """Main chat endpoint with scope validation"""
    data = request.get_json(force=True)
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Missing 'query'"}), 400

    # Simple scope validation for non-mental health topics
    query_lower = query.lower()
    non_mental_health_indicators = [
        'computer', 'technology', 'programming', 'politics', 'sports', 'football',
        'recipe', 'cooking', 'weather', 'mathematics', 'history', 'business',
        'movie', 'music', 'travel', 'shopping', 'news', 'science'
    ]
    
    # Check if query is clearly outside mental health scope
    if any(indicator in query_lower for indicator in non_mental_health_indicators):
        rejection_message = "I'm a mental health support assistant and can only help with emotional well-being and mental health concerns. Let's focus on how you're feeling today - is there anything causing you stress, anxiety, or affecting your mood?"
        
        conv_id = data.get("id") or str(uuid.uuid4())
        save_message(conv_id, "user", query)
        save_message(conv_id, "assistant", rejection_message)
        
        return jsonify({
            "answer": rejection_message,
            "id": conv_id,
            "scope_rejection": True
        })

    # Conversation ID handling
    conv_id = data.get("id")
    new_conv = False
    if not conv_id:
        conv_id = str(uuid.uuid4())
        new_conv = True

    # Load conversation history
    history = load_history(conv_id)
    
    # Get message count for this conversation
    conn = sqlite3.connect(DB_FILE)
    try:
        message_count = conn.execute("""
            SELECT COUNT(*) FROM messages WHERE conv_id = ?
        """, (conv_id,)).fetchone()[0]
    finally:
        conn.close()
    
    # Build messages for AI
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history
    for entry in history:
        role = entry.get("role", "user")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": entry.get("content", "")})
    
    # Add current query
    messages.append({"role": "user", "content": query})
    
    # Get context from embeddings if available
    context = ""
    if chunk_embeddings is not None:
        top = retrieve(query, k=4)
        context = build_context(top)
    
    # Build user prompt with context
    if context:
        user_prompt = f"""Answer the user's question using ONLY the CONTEXT below.
If the context is insufficient, be honest and provide safe, general guidance.

QUESTION:
{query}

CONTEXT:
{context}
"""
    else:
        user_prompt = query
    
    # Replace the last user message with the enhanced prompt
    messages[-1] = {"role": "user", "content": user_prompt}
    
    try:
        # Get AI response using available service
        if openai_client:
            # Use Ollama OpenAI client
            try:
                response = openai_client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
            except Exception as ollama_error:
                print(f"Ollama error: {ollama_error}")
                # Fallback to simple response
                answer = "Hello! I'm AIMHSA, your mental health companion for Rwanda. How can I support you today? If you need immediate help, contact the Mental Health Hotline at 105."
        elif ai_service:
            # Use Hugging Face AI service
            try:
                answer = ai_service.generate_response(messages)
            except Exception as hf_error:
                print(f"Hugging Face AI error: {hf_error}")
                # Fallback to simple response
                answer = "Hello! I'm AIMHSA, your mental health companion for Rwanda. How can I support you today? If you need immediate help, contact the Mental Health Hotline at 105."
        else:
            # Fallback response
            answer = "Hello! I'm AIMHSA, your mental health companion for Rwanda. How can I support you today? If you need immediate help, contact the Mental Health Hotline at 105."
        
        # Save conversation
        save_message(conv_id, "user", query)
        save_message(conv_id, "assistant", answer)
        
        # RISK ASSESSMENT AND AUTOMATED BOOKING WORKFLOW
        risk_assessment = assess_conversation_risk(query, history)
        
        # Store risk assessment
        conn = sqlite3.connect(DB_FILE)
        try:
            conn.execute("""
                INSERT INTO risk_assessments 
                (conv_id, user_query, risk_score, risk_level, detected_indicators, assessment_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                conv_id, 
                query, 
                risk_assessment['risk_score'],
                risk_assessment['risk_level'],
                json.dumps(risk_assessment['detected_indicators']),
                risk_assessment['assessment_timestamp']
            ))
            conn.commit()
        finally:
            conn.close()
        
        # Check for automated booking triggers
        booking_result = None
        ask_booking = None
        booking_created = False
        
        # Check if booking prompt was already shown for this conversation
        conn = sqlite3.connect(DB_FILE)
        try:
            booking_prompt_shown = conn.execute("""
                SELECT booking_prompt_shown FROM conversations WHERE conv_id = ?
            """, (conv_id,)).fetchone()
            booking_prompt_shown = booking_prompt_shown[0] if booking_prompt_shown else False
        finally:
            conn.close()
        
        # Trigger 1: After 5 messages - ask user if they want to book (only once per conversation)
        if message_count >= 5 and not booking_prompt_shown:
            ask_booking = True
            # Mark that booking prompt has been shown
            conn = sqlite3.connect(DB_FILE)
            try:
                conn.execute("""
                    UPDATE conversations SET booking_prompt_shown = 1 WHERE conv_id = ?
                """, (conv_id,))
                conn.commit()
            finally:
                conn.close()
        
        # Trigger 2: High/Critical risk detection - automatic booking
        if risk_assessment['risk_level'] in ['high', 'critical']:
            user_account = data.get("account", "").strip()
            booking_result = create_automated_booking(conv_id, risk_assessment, user_account)
            
            if booking_result:
                # Add booking notification to response
                answer += f"\n\n🚨 **URGENT**: Based on our conversation, I've automatically scheduled you with a mental health professional. You will receive SMS confirmation shortly."
                # Set flag to trigger frontend booking display
                booking_created = True
                booking_id = booking_result.get('booking_id')
                professional_name = booking_result.get('professional_name')
                specialization = booking_result.get('specialization')
                session_type = booking_result.get('session_type')
                scheduled_datetime = booking_result.get('scheduled_datetime')
        
        # Prepare response
        resp = {"answer": answer, "id": conv_id}
        if new_conv:
            resp["new"] = True
        if ask_booking:
            resp["ask_booking"] = True
        if booking_result:
            resp["booking_created"] = True
            resp["booking_id"] = booking_result.get("booking_id")
            resp["professional_name"] = booking_result.get("professional_name")
            resp["specialization"] = booking_result.get("specialization")
            resp["session_type"] = booking_result.get("session_type")
            resp["scheduled_datetime"] = booking_result.get("scheduled_datetime")
        
        return jsonify(resp)
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    """
    POST /register
    JSON: { "username": "...", "email": "...", "fullname": "...", "telephone": "...", "province": "...", "district": "...", "password": "..." }
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # Extract and validate all fields
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    fullname = (data.get("fullname") or "").strip()
    telephone = (data.get("telephone") or "").strip()
    province = (data.get("province") or "").strip()
    district = (data.get("district") or "").strip()
    password = (data.get("password") or "")
    
    # Collect validation errors
    errors = {}
    
    # Validate required fields
    if not username:
        errors['username'] = 'Username is required'
    if not email:
        errors['email'] = 'Email is required'
    if not fullname:
        errors['fullname'] = 'Full name is required'
    if not telephone:
        errors['telephone'] = 'Phone number is required'
    if not province:
        errors['province'] = 'Province is required'
    if not district:
        errors['district'] = 'District is required'
    if not password:
        errors['password'] = 'Password is required'
    
    # Email validation
    import re
    if email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors['email'] = 'Please enter a valid email address'
    
    # Phone validation (Rwanda format)
    if telephone:
        phone_pattern = r'^(\+250|0)[0-9]{9}$'
        if not re.match(phone_pattern, telephone):
            errors['telephone'] = 'Please enter a valid Rwanda phone number (+250XXXXXXXXX or 07XXXXXXXX)'
    
    # Username validation
    if username:
        if len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters long'
        elif len(username) > 20:
            errors['username'] = 'Username must be no more than 20 characters long'
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors['username'] = 'Username can only contain letters, numbers, and underscores'
    
    # Password validation
    if password:
        if len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters long'
        elif len(password) > 128:
            errors['password'] = 'Password must be no more than 128 characters long'
    
    # Return validation errors if any
    if errors:
        return jsonify({"errors": errors, "message": "Please correct the errors below"}), 400

    conn = sqlite3.connect(DB_FILE)
    try:
        # Check if username already exists
        cur = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            return jsonify({"errors": {"username": "This username is already taken. Please choose another."}, "message": "Please correct the errors below"}), 409
        
        # Check if email already exists
        cur = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            return jsonify({"errors": {"email": "This email is already registered. Please use a different email."}, "message": "Please correct the errors below"}), 409
        
        # Check if telephone already exists
        cur = conn.execute("SELECT 1 FROM users WHERE telephone = ?", (telephone,))
        if cur.fetchone():
            return jsonify({"errors": {"telephone": "This phone number is already registered. Please use a different phone number."}, "message": "Please correct the errors below"}), 409
        
        # All validations passed, create the user
        pw_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, email, fullname, telephone, province, district, password_hash, created_ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (username, email, fullname, telephone, province, district, pw_hash, time.time()),
        )
        conn.commit()
        
    except sqlite3.IntegrityError as e:
        # Fallback error handling in case of race conditions
        if "username" in str(e):
            return jsonify({"errors": {"username": "This username is already taken. Please choose another."}, "message": "Please correct the errors below"}), 409
        elif "email" in str(e):
            return jsonify({"errors": {"email": "This email is already registered. Please use a different email."}, "message": "Please correct the errors below"}), 409
        elif "telephone" in str(e):
            return jsonify({"errors": {"telephone": "This phone number is already registered. Please use a different phone number."}, "message": "Please correct the errors below"}), 409
        else:
            return jsonify({"error": "Registration failed. Please try again."}), 409
    except Exception as e:
        app.logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed. Please try again."}), 500
    finally:
        conn.close()
    
    return jsonify({"ok": True, "account": username, "message": "Account created successfully"})

@app.route('/api/login', methods=['POST'])
def api_login():
    """
    POST /login
    JSON: { "email": "...", "password": "..." }
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    
    # Email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"error": "Invalid email format"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT username, password_hash FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "invalid credentials"}), 401
        username, stored = row
        if not check_password_hash(stored, password):
            return jsonify({"error": "invalid credentials"}), 401
    finally:
        conn.close()
    return jsonify({"ok": True, "account": username})

@app.route('/api/history')
def api_history():
    """Get conversation history"""
    conv_id = request.args.get("id")
    if not conv_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400
    
    try:
        hist = load_history(conv_id)
        return jsonify({"id": conv_id, "history": hist})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/request-booking', methods=['POST'])
def request_booking():
    """Handle manual booking requests from users"""
    data = request.get_json(force=True)
    conv_id = data.get("conv_id")
    user_account = data.get("account", "").strip()
    
    if not conv_id:
        return jsonify({"error": "Missing conversation ID"}), 400
    
    try:
        # Load conversation history for risk assessment
        history = load_history(conv_id)
        
        # Get the last user message for risk assessment
        conn = sqlite3.connect(DB_FILE)
        try:
            cur = conn.execute("""
                SELECT content FROM messages 
                WHERE conv_id = ? AND role = 'user' 
                ORDER BY ts DESC LIMIT 1
            """, (conv_id,))
            last_message = cur.fetchone()
            last_query = last_message[0] if last_message else ""
        finally:
            conn.close()
        
        # Assess risk based on conversation
        risk_assessment = assess_conversation_risk(last_query, history)
        
        # Create booking (even for low risk if user requests)
        booking_result = create_automated_booking(conv_id, risk_assessment, user_account)
        
        if booking_result:
            return jsonify({
                "success": True,
                "booking_id": booking_result["booking_id"],
                "professional": booking_result["professional"],
                "risk_level": booking_result["risk_level"],
                "message": "Booking request submitted successfully. You will receive SMS confirmation shortly."
            })
        else:
            return jsonify({
                "success": False,
                "error": "Unable to create booking at this time. Please try again later."
            }), 500
            
    except Exception as e:
        return jsonify({"error": f"Booking request failed: {str(e)}"}), 500

@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset database"""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM attachments")
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM conversations")
        conn.execute("DELETE FROM users")
        conn.commit()
    finally:
        conn.close()
    
    return jsonify({"ok": True})

@app.route('/session', methods=['POST'])
def api_session():
    """
    Create or retrieve session by IP or account.
    Request JSON: { "account": "<optional account id>" }
    Returns: { "id": "<conv_id>", "new": true|false }
    """
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        data = {}
    
    account = (data.get("account") or "").strip()
    if account:
        key = f"acct:{account}"
    else:
        ip = request.remote_addr or "unknown"
        key = f"ip:{ip}"
    
    # Simple session creation logic
    conv_id = str(uuid.uuid4())
    
    # Save session to database
    conn = sqlite3.connect(DB_FILE)
    try:
        # Check if session exists
        cur = conn.execute("SELECT conv_id FROM sessions WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            # Update existing session
            conn.execute("UPDATE sessions SET ts = ? WHERE key = ?", (time.time(), key))
            conn.commit()
            return jsonify({"id": row[0], "new": False})
        else:
            # Create new session
            conn.execute(
                "INSERT INTO sessions (key, conv_id, ts) VALUES (?, ?, ?)",
                (key, conv_id, time.time())
            )
            
            # Also create a conversations entry
            conn.execute(
                "INSERT OR IGNORE INTO conversations (conv_id, owner_key, preview, ts) VALUES (?, ?, ?, ?)",
                (conv_id, key, "New chat", time.time())
            )
            conn.commit()
            return jsonify({"id": conv_id, "new": True})
    finally:
        conn.close()

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def test_ollama_connection():
    """Test connection to Ollama or Hugging Face AI service"""
    try:
        if openai_client:
            print("🔗 Testing Ollama connection...")
            response = openai_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            print("✅ Ollama connection successful!")
            return True
        elif ai_service:
            print("🔗 Testing Hugging Face AI service...")
            test_response = ai_service.generate_response([{"role": "user", "content": "Hello"}])
            if test_response and len(test_response.strip()) > 0:
                print("✅ Hugging Face AI service successful!")
                return True
            else:
                print("❌ Hugging Face AI service returned empty response")
                return False
        else:
            print("❌ No AI service available")
            return False
    except Exception as e:
        print(f"❌ AI service connection failed: {e}")
        if openai_client:
            print("💡 Make sure Ollama is running: ollama serve")
        return False

@app.route('/history')
def history():
    """
    Query params: ?id=<conv_id>
    Returns: { "id": "<conv_id>", "history": [ {role, content}, ... ], "attachments": [ {filename,text}, ... ] }
    """
    conv_id = request.args.get("id")
    password = (request.args.get("password") or "").strip()
    if not conv_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400
    try:
        # if conversation is archived and locked, require password to view history
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.execute("SELECT IFNULL(archived,0), archive_pw_hash FROM conversations WHERE conv_id = ?", (conv_id,))
            row = cur.fetchone()
        finally:
            conn.close()
        if row and int(row[0]) == 1 and row[1]:
            if not password or not check_password_hash(row[1], password):
                return jsonify({"error": "password required"}), 403
        hist = load_history(conv_id)
        atts = load_attachments(conv_id)
        return jsonify({"id": conv_id, "history": hist, "attachments": atts})
    except Exception as e:
        app.logger.exception("history endpoint failed")
        return jsonify({"error": str(e)}), 500

@app.route('/conversations')
@app.route('/api/conversations')
def get_conversations_endpoint():
    """
    GET /conversations?account=<required>
    Returns: { "conversations": [ {id, preview, timestamp}, ... ] }
    """
    account = (request.args.get("account") or "").strip()
    if not account:
        return jsonify({"error": "Account required to list conversations"}), 403
    key = f"acct:{account}"
    try:
        rows = list_conversations(key)
        return jsonify({"conversations": rows})
    except Exception as e:
        app.logger.exception("failed to list conversations")
        return jsonify({"error": str(e)}), 500

@app.route('/conversations', methods=['POST'])
@app.route('/api/conversations', methods=['POST'])
def create_conversations_endpoint():
    """
    POST /conversations
    Body JSON: { "account": "<required account id>" }
    Returns: { "id": "<conv_id>", "new": true }
    """
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        data = {}
    account = (data.get("account") or "").strip()
    if not account:
        return jsonify({"error": "Account required to create server-backed conversations"}), 403
    key = f"acct:{account}"
    conv_id = create_conversation(owner_key=key, preview="New chat")
    return jsonify({"id": conv_id, "new": True})

@app.route('/conversations/archived')
@app.route('/api/conversations/archived')
def get_archived_conversations_endpoint():
    """
    GET /conversations/archived?account=<required>
    Returns archived conversations for this account
    """
    account = (request.args.get("account") or "").strip()
    if not account:
        return jsonify({"error": "Account required to list conversations"}), 403
    key = f"acct:{account}"
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute(
            "SELECT conv_id, preview, ts, CASE WHEN archive_pw_hash IS NULL OR archive_pw_hash = '' THEN 0 ELSE 1 END AS locked FROM conversations WHERE owner_key = ? AND IFNULL(archived,0) = 1 ORDER BY ts DESC",
            (key,),
        )
        rows = cur.fetchall()
        items = [{"id": r[0], "preview": r[1] or "New chat", "timestamp": r[2], "locked": bool(r[3])} for r in rows]
        return jsonify({"conversations": items})
    except Exception as e:
        app.logger.exception("failed to list archived conversations")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/conversations/archive', methods=['POST'])
@app.route('/api/conversations/archive', methods=['POST'])
def archive_conversation():
    """
    POST /conversations/archive
    JSON: { "account": "...", "id": "<conv_id>", "archived": true|false }
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    account = (data.get("account") or "").strip()
    conv_id = (data.get("id") or "").strip()
    archived = bool(data.get("archived", True))
    password = (data.get("password") or "").strip()
    if not account or not conv_id:
        return jsonify({"error": "account and id required"}), 400
    owner_key = f"acct:{account}"
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT owner_key FROM conversations WHERE conv_id = ?", (conv_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "conversation not found"}), 404
        if (row[0] or "") != owner_key:
            return jsonify({"error": "forbidden"}), 403
        # when archiving, password is REQUIRED; when unarchiving, password MUST match
        if archived:
            if not password:
                return jsonify({"error": "password required to archive"}), 400
            pw_hash = generate_password_hash(password)
            conn.execute("UPDATE conversations SET archive_pw_hash = ? WHERE conv_id = ?", (pw_hash, conv_id))
        else:
            cur = conn.execute("SELECT archive_pw_hash FROM conversations WHERE conv_id = ?", (conv_id,))
            row = cur.fetchone()
            if row and row[0]:
                if not password or not check_password_hash(row[0], password):
                    return jsonify({"error": "invalid password"}), 403
            # clear hash on successful unarchive
            conn.execute("UPDATE conversations SET archive_pw_hash = NULL WHERE conv_id = ?", (conv_id,))
        conn.execute("UPDATE conversations SET archived = ? WHERE conv_id = ?", (archived, conv_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/professional/login', methods=['POST'])
def professional_login():
    """Professional login"""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # Accept either username or email for convenience
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "")
    
    if (not username and not email) or not password:
        return jsonify({"error": "username/email and password required"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        if username:
            cur = conn.execute(
                "SELECT id, password_hash, first_name, last_name, username, email FROM professionals WHERE username = ? AND is_active = 1",
                (username,)
            )
        else:
            cur = conn.execute(
                "SELECT id, password_hash, first_name, last_name, username, email FROM professionals WHERE email = ? AND is_active = 1",
                (email,)
            )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "invalid credentials"}), 401
        
        prof_id, stored_hash, first_name, last_name, uname, uemail = row
        if not check_password_hash(stored_hash, password):
            return jsonify({"error": "invalid credentials"}), 401
        
        return jsonify({
            "ok": True, 
            "professional_id": prof_id,
            "name": f"{first_name} {last_name}",
            "username": uname,
            "email": uemail
        })
    finally:
        conn.close()

@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint for all user types"""
    try:
        # Clear any server-side session data if needed
        # For now, we rely on client-side localStorage clearing
        
        return jsonify({
            "ok": True,
            "message": "Logged out successfully"
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Logout error: {str(e)}"
        }), 500

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login - redirects to dashboard"""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "")
    
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT id, password_hash, email, role FROM admin_users WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "invalid credentials"}), 401
        
        admin_id, stored_hash, email, role = row
        if not check_password_hash(stored_hash, password):
            return jsonify({"error": "invalid credentials"}), 401
        
        # Create admin session token
        import secrets
        session_token = secrets.token_urlsafe(32)
        
        return jsonify({
            "ok": True,
            "redirect": "/admin_dashboard.html",
            "admin_id": admin_id,
            "username": username,
            "email": email,
            "role": role,
            "session_token": session_token
        })
    finally:
        conn.close()

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    """
    POST /forgot_password
    JSON: { "email": "..." }
    Creates a short-lived reset token and sends it via email.
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    email = (data.get("email") or "").strip()
    if not email:
        return jsonify({"error": "email required"}), 400
    
    # Email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"error": "Invalid email format"}), 400
    
    # verify user exists
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT username, fullname FROM users WHERE email = ?", (email,))
        user_row = cur.fetchone()
        if not user_row:
            # do not reveal whether the user exists; still return ok
            return jsonify({"ok": True, "message": "If the email exists, a reset code has been sent."})
        
        username, fullname = user_row
        
        # Check if there's already an active reset token for this user
        cur = conn.execute(
            "SELECT id FROM password_resets WHERE username = ? AND used = 0 AND expires_ts > ?",
            (username, time.time())
        )
        existing_token = cur.fetchone()
        
        if existing_token:
            # Invalidate the existing token
            conn.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (existing_token[0],))
        
        # Generate new reset token
        token = uuid.uuid4().hex[:6].upper()  # 6-char code
        expires = time.time() + 15 * 60  # 15 minutes
        
        # Store the reset token
        conn.execute(
            "INSERT INTO password_resets (username, token, expires_ts, used) VALUES (?, ?, ?, 0)",
            (username, token, expires),
        )
        conn.commit()
        
        # For demo purposes, return the token instead of sending email
        return jsonify({
            "ok": True, 
            "token": token, 
            "expires_in": 900, 
            "message": "Password reset code generated. Use this code for testing.",
            "user_info": {
                "username": username,
                "fullname": fullname
            }
        })
            
    finally:
        conn.close()

@app.route('/reset_password', methods=['POST'])
def reset_password():
    """
    POST /reset_password
    JSON: { "email": "...", "token": "ABC123", "new_password": "..." }
    Validates token and updates the user's password.
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    email = (data.get("email") or "").strip()
    token = (data.get("token") or "").strip().upper()
    new_password = (data.get("new_password") or "")
    if not email or not token or not new_password:
        return jsonify({"error": "email, token, and new_password required"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "new_password too short"}), 400
    
    # Email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"error": "Invalid email format"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # First get the username from email
        cur = conn.execute("SELECT username FROM users WHERE email = ?", (email,))
        user_row = cur.fetchone()
        if not user_row:
            return jsonify({"error": "invalid email"}), 400
        username = user_row[0]
        
        # Then validate the token
        cur = conn.execute(
            "SELECT id, expires_ts, used FROM password_resets WHERE username = ? AND token = ?",
            (username, token),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "invalid token"}), 400
        reset_id, expires_ts, used = row
        if used:
            return jsonify({"error": "token already used"}), 400
        if time.time() > float(expires_ts):
            return jsonify({"error": "token expired"}), 400
        # Update password and mark token used
        pw_hash = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (pw_hash, username))
        conn.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (reset_id,))
        conn.commit()
        
        # Get user info for confirmation
        cur = conn.execute("SELECT email, fullname FROM users WHERE username = ?", (username,))
        user_info = cur.fetchone()
        
        return jsonify({
            "ok": True, 
            "message": "Password reset successfully. You can now login with your new password.",
            "user_info": {
                "username": username,
                "email": user_info[0] if user_info else email,
                "fullname": user_info[1] if user_info else "User"
            }
        })
    finally:
        conn.close()

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Clear messages and attachments for a conversation."""
    data = request.get_json(force=True)
    conv_id = data.get("id")
    if not conv_id:
        return jsonify({"error": "Missing conversation id"}), 400

    conn = sqlite3.connect(DB_FILE)
    try:
        # Delete messages and attachments for this conversation
        conn.execute("DELETE FROM messages WHERE conv_id = ?", (conv_id,))
        conn.execute("DELETE FROM attachments WHERE conv_id = ?", (conv_id,))
        # Reset conversation preview
        conn.execute(
            "UPDATE conversations SET preview = ? WHERE conv_id = ?",
            ("New chat", conv_id),
        )
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- delete a conversation (requires account owner) ---
@app.route('/conversations/delete', methods=['POST'])
@app.route('/api/conversations/delete', methods=['POST'])
def delete_conversation():
    """
    POST /conversations/delete
    JSON: { "account": "...", "id": "<conv_id>" }
    Only allows deletion when the conversation owner matches acct:<account>.
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    account = (data.get("account") or "").strip()
    conv_id = (data.get("id") or "").strip()
    password = (data.get("password") or "").strip()
    if not account or not conv_id:
        return jsonify({"error": "account and id required"}), 400

    owner_key = f"acct:{account}"

    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT owner_key, IFNULL(archived,0), archive_pw_hash FROM conversations WHERE conv_id = ?", (conv_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "conversation not found"}), 404
        if (row[0] or "") != owner_key:
            return jsonify({"error": "forbidden"}), 403
        # If archived and locked, require correct password to delete
        if int(row[1]) == 1 and row[2]:
            if not password or not check_password_hash(row[2], password):
                return jsonify({"error": "invalid password"}), 403

        # delete related rows
        conn.execute("DELETE FROM messages WHERE conv_id = ?", (conv_id,))
        conn.execute("DELETE FROM attachments WHERE conv_id = ?", (conv_id,))
        conn.execute("DELETE FROM sessions WHERE conv_id = ?", (conv_id,))
        conn.execute("DELETE FROM conversations WHERE conv_id = ?", (conv_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- rename a conversation (requires account owner) ---
@app.route('/conversations/rename', methods=['POST'])
@app.route('/api/conversations/rename', methods=['POST'])
def rename_conversation():
    """
    POST /conversations/rename
    JSON: { "account": "...", "id": "<conv_id>", "preview": "<new title>" }
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    account = (data.get("account") or "").strip()
    conv_id = (data.get("id") or "").strip()
    preview = (data.get("preview") or "").strip()
    if not account or not conv_id or not preview:
        return jsonify({"error": "account, id and preview required"}), 400
    owner_key = f"acct:{account}"
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT owner_key, IFNULL(archived,0) FROM conversations WHERE conv_id = ?", (conv_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "conversation not found"}), 404
        if (row[0] or "") != owner_key:
            return jsonify({"error": "forbidden"}), 403
        if int(row[1]) == 1:
            return jsonify({"error": "cannot rename archived conversation"}), 403
        conn.execute("UPDATE conversations SET preview = ?, ts = ? WHERE conv_id = ?", (preview[:120], time.time(), conv_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- handle booking response from user ---
@app.route('/booking_response', methods=['POST'])
def handle_booking_response():
    """
    POST /booking_response
    JSON: { "conversation_id": "...", "response": "yes/no", "account": "..." }
    Handles user's response to booking question
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    conversation_id = data.get("conversation_id")
    response = data.get("response")  # "yes" or "no"
    account = data.get("account")
    
    if not conversation_id or not response:
        return jsonify({"error": "conversation_id and response required"}), 400
    
    if response not in ["yes", "no"]:
        return jsonify({"error": "response must be 'yes' or 'no'"}), 400
    
    # If user wants booking, create one
    if response == "yes":
        try:
            # Get conversation history for risk assessment
            conn = sqlite3.connect(DB_FILE)
            try:
                cur = conn.execute("SELECT role, content FROM messages WHERE conv_id = ? ORDER BY ts DESC LIMIT 10", (conversation_id,))
                messages = cur.fetchall()
                conversation_history = [{"role": row[0], "content": row[1]} for row in messages]
                
                # Simple risk assessment based on recent messages
                risk_level = "medium"  # Default for user-requested booking
                for msg in conversation_history:
                    content = msg["content"].lower()
                    if any(word in content for word in ["suicide", "kill", "end", "harm"]):
                        risk_level = "critical"
                        break
                    elif any(word in content for word in ["depressed", "hopeless", "crisis", "emergency"]):
                        risk_level = "high"
                        break
                
                # Get user location for better matching
                user_location = None
                if account:
                    user_data = get_user_data(account)
                    if user_data:
                        user_location = user_data.get('district', '')
                
                # Find available professional with location matching
                professional = find_available_professional(risk_level, user_location)
                
                if professional:
                    # Create booking
                    booking_id = str(uuid.uuid4())
                    current_time = time.time()
                    
                    # Schedule for within 24 hours
                    scheduled_time = current_time + (24 * 60 * 60)  # 24 hours from now
                    
                    conn.execute("""
                        INSERT INTO automated_bookings 
                        (booking_id, conv_id, user_account, professional_id, risk_level, risk_score, 
                         booking_status, scheduled_datetime, session_type, created_ts, updated_ts)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (booking_id, conversation_id, account, professional["id"], risk_level, 0.5,
                          "pending", scheduled_time, "consultation", current_time, current_time))
                    
                    # Create notification for professional
                    conn.execute("""
                        INSERT INTO professional_notifications 
                        (professional_id, booking_id, notification_type, title, message, priority, created_ts)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (professional["id"], booking_id, "new_booking", 
                          f"New {risk_level.title()} Risk Booking", 
                          f"User {account} has requested a mental health consultation.", 
                          "high" if risk_level in ["critical", "high"] else "normal", current_time))
                    
                    conn.commit()
                    
                    # Send SMS notifications if configured
                    sms_service = get_sms_service()
                    if sms_service:
                        try:
                            # Get user data for SMS
                            user_data = None
                            if account:
                                user_data = get_user_data(account)
                            
                            # Send SMS to user
                            if user_data and user_data.get("telephone"):
                                sms_service.send_booking_notification(
                                    user_data, professional, {
                                        "booking_id": booking_id,
                                        "scheduled_time": scheduled_time,
                                        "risk_level": risk_level,
                                        "session_type": "consultation"
                                    }
                                )
                            
                            # Send SMS to professional
                            if professional.get("phone"):
                                sms_service.send_professional_notification(
                                    professional, user_data or {"fullname": account}, {
                                        "booking_id": booking_id,
                                        "scheduled_time": scheduled_time,
                                        "risk_level": risk_level,
                                        "session_type": "consultation"
                                    }
                                )
                        except Exception as sms_error:
                            print(f"SMS notification failed: {sms_error}")
                    
                    # Format professional name
                    professional_name = f"{professional.get('first_name', '')} {professional.get('last_name', '')}"
                    specialization = professional.get('specialization', 'counselor')
                    
                    return jsonify({
                        "ok": True,
                        "message": "Booking created successfully! You will receive SMS confirmation shortly.",
                        "booking": {
                            "booking_id": booking_id,
                            "professional_name": professional_name,
                            "specialization": specialization,
                            "session_type": "consultation",
                            "scheduled_datetime": scheduled_time,
                            "professional": professional,
                            "scheduled_time": scheduled_time,
                            "risk_level": risk_level
                        }
                    })
                else:
                    return jsonify({
                        "ok": True,
                        "message": "I'm sorry, no professionals are currently available. Please try again later or contact the Mental Health Hotline at 105 for immediate support."
                    })
                    
            finally:
                conn.close()
                
        except Exception as e:
            return jsonify({"error": f"Failed to create booking: {str(e)}"}), 500
    
    else:  # response == "no"
        return jsonify({
            "ok": True,
            "message": "No problem! I'm here whenever you need support. Feel free to continue our conversation or reach out anytime."
        })

# Admin endpoints for professional management
@app.route('/admin/professionals', methods=['POST'])
def create_professional():
    """Create a new professional"""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    required_fields = ['username', 'first_name', 'last_name', 'email', 'specialization', 'expertise_areas']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Password is required but can be default
    password = data.get('password', 'password123')
    
    # Hash password
    password_hash = generate_password_hash(password)
    
    # Prepare expertise areas as JSON
    expertise_areas = json.dumps(data.get('expertise_areas', []))
    languages = json.dumps(data.get('languages', ['english']))
    qualifications = json.dumps(data.get('qualifications', []))
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # Check if username already exists
        existing_username = conn.execute(
            "SELECT username FROM professionals WHERE username = ?", 
            (data['username'],)
        ).fetchone()
        
        if existing_username:
            return jsonify({
                "error": "Username already exists", 
                "details": f"Username '{data['username']}' is already taken. Please choose a different username."
            }), 409
        
        # Check if email already exists
        existing_email = conn.execute(
            "SELECT email FROM professionals WHERE email = ?", 
            (data['email'],)
        ).fetchone()
        
        if existing_email:
            return jsonify({
                "error": "Email already exists", 
                "details": f"Email '{data['email']}' is already registered. Please use a different email."
            }), 409
        
        cursor = conn.execute("""
            INSERT INTO professionals 
            (username, password_hash, first_name, last_name, email, phone,
             specialization, expertise_areas, languages, qualifications, district,
             consultation_fee, experience_years, bio, created_ts, updated_ts, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            data['username'], password_hash, data['first_name'], data['last_name'],
            data['email'], data.get('phone'), data['specialization'], expertise_areas,
            languages, qualifications, data.get('district'), data.get('consultation_fee'),
            data.get('experience_years', 0), data.get('bio'), time.time(), time.time()
        ))
        conn.commit()
        
        # Get the created professional ID
        prof_id = cursor.lastrowid
        
        return jsonify({
            "ok": True, 
            "message": "Professional created successfully",
            "professional": {"id": prof_id}
        })
    except sqlite3.IntegrityError as e:
        return jsonify({
            "error": "Database constraint violation", 
            "details": str(e)
        }), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/professionals', methods=['GET'])
def list_professionals():
    """List all professionals with filtering"""
    specialization = request.args.get('specialization')
    is_active = request.args.get('is_active')
    
    conn = sqlite3.connect(DB_FILE)
    try:
        query = "SELECT * FROM professionals"
        params = []
        conditions = []
        
        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(is_active)
        
        if specialization:
            conditions.append("specialization = ?")
            params.append(specialization)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_ts DESC"
        
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        
        professionals = []
        columns = [desc[0] for desc in cur.description]
        for row in rows:
            prof = dict(zip(columns, row))
            # Parse JSON fields with error handling
            try:
                prof['expertise_areas'] = json.loads(prof.get('expertise_areas') or '[]')
            except (json.JSONDecodeError, TypeError):
                prof['expertise_areas'] = []
            
            try:
                prof['languages'] = json.loads(prof.get('languages') or '[]')
            except (json.JSONDecodeError, TypeError):
                prof['languages'] = ['english']
            
            try:
                prof['qualifications'] = json.loads(prof.get('qualifications') or '[]')
            except (json.JSONDecodeError, TypeError):
                prof['qualifications'] = []
            
            # Note: availability_schedule column doesn't exist in database schema
            
            professionals.append(prof)
        
        return jsonify({"professionals": professionals})
    finally:
        conn.close()

@app.route('/admin/professionals/<int:prof_id>', methods=['PUT'])
def update_professional(prof_id: int):
    """Update a professional's information"""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # Check if professional exists
        existing = conn.execute("SELECT id FROM professionals WHERE id = ?", (prof_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Professional not found"}), 404
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        # Handle password update
        if data.get('password'):
            password_hash = generate_password_hash(data['password'])
            update_fields.append("password_hash = ?")
            params.append(password_hash)
        
        # Handle other fields
        updatable_fields = [
            'first_name', 'last_name', 'email', 'phone',
            'specialization', 'district', 'consultation_fee',
            'experience_years', 'bio'
        ]
        
        for field in updatable_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        # Handle JSON fields
        if 'expertise_areas' in data:
            update_fields.append("expertise_areas = ?")
            params.append(json.dumps(data['expertise_areas']))
        
        if 'languages' in data:
            update_fields.append("languages = ?")
            params.append(json.dumps(data['languages']))
        
        if 'qualifications' in data:
            update_fields.append("qualifications = ?")
            params.append(json.dumps(data['qualifications']))
        
        # Note: availability_schedule column doesn't exist in database schema
        
        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400
        
        # Add updated timestamp
        update_fields.append("updated_ts = ?")
        params.append(time.time())
        
        # Add prof_id to params
        params.append(prof_id)
        
        query = f"UPDATE professionals SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        
        return jsonify({"ok": True, "message": "Professional updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/professionals/<int:prof_id>', methods=['DELETE'])
def delete_professional(prof_id: int):
    """Delete a professional"""
    conn = sqlite3.connect(DB_FILE)
    try:
        # Check if professional exists
        existing = conn.execute("SELECT first_name, last_name FROM professionals WHERE id = ?", (prof_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Professional not found"}), 404
        
        first_name, last_name = existing
        
        # Check for active bookings
        active_bookings = conn.execute(
            "SELECT COUNT(*) FROM automated_bookings WHERE professional_id = ? AND booking_status IN ('pending', 'confirmed')",
            (prof_id,)
        ).fetchone()[0]
        
        if active_bookings > 0:
            return jsonify({
                "error": "Cannot delete professional with active bookings",
                "details": f"Professional {first_name} {last_name} has {active_bookings} active booking(s). Please handle these bookings first."
            }), 409
        
        # Delete the professional
        conn.execute("DELETE FROM professionals WHERE id = ?", (prof_id,))
        conn.commit()
        
        return jsonify({"ok": True, "message": f"Professional {first_name} {last_name} deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/professionals/<int:prof_id>/cancel-bookings', methods=['POST'])
def cancel_professional_bookings(prof_id: int):
    """Cancel all active bookings for a professional"""
    conn = sqlite3.connect(DB_FILE)
    try:
        # Check if professional exists
        existing = conn.execute("SELECT first_name, last_name FROM professionals WHERE id = ?", (prof_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Professional not found"}), 404
        
        first_name, last_name = existing
        
        # Cancel all active bookings
        result = conn.execute(
            "UPDATE automated_bookings SET booking_status = 'cancelled' WHERE professional_id = ? AND booking_status IN ('pending', 'confirmed')",
            (prof_id,)
        )
        
        cancelled_count = result.rowcount
        conn.commit()
        
        return jsonify({
            "ok": True, 
            "message": f"Cancelled {cancelled_count} active booking(s) for {first_name} {last_name}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/professionals/<int:prof_id>/transfer-bookings', methods=['POST'])
def transfer_professional_bookings(prof_id: int):
    """Transfer all active bookings from one professional to another"""
    conn = sqlite3.connect(DB_FILE)
    try:
        data = request.get_json()
        to_professional_id = data.get('to_professional_id')
        
        if not to_professional_id:
            return jsonify({"error": "Target professional ID is required"}), 400
        
        # Check if both professionals exist
        from_prof = conn.execute("SELECT first_name, last_name FROM professionals WHERE id = ?", (prof_id,)).fetchone()
        to_prof = conn.execute("SELECT first_name, last_name FROM professionals WHERE id = ?", (to_professional_id,)).fetchone()
        
        if not from_prof:
            return jsonify({"error": "Source professional not found"}), 404
        if not to_prof:
            return jsonify({"error": "Target professional not found"}), 404
        
        # Transfer all active bookings
        result = conn.execute(
            "UPDATE automated_bookings SET professional_id = ? WHERE professional_id = ? AND booking_status IN ('pending', 'confirmed')",
            (to_professional_id, prof_id)
        )
        
        transferred_count = result.rowcount
        conn.commit()
        
        return jsonify({
            "ok": True, 
            "message": f"Transferred {transferred_count} active booking(s) from {from_prof[0]} {from_prof[1]} to {to_prof[0]} {to_prof[1]}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/professionals/<int:prof_id>/status', methods=['POST'])
def toggle_professional_status(prof_id: int):
    """Toggle professional active status"""
    conn = sqlite3.connect(DB_FILE)
    try:
        # Get current status
        current = conn.execute("SELECT is_active FROM professionals WHERE id = ?", (prof_id,)).fetchone()
        if not current:
            return jsonify({"error": "Professional not found"}), 404
        
        is_active = current[0]
        new_status = 0 if is_active else 1
        
        conn.execute("UPDATE professionals SET is_active = ?, updated_ts = ? WHERE id = ?", 
                    (new_status, time.time(), prof_id))
        conn.commit()
        
        return jsonify({"ok": True, "is_active": bool(new_status)})
    finally:
        conn.close()

@app.route('/admin/bookings', methods=['GET'])
def list_bookings():
    """List all automated bookings with user and professional information"""
    status = request.args.get('status')
    risk_level = request.args.get('risk_level')
    limit = int(request.args.get('limit', 100))
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # Get all bookings with user and professional information
        query = """
            SELECT 
                ab.*,
                u.fullname as user_fullname,
                u.email as user_email,
                u.telephone as user_phone,
                u.province as user_province,
                u.district as user_district,
                (u.district || ', ' || u.province) as user_location,
                u.created_ts as user_created_ts,
                p.first_name as professional_first_name,
                p.last_name as professional_last_name,
                p.specialization as professional_specialization,
                p.email as professional_email,
                p.phone as professional_phone,
                p.experience_years as professional_experience,
                (p.first_name || ' ' || p.last_name) as professional_name
            FROM automated_bookings ab
            LEFT JOIN users u ON ab.user_account = u.username
            LEFT JOIN professionals p ON ab.professional_id = p.id
        """
        params = []
        conditions = []
        
        if status:
            conditions.append("ab.booking_status = ?")
            params.append(status)
        
        if risk_level:
            conditions.append("ab.risk_level = ?")
            params.append(risk_level)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY ab.created_ts DESC LIMIT ?"
        params.append(limit)
        
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        
        bookings = []
        columns = [desc[0] for desc in cur.description]
        for row in rows:
            booking = dict(zip(columns, row))
            bookings.append(booking)
        
        return jsonify({"bookings": bookings})
    finally:
        conn.close()

@app.route('/admin/bookings/<booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    """Delete a booking permanently"""
    conn = sqlite3.connect(DB_FILE)
    try:
        # Check if booking exists
        existing = conn.execute("SELECT booking_id FROM automated_bookings WHERE booking_id = ?", (booking_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Booking not found"}), 404
        
        # Delete the booking
        conn.execute("DELETE FROM automated_bookings WHERE booking_id = ?", (booking_id,))
        conn.commit()
        
        return jsonify({
            "ok": True, 
            "message": f"Booking {booking_id} deleted successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/professionals/check-availability', methods=['GET'])
def check_professional_availability():
    """Check if username or email is available"""
    username = request.args.get('username')
    email = request.args.get('email')
    
    if not username and not email:
        return jsonify({"error": "username or email required"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        result = {"username_available": True, "email_available": True}
        
        if username:
            existing_username = conn.execute(
                "SELECT username FROM professionals WHERE username = ?", 
                (username,)
            ).fetchone()
            result["username_available"] = not existing_username
        
        if email:
            existing_email = conn.execute(
                "SELECT email FROM professionals WHERE email = ?", 
                (email,)
            ).fetchone()
            result["email_available"] = not existing_email
        
        return jsonify(result)
    finally:
        conn.close()

# Additional admin endpoints for dashboard functionality
@app.route('/admin/risk-assessments', methods=['GET'])
def list_risk_assessments():
    """List risk assessments for admin dashboard"""
    limit = int(request.args.get('limit', 100))
    
    conn = sqlite3.connect(DB_FILE)
    try:
        query = """
            SELECT ra.*, u.fullname as user_fullname, u.email as user_email
            FROM risk_assessments ra
            LEFT JOIN conversations c ON ra.conv_id = c.conv_id
            LEFT JOIN users u ON c.owner_key = u.username
            ORDER BY ra.assessment_timestamp DESC LIMIT ?
        """
        
        cur = conn.execute(query, (limit,))
        rows = cur.fetchall()
        
        assessments = []
        columns = [desc[0] for desc in cur.description]
        for row in rows:
            assessment = dict(zip(columns, row))
            assessments.append(assessment)
        
        return jsonify({"assessments": assessments})
    finally:
        conn.close()

@app.route('/monitor/risk-stats', methods=['GET'])
def get_risk_stats():
    """Get risk statistics for monitoring"""
    conn = sqlite3.connect(DB_FILE)
    try:
        # Get risk level counts
        cur = conn.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM risk_assessments
            WHERE assessment_timestamp > ? 
            GROUP BY risk_level
        """, (time.time() - 7 * 24 * 60 * 60,))  # Last 7 days
        
        risk_counts = {}
        for row in cur.fetchall():
            risk_counts[row[0]] = row[1]
        
        # Get total assessments
        total_assessments = conn.execute("SELECT COUNT(*) FROM risk_assessments").fetchone()[0]
        
        return jsonify({
            "risk_counts": risk_counts,
            "total_assessments": total_assessments,
            "period": "last_7_days"
        })
    finally:
        conn.close()

@app.route('/monitor/recent-assessments', methods=['GET'])
def get_recent_assessments():
    """Get recent risk assessments"""
    limit = int(request.args.get('limit', 10))
    
    conn = sqlite3.connect(DB_FILE)
    try:
        query = """
            SELECT ra.*, u.fullname as user_fullname, u.email as user_email
            FROM risk_assessments ra
            LEFT JOIN conversations c ON ra.conv_id = c.conv_id
            LEFT JOIN users u ON c.owner_key = u.username
            ORDER BY ra.assessment_timestamp DESC LIMIT ?
        """
        
        cur = conn.execute(query, (limit,))
        rows = cur.fetchall()
        
        assessments = []
        columns = [desc[0] for desc in cur.description]
        for row in rows:
            assessment = dict(zip(columns, row))
            assessments.append(assessment)
        
        return jsonify({"assessments": assessments})
    finally:
        conn.close()

@app.route('/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for admin dashboard"""
    conn = sqlite3.connect(DB_FILE)
    try:
        # Get professional notifications
        cur = conn.execute("""
            SELECT pn.*, p.first_name, p.last_name, ab.user_account
            FROM professional_notifications pn
            LEFT JOIN professionals p ON pn.professional_id = p.id
            LEFT JOIN automated_bookings ab ON pn.booking_id = ab.booking_id
            ORDER BY pn.created_ts DESC LIMIT 50
        """)
        
        rows = cur.fetchall()
        
        notifications = []
        columns = [desc[0] for desc in cur.description]
        for row in rows:
            notification = dict(zip(columns, row))
            notifications.append(notification)
        
        return jsonify({"notifications": notifications})
    finally:
        conn.close()

# Professional Dashboard Endpoints
@app.route('/professional/profile', methods=['GET'])
def get_professional_profile():
    """Get current professional's profile"""
    # Get professional from session or token
    professional_id = request.args.get('id')
    if not professional_id:
        return jsonify({"error": "Professional ID required"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute("SELECT * FROM professionals WHERE id = ?", (professional_id,))
        row = cur.fetchone()
        
        if not row:
            return jsonify({"error": "Professional not found"}), 404
        
        columns = [desc[0] for desc in cur.description]
        professional = dict(zip(columns, row))
        
        # Parse JSON fields
        try:
            professional['expertise_areas'] = json.loads(professional.get('expertise_areas') or '[]')
        except (json.JSONDecodeError, TypeError):
            professional['expertise_areas'] = []
        
        try:
            professional['languages'] = json.loads(professional.get('languages') or '[]')
        except (json.JSONDecodeError, TypeError):
            professional['languages'] = ['english']
        
        try:
            professional['qualifications'] = json.loads(professional.get('qualifications') or '[]')
        except (json.JSONDecodeError, TypeError):
            professional['qualifications'] = []
        
        return jsonify({"professional": professional})
    finally:
        conn.close()

@app.route('/professional/dashboard-stats', methods=['GET'])
def get_professional_dashboard_stats():
    """Get professional dashboard statistics"""
    professional_id = request.args.get('id')
    if not professional_id:
        return jsonify({"error": "Professional ID required"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # Get total sessions
        total_sessions = conn.execute(
            "SELECT COUNT(*) FROM automated_bookings WHERE professional_id = ?",
            (professional_id,)
        ).fetchone()[0]
        
        # Get pending sessions
        pending_sessions = conn.execute(
            "SELECT COUNT(*) FROM automated_bookings WHERE professional_id = ? AND booking_status = 'pending'",
            (professional_id,)
        ).fetchone()[0]
        
        # Get confirmed sessions
        confirmed_sessions = conn.execute(
            "SELECT COUNT(*) FROM automated_bookings WHERE professional_id = ? AND booking_status = 'confirmed'",
            (professional_id,)
        ).fetchone()[0]
        
        # Get high risk sessions
        high_risk_sessions = conn.execute(
            "SELECT COUNT(*) FROM automated_bookings WHERE professional_id = ? AND risk_level IN ('high', 'critical')",
            (professional_id,)
        ).fetchone()[0]
        
        # Get today's sessions
        today_start = time.time() - (time.time() % 86400)  # Start of today
        today_sessions = conn.execute(
            "SELECT COUNT(*) FROM automated_bookings WHERE professional_id = ? AND created_ts >= ?",
            (professional_id, today_start)
        ).fetchone()[0]
        
        # Get unread notifications
        unread_notifications = conn.execute(
            "SELECT COUNT(*) FROM professional_notifications WHERE professional_id = ? AND is_read = 0",
            (professional_id,)
        ).fetchone()[0]
        
        return jsonify({
            "total_sessions": total_sessions,
            "pending_sessions": pending_sessions,
            "confirmed_sessions": confirmed_sessions,
            "high_risk_sessions": high_risk_sessions,
            "today_sessions": today_sessions,
            "unread_notifications": unread_notifications
        })
    finally:
        conn.close()

@app.route('/professional/sessions', methods=['GET'])
def get_professional_sessions():
    """Get professional's assigned sessions"""
    professional_id = request.args.get('id')
    if not professional_id:
        return jsonify({"error": "Professional ID required"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        query = """
            SELECT 
                ab.*,
                u.fullname as user_fullname,
                u.email as user_email,
                u.telephone as user_phone,
                u.province as user_province,
                u.district as user_district,
                (u.district || ', ' || u.province) as user_location
            FROM automated_bookings ab
            LEFT JOIN users u ON ab.user_account = u.username
            WHERE ab.professional_id = ?
            ORDER BY ab.created_ts DESC
        """
        
        cur = conn.execute(query, (professional_id,))
        rows = cur.fetchall()
        
        sessions = []
        columns = [desc[0] for desc in cur.description]
        for row in rows:
            session = dict(zip(columns, row))
            sessions.append(session)
        
        return jsonify({"sessions": sessions})
    finally:
        conn.close()

@app.route('/professional/sessions/<booking_id>/status', methods=['PUT'])
def update_session_status(booking_id: str):
    """Update session status (accept/decline)"""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    status = data.get('status')  # 'accepted' or 'declined'
    if status not in ['accepted', 'declined']:
        return jsonify({"error": "Invalid status"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # Update booking status
        conn.execute(
            "UPDATE automated_bookings SET booking_status = ?, updated_ts = ? WHERE booking_id = ?",
            (status, time.time(), booking_id)
        )
        conn.commit()
        
        return jsonify({"ok": True, "message": f"Session {status} successfully"})
    finally:
        conn.close()

@app.route('/professional/sessions/<booking_id>/notes', methods=['POST'])
def add_session_notes(booking_id: str):
    """Add notes to a session"""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    notes = data.get('notes', '')
    treatment_plan = data.get('treatment_plan', '')
    
    conn = sqlite3.connect(DB_FILE)
    try:
        # Update booking with notes
        conn.execute(
            "UPDATE automated_bookings SET session_notes = ?, treatment_plan = ?, updated_ts = ? WHERE booking_id = ?",
            (notes, treatment_plan, time.time(), booking_id)
        )
        conn.commit()
        
        return jsonify({"ok": True, "message": "Session notes added successfully"})
    finally:
        conn.close()

@app.route('/professional/users', methods=['GET'])
def get_professional_users():
    """Get all users assigned to this professional"""
    professional_id = request.args.get('id')
    if not professional_id:
        return jsonify({"error": "Professional ID required"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        query = """
            SELECT DISTINCT
                u.*,
                COUNT(ab.booking_id) as total_sessions,
                MAX(ab.risk_level) as highest_risk_level,
                MAX(ab.created_ts) as last_session_date
            FROM users u
            INNER JOIN automated_bookings ab ON u.username = ab.user_account
            WHERE ab.professional_id = ?
            GROUP BY u.username
            ORDER BY last_session_date DESC
        """
        
        cur = conn.execute(query, (professional_id,))
        rows = cur.fetchall()
        
        users = []
        columns = [desc[0] for desc in cur.description]
        for row in rows:
            user = dict(zip(columns, row))
            users.append(user)
        
        return jsonify({"users": users})
    finally:
        conn.close()

@app.route('/professional/notifications', methods=['GET'])
def get_professional_notifications():
    """Get professional notifications"""
    professional_id = request.args.get('id')
    if not professional_id:
        return jsonify({"error": "Professional ID required"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    try:
        query = """
            SELECT pn.*, ab.user_account, ab.risk_level
            FROM professional_notifications pn
            LEFT JOIN automated_bookings ab ON pn.booking_id = ab.booking_id
            WHERE pn.professional_id = ?
            ORDER BY pn.created_ts DESC
            LIMIT 50
        """
        
        cur = conn.execute(query, (professional_id,))
        rows = cur.fetchall()
        
        notifications = []
        columns = [desc[0] for desc in cur.description]
        for row in rows:
            notification = dict(zip(columns, row))
            notifications.append(notification)
        
        return jsonify({"notifications": notifications})
    finally:
        conn.close()

@app.route('/professional/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id: int):
    """Mark notification as read"""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute(
            "UPDATE professional_notifications SET is_read = 1 WHERE id = ?",
            (notification_id,)
        )
        conn.commit()
        
        return jsonify({"ok": True, "message": "Notification marked as read"})
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="AIMHSA Unified Launcher - Single Port")
    parser.add_argument("--port", "-p", type=int, default=SERVER_PORT, help=f"Port to run on (default: {SERVER_PORT})")
    parser.add_argument("--host", default=SERVER_HOST, help=f"Host to bind to (default: {SERVER_HOST})")
    parser.add_argument("--skip-ollama-test", action="store_true", help="Skip Ollama connection test")
    args = parser.parse_args()
    
    print("="*60)
    print("🧠 AIMHSA - AI Mental Health Support Assistant")
    print("="*60)
    print(f"🌐 Running on: http://{args.host}:{args.port}")
    if openai_client:
        print(f"🤖 Ollama URL: {OLLAMA_BASE_URL}")
        print(f"🧠 Chat Model: {CHAT_MODEL}")
        print(f"🔍 Embed Model: {EMBED_MODEL}")
    elif ai_service:
        print("🤖 Using Hugging Face AI Service")
        print("🧠 Model: microsoft/DialoGPT-medium")
    else:
        print("⚠️ No AI service available - using fallback responses")
    print("="*60)
    
    # Test Ollama connection
    if not args.skip_ollama_test:
        if not test_ollama_connection():
            print("⚠️  Continuing without Ollama connection test...")
    
    # Initialize storage and embeddings
    print("🚀 Initializing AIMHSA...")
    init_storage()
    
    print("Available routes:")
    print(f"  - http://localhost:{args.port}/ (main chat)")
    print(f"  - http://localhost:{args.port}/landing (landing page)")
    print(f"  - http://localhost:{args.port}/login (login page)")
    print(f"  - http://localhost:{args.port}/register (register page)")
    print("="*60)
    
    # Open browser
    try:
        webbrowser.open(f"http://localhost:{args.port}")
    except Exception:
        pass
    
    print("✅ AIMHSA is ready!")
    print("Press Ctrl+C to stop")
    
    # Run Flask app
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == "__main__":
    main()