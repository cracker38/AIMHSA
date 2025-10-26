from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
# Replace ollama import with OpenAI client
from openai import OpenAI
import os
from translation_service import translation_service

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client for Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")

openai_client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key=OLLAMA_API_KEY
)

# Load embeddings once at startup
def load_embeddings():
    with open('storage/embeddings.json', 'r') as f:
        chunks = json.load(f)
    chunk_texts = [c["text"] for c in chunks]
    chunk_sources = [{"source": c["source"], "chunk": c["chunk"]} for c in chunks]
    chunk_embeddings = np.array([c["embedding"] for c in chunks], dtype=np.float32)
    return chunks, chunk_texts, chunk_sources, chunk_embeddings

chunks, chunk_texts, chunk_sources, chunk_embeddings = load_embeddings()

def get_rag_response(query):
    """Get RAG response for a query using OpenAI client"""
    try:
        # Get query embedding using OpenAI client
        response = openai_client.embeddings.create(
            model='nomic-embed-text',
            input=query
        )
        q_emb = np.array([response.data[0].embedding], dtype=np.float32)
        
        # Check dimensions
        if q_emb.shape[1] != chunk_embeddings.shape[1]:
            return "I'm sorry, there's a technical issue with the system."
        
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

if __name__ == '__main__':
    print("Starting Working AIMHSA API...")
    print("RAG System: Ready")
    print("Embeddings: Loaded")
    print("Models: Available via OpenAI Client")
    app.run(host='0.0.0.0', port=7860, debug=True)

