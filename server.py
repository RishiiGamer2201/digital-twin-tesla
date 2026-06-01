"""
Flask backend for the Nikola Tesla Digital Twin.
Serves the HTML frontend and provides REST API endpoints.
"""
import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify, send_from_directory, Response
from src.agent.twin import DigitalTwin
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static")

# Initialize the Digital Twin once
print("Loading Digital Twin of Nikola Tesla...")
twin = DigitalTwin()
print("Digital Twin ready.")


# ============================================================
# STATIC FILES
# ============================================================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ============================================================
# CHAT ENDPOINTS
# ============================================================

@app.route("/api/chat", methods=["POST"])
def chat():
    """Process a chat message and return Tesla's response (non-streaming)."""
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        response_text, rag_sources = twin.chat(user_message)
        sources = _format_sources(rag_sources)
        return jsonify({
            "response": response_text,
            "sources": sources,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Stream Tesla's response via Server-Sent Events."""
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    def generate():
        try:
            for event_type, event_data in twin.chat_stream(user_message):
                payload = json.dumps(event_data, ensure_ascii=True)
                yield f"event: {event_type}\ndata: {payload}\n\n"
        except Exception as e:
            error_payload = json.dumps({"error": str(e)}, ensure_ascii=True)
            yield f"event: error\ndata: {error_payload}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# ============================================================
# MEMORY ENDPOINTS
# ============================================================

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


# ============================================================
# SESSION ENDPOINTS
# ============================================================

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

# ============================================================
# QUIZ ENDPOINTS
# ============================================================

@app.route("/api/session/details", methods=["POST"])
def session_details():
    """Get full details of a past session including facts."""
    data = request.get_json()
    session_id = data.get("session_id", "")
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    try:
        details = twin.memory.ltm.get_session_details(session_id)
        if not details:
            return jsonify({"error": "Session not found"}), 404
        return jsonify({
            "id": details.get("id", ""),
            "timestamp": details.get("timestamp", ""),
            "summary": details.get("summary", ""),
            "topics": details.get("topics", "[]"),
            "entities": details.get("entities", "[]"),
            "message_count": details.get("message_count", 0),
            "user_name": details.get("user_name", ""),
            "facts": [
                {
                    "content": f.get("content", ""),
                    "category": f.get("category", ""),
                    "importance": f.get("importance", 0.5),
                }
                for f in details.get("facts", [])
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/quiz/generate", methods=["POST"])
def quiz_generate():
    """Generate a quiz question about Tesla / electrical engineering."""
    data = request.get_json() or {}
    topic = data.get("topic", "")
    try:
        quiz = twin.generate_quiz(topic)
        return jsonify(quiz)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/quiz/check", methods=["POST"])
def quiz_check():
    """Check a quiz answer and return Tesla-style feedback."""
    data = request.get_json()
    question = data.get("question", "")
    user_answer = data.get("user_answer", "")
    correct_answer = data.get("correct_answer", "")
    try:
        result = twin.check_quiz(question, user_answer, correct_answer)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# DEBATE ENDPOINT
# ============================================================

@app.route("/api/debate", methods=["POST"])
def debate():
    """Generate a Tesla vs Edison debate on a given topic."""
    data = request.get_json()
    topic = data.get("topic", "AC vs DC power")
    try:
        result = twin.debate(topic)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# EXPORT ENDPOINT
# ============================================================

@app.route("/api/export", methods=["POST"])
def export_chat():
    """Export conversation as a downloadable markdown file."""
    data = request.get_json()
    messages = data.get("messages", [])
    fmt = data.get("format", "markdown")

    lines = []
    lines.append("# Conversation with Nikola Tesla")
    lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "assistant":
            lines.append(f"**Nikola Tesla:**")
        else:
            lines.append(f"**You:**")
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

    md_content = "\n".join(lines)

    return Response(
        md_content,
        mimetype="text/markdown",
        headers={
            "Content-Disposition": "attachment; filename=tesla_conversation.md"
        }
    )


# ============================================================
# TIMELINE ENDPOINT
# ============================================================

@app.route("/api/timeline", methods=["GET"])
def timeline():
    """Return Tesla's life timeline events."""
    events = [
        {"year": 1856, "title": "Born in Smiljan",
         "description": "Born during a lightning storm in Smiljan, Austrian Empire (modern-day Croatia)."},
        {"year": 1875, "title": "Graz Polytechnic",
         "description": "Enrolled at Austrian Polytechnic in Graz to study engineering."},
        {"year": 1882, "title": "Budapest Revelation",
         "description": "While walking in Budapest, Tesla visualized the rotating magnetic field concept."},
        {"year": 1884, "title": "Arrived in America",
         "description": "Immigrated to New York with 4 cents and a letter of recommendation to Edison."},
        {"year": 1885, "title": "Left Edison's Company",
         "description": "Parted ways with Edison over a dispute about promised payment for improvements."},
        {"year": 1887, "title": "Tesla Electric Company",
         "description": "Founded his own company and filed patents for AC induction motors."},
        {"year": 1888, "title": "Westinghouse Partnership",
         "description": "Licensed AC patents to George Westinghouse for $60,000 plus royalties."},
        {"year": 1891, "title": "Tesla Coil Invented",
         "description": "Invented the Tesla coil and demonstrated wireless energy transfer."},
        {"year": 1893, "title": "Chicago World's Fair",
         "description": "AC power illuminated the World's Columbian Exposition, proving its superiority."},
        {"year": 1895, "title": "Niagara Falls Power",
         "description": "AC generators at Niagara Falls began powering Buffalo, New York."},
        {"year": 1899, "title": "Colorado Springs",
         "description": "Conducted high-voltage experiments, produced artificial lightning, claimed signals from Mars."},
        {"year": 1901, "title": "Wardenclyffe Tower",
         "description": "Began construction of the Wardenclyffe wireless transmission tower on Long Island."},
        {"year": 1905, "title": "Wardenclyffe Abandoned",
         "description": "J.P. Morgan withdrew funding. The dream of worldwide wireless power collapsed."},
        {"year": 1917, "title": "AIEE Edison Medal",
         "description": "Received the Edison Medal, the highest honor in electrical engineering."},
        {"year": 1934, "title": "Death Ray Claims",
         "description": "Announced a particle beam weapon concept, which the press called a death ray."},
        {"year": 1943, "title": "Passed Away",
         "description": "Died alone in Room 3327 of the New Yorker Hotel at age 86."},
    ]
    return jsonify({"events": events})


# ============================================================
# PDF UPLOAD ENDPOINT
# ============================================================

@app.route("/api/upload-pdf", methods=["POST"])
def upload_pdf():
    """Upload a PDF, extract text, chunk it, and add to vector store."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    pdf_file = request.files["file"]
    if not pdf_file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    try:
        from pypdf import PdfReader
        from src.data_collection.preprocessor import word_chunks

        # Save to temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_file.save(tmp.name)
        tmp.close()

        # Extract text
        reader = PdfReader(tmp.name)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        os.unlink(tmp.name)

        if not full_text.strip():
            return jsonify({"error": "Could not extract text from PDF"}), 400

        # Chunk the text
        chunks = word_chunks(full_text, size=512, overlap=64)

        # Add to vector store
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "metadata": {
                    "source_type": "user_upload",
                    "work": pdf_file.filename,
                    "scientist": "Nikola Tesla",
                    "chunk_index": i,
                }
            })

        if documents:
            vs = twin.retriever.get_vectorstore()
            vs.add_documents(documents)

        return jsonify({
            "status": "success",
            "chunks_added": len(documents),
            "filename": pdf_file.filename
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _format_sources(rag_sources):
    """Format RAG sources for API response."""
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
    return sources


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
