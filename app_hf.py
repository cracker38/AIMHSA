from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import json
import numpy as np
import os
# Replace ollama import with OpenAI client
from openai import OpenAI
from translation_service import translation_service

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client for Ollama with error handling
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")

try:
    openai_client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=OLLAMA_API_KEY
    )
    print("✅ OpenAI client initialized (Ollama)")
except Exception as e:
    print(f"⚠️ Failed to initialize OpenAI client: {e}")
    openai_client = None

# Load embeddings once at startup with error handling
def load_embeddings():
    try:
        with open('storage/embeddings.json', 'r') as f:
            chunks = json.load(f)
        chunk_texts = [c["text"] for c in chunks]
        chunk_sources = [{"source": c["source"], "chunk": c["chunk"]} for c in chunks]
        chunk_embeddings = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        print(f"✅ Loaded {len(chunks)} embeddings")
        return chunks, chunk_texts, chunk_sources, chunk_embeddings
    except FileNotFoundError:
        print("⚠️ Embeddings file not found - RAG features disabled")
        return [], [], [], None
    except Exception as e:
        print(f"⚠️ Error loading embeddings: {e}")
        return [], [], [], None

chunks, chunk_texts, chunk_sources, chunk_embeddings = load_embeddings()

def get_rag_response(query):
    """Get RAG response for a query using OpenAI client"""
    # If OpenAI client or embeddings not available, provide helpful fallback response
    if openai_client is None or chunk_embeddings is None:
        fallback_responses = {
            'greeting': "Hello! I'm AIMHSA, your mental health companion for Rwanda. How can I support you today?",
            'default': "I understand you're reaching out for support. I'm here to help with your mental health concerns. Could you tell me more about what's troubling you?"
        }
        
        query_lower = query.lower().strip()
        if any(word in query_lower for word in ['hello', 'hi', 'good morning', 'good evening', 'greetings']):
            return fallback_responses['greeting']
        return fallback_responses['default']
    
    try:
        # Get query embedding using OpenAI client
        response = openai_client.embeddings.create(
            model='nomic-embed-text',
            input=query
        )
        q_emb = np.array([response.data[0].embedding], dtype=np.float32)
        
        # Check dimensions
        if q_emb.shape[1] != chunk_embeddings.shape[1]:
            return "I'm sorry, there's a technical issue with the system. Please try rephrasing your question."
        
        # Find similar chunks
        doc_norm = chunk_embeddings / np.linalg.norm(chunk_embeddings, axis=1, keepdims=True)
        q_norm = q_emb[0] / np.linalg.norm(q_emb[0])
        similarities = np.dot(doc_norm, q_norm)
        top_indices = np.argsort(similarities)[-3:][::-1]
        
        # Build context
        context_parts = []
        for i, idx in enumerate(top_indices):
            context_parts.append(f"[{i+1}] {chunks[idx]['text']}")
        context = "\n\n".join(context_parts)
        
        # Get response from OpenAI client
        messages = [
            {"role": "system", "content": "You are AIMHSA, a supportive mental-health companion for Rwanda. Be warm, brief, and evidence-informed. Do NOT diagnose or prescribe medications. Encourage professional care when appropriate. Answer in clear, simple English only."},
            {"role": "user", "content": f"Answer the user's question using the CONTEXT below when relevant.\nIf the context is insufficient, be honest and provide safe, general guidance.\nIf the user greets you or asks for general help, respond helpfully without requiring context.\n\nQUESTION:\n{query}\n\nCONTEXT:\n{context}"}
        ]
        
        response = openai_client.chat.completions.create(
            model='llama3.2:3b', 
            messages=messages,
            temperature=0.2,
            top_p=0.9
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"RAG error: {e}")
        return "I'm here to help. Could you please rephrase your question? If this is an emergency, contact Rwanda's Mental Health Hotline at 105 or CARAES Ndera Hospital at +250 788 305 703."

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # 1) Detect user language (rw, fr, sw, en)
        user_lang = translation_service.detect_language(query) or 'en'

        # 2) Translate user query to English for RAG (source auto)
        query_en = query if user_lang == 'en' else translation_service.translate_text(query, 'en')

        # 3) Get RAG response in English only
        answer_en = get_rag_response(query_en)

        # 4) Translate back to user's language if needed
        answer = answer_en if user_lang == 'en' else translation_service.translate_text(answer_en, user_lang)
        
        return jsonify({
            "answer": answer,
            "id": "working-api"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/healthz', methods=['GET'])
def health():
    return jsonify({"ok": True})

# Serve frontend files
@app.route('/')
def index():
    return send_file('chatbot/index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from chatbot directory"""
    return send_from_directory('chatbot', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory('chatbot/js', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory('chatbot', filename)

if __name__ == '__main__':
    print("="*60)
    print("🧠 AIMHSA - AI Mental Health Support Assistant")
    print("="*60)
    
    if openai_client:
        print("✅ Ollama OpenAI Client: Available")
    else:
        print("⚠️ Ollama OpenAI Client: Not available")
    
    if chunk_embeddings is not None:
        print(f"✅ Embeddings: Loaded ({len(chunks)} chunks)")
    else:
        print("⚠️ Embeddings: Not available - using fallback responses")
    
    print("="*60)
    print("Starting AIMHSA API on port 7860...")
    print("="*60)
    
    app.run(host='0.0.0.0', port=7860, debug=False)