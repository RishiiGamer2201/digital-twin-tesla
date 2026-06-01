# Digital Twin of Nikola Tesla

**AIMS DTU Summer Project 2026**

A Digital Twin of Nikola Tesla, grounded in his actual writings, patents, and interviews. Ask Tesla about his inventions, philosophy, and vision for the future. Powered by RAG (Retrieval-Augmented Generation), long-term memory, and Google Gemini AI.

---

## Features

- **RAG Pipeline**: Retrieves context from Tesla's autobiography ("My Inventions"), Wikipedia, Wikiquote, and YouTube documentary transcripts before generating responses.
- **Persona Engine**: Deep Tesla persona with historically accurate voice, speech patterns, epistemic style, and timeline awareness (knowledge cutoff: 1943).
- **Conversation Memory**:
  - Short-term: Rolling buffer of recent messages for context continuity.
  - Long-term: SQLite-backed session summaries and extracted facts, retrieved by keyword relevance.
- **Voice I/O**: Browser-native voice input (Web Speech API microphone) and voice output (Speech Synthesis) with no server-side dependencies.
- **Memory Dashboard**: Live sidebar showing session count, message count, and past session summaries with delete functionality.
- **Source Citations**: Every response shows which Tesla writings were referenced, with expandable previews.
- **Premium Dark UI**: Custom HTML/CSS/JS frontend with glassmorphism, animations, and electric-blue accent theme.

---

## Architecture

```
User Query
    |
    v
[Flask Server] --> [RAG Retriever] --> [ChromaDB + sentence-transformers]
    |                                          |
    v                                          v
[Memory Manager] --> [Short-term Buffer]   [Relevant Chunks]
    |                [Long-term SQLite]        |
    v                                          v
[Prompt Builder] <-- [Tesla Persona Config]
    |
    v
[Gemini 2.5 Flash] --> Response --> [Sanitizer] --> User
```

---

## Tech Stack

| Component       | Technology                     | Cost  |
|-----------------|--------------------------------|-------|
| LLM             | Google Gemini 2.5 Flash        | Free  |
| Embeddings      | sentence-transformers (local)  | Free  |
| Vector Store    | ChromaDB (local)               | Free  |
| Memory          | SQLite                         | Free  |
| Web Server      | Flask                          | Free  |
| Frontend        | HTML / CSS / JavaScript        | Free  |
| Voice I/O       | Web Speech API (browser)       | Free  |
| Data Sources    | Public domain texts + YouTube  | Free  |
| **Total Cost**  |                                | **$0**|

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/RishiiGamer2201/digital-twin-tesla.git
cd digital-twin-tesla
```

### 2. Create virtual environment and install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env` and add your free Gemini API key from [aistudio.google.com](https://aistudio.google.com):

```
GEMINI_API_KEY=your_api_key_here
SCIENTIST_NAME=Nikola Tesla
```

### 4. Collect Tesla's writings (one-time)

```bash
python scripts/collect_data.py
```

This downloads Tesla's autobiography, Wikipedia data, Wikiquote, and YouTube transcripts.

### 5. Build the vector store (one-time)

```bash
python scripts/build_vectorstore.py
```

Chunks and indexes 188 documents into ChromaDB using local embeddings.

### 6. Run the application

```bash
python server.py
```

Open **http://localhost:5000** in your browser.

---

## Project Structure

```
digital-twin-tesla/
|-- server.py                   # Flask backend (API endpoints)
|-- static/
|   |-- index.html              # Frontend (HTML/CSS/JS)
|-- src/
|   |-- agent/
|   |   |-- twin.py             # Core Digital Twin agent
|   |-- data_collection/
|   |   |-- scraper.py          # Web scraper for Tesla texts
|   |   |-- youtube_loader.py   # YouTube transcript downloader
|   |   |-- pdf_loader.py       # PDF text extractor
|   |   |-- preprocessor.py     # Text chunking and metadata
|   |-- rag/
|   |   |-- embedder.py         # Local sentence-transformer embeddings
|   |   |-- vectorstore.py      # ChromaDB interface
|   |   |-- retriever.py        # High-level retrieval logic
|   |-- memory/
|   |   |-- short_term.py       # Conversation buffer
|   |   |-- long_term.py        # SQLite session/fact storage
|   |   |-- manager.py          # Unified memory orchestrator
|   |-- persona/
|   |   |-- tesla_config.py     # Tesla persona and system prompt
|   |   |-- prompt_builder.py   # Dynamic prompt assembly
|   |-- llm/
|       |-- gemini_client.py    # Gemini API wrapper
|-- scripts/
|   |-- collect_data.py         # Data collection runner
|   |-- build_vectorstore.py    # Vector store builder
|-- docs/
|   |-- architecture.md         # Architecture documentation
|   |-- design_decisions.md     # Design decisions
|-- tests/
|   |-- sample_conversations.md # Example conversations
|-- requirements.txt
|-- setup.py
|-- .env.example
|-- .gitignore
|-- README.md
```

---

## API Endpoints

| Method | Endpoint             | Description                    |
|--------|----------------------|--------------------------------|
| GET    | `/`                  | Serve the frontend             |
| POST   | `/api/chat`          | Send a message, get response   |
| GET    | `/api/memory`        | Get memory dashboard stats     |
| POST   | `/api/session/end`   | End session, save to memory    |
| POST   | `/api/session/clear` | Clear chat without saving      |
| POST   | `/api/session/delete`| Delete a past session          |

---

## Sample Questions to Test

1. "Tell me about your autobiography My Inventions"
2. "How did you discover the rotating magnetic field?"
3. "What do you think about Thomas Edison?"
4. "How does a Tesla coil work? Explain it simply."
5. "What do you think about the internet and smartphones?" (timeline test)
6. "My name is Sagar and I study at DTU" followed by "Do you remember my name?"

---

## Deliverables Checklist

- [x] Data Collection Pipeline (scraper, YouTube, PDF, preprocessor)
- [x] RAG System (ChromaDB + sentence-transformers + retriever)
- [x] Persona Engine (Tesla system prompt + prompt builder)
- [x] Memory System (short-term buffer + long-term SQLite)
- [x] LLM Integration (Gemini 2.5 Flash)
- [x] Web Frontend (HTML/CSS/JS with Flask backend)
- [x] Voice I/O (Web Speech API)
- [x] Memory Dashboard (session stats + delete)
- [x] Source Citations
- [x] Documentation

---

## Credits

- **Tesla's Writings**: Project Gutenberg, Wikiquote, Wikipedia (public domain)
- **LLM**: Google Gemini 2.5 Flash (free tier)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (MIT License)
- **Vector Store**: ChromaDB (Apache 2.0)

---

## License

This project is for educational purposes as part of the AIMS DTU Summer 2026 curriculum.
