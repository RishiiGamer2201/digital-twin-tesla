"""
Flask backend for the Nikola Tesla Digital Twin.
Serves the HTML frontend and provides REST API endpoints.
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify, send_from_directory
from src.agent.twin import DigitalTwin
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static")

# Initialize the Digital Twin once
print("Loading Digital Twin of Nikola Tesla...")
twin = DigitalTwin()
print("Digital Twin ready.")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Process a chat message and return Tesla's response."""
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        response_text, rag_sources = twin.chat(user_message)
        # Format sources for frontend
        sources = []
        if rag_sources:
            for s in rag_sources:
                meta = s.get("metadata", {})
                sources.append({
                    "work": meta.get("work", "Unknown source"),
                    "source_type": meta.get("source_type", ""),
                    "year": meta.get("year", ""),
                    "text_preview": s.get("text", "")[:200],
                })
        return jsonify({
            "response": response_text,
            "sources": sources,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/memory", methods=["GET"])
def memory_stats():
    """Return memory dashboard data."""
    try:
        stats = twin.get_memory_stats()
        return jsonify({
            "total_sessions": stats["total_sessions"],
            "current_messages": stats["current_session_messages"],
            "recent_sessions": [
                {
                    "id": s.get("id", ""),
                    "summary": s.get("summary", ""),
                    "timestamp": s.get("timestamp", ""),
                    "topics": s.get("topics", ""),
                }
                for s in stats.get("recent_sessions", [])
            ],
            "recent_facts": [
                {
                    "content": f.get("content", ""),
                    "category": f.get("category", ""),
                }
                for f in stats.get("recent_facts", [])
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/end", methods=["POST"])
def end_session():
    """End the current session and save to long-term memory."""
    try:
        summary = twin.end_session()
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/clear", methods=["POST"])
def clear_session():
    """Clear chat without saving."""
    try:
        twin.memory.buffer.clear()
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/delete", methods=["POST"])
def delete_session():
    """Delete a specific past session from long-term memory."""
    data = request.get_json()
    session_id = data.get("session_id", "")
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    try:
        deleted = twin.memory.ltm.delete_session(session_id)
        if deleted:
            return jsonify({"status": "deleted"})
        else:
            return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
