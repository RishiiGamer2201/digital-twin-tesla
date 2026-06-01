# Architecture -- Digital Twin of Nikola Tesla

## High-Level System Architecture

```
+--------------------------------------------------+
|                   Browser                         |
|  +--------------------------------------------+  |
|  |           HTML/CSS/JS Frontend              |  |
|  |  +--------+ +----------+ +---------------+ |  |
|  |  |  Chat  | | Timeline | | Knowledge     | |  |
|  |  |  Panel | | Modal    | | Graph (Canvas)| |  |
|  |  +--------+ +----------+ +---------------+ |  |
|  |  +--------+ +----------+ +---------------+ |  |
|  |  | Quiz   | | Debate   | | PDF Upload    | |  |
|  |  | Modal  | | Modal    | | Modal         | |  |
|  |  +--------+ +----------+ +---------------+ |  |
|  |  +--------+ +---------+                    |  |
|  |  | Voice  | | Theme   |                    |  |
|  |  | I/O    | | Toggle  |                    |  |
|  |  +--------+ +---------+                    |  |
|  +--------------------------------------------+  |
|         |  REST/JSON + SSE (streaming)            |
+---------|-----------------------------------------+
          |
          v
+--------------------------------------------------+
|              Flask Server (server.py)             |
|                                                   |
|  Endpoints:                                       |
|  POST /api/chat/stream  --> SSE token stream      |
|  POST /api/chat         --> Non-streaming fallback|
|  POST /api/quiz/generate--> Quiz question         |
|  POST /api/quiz/check   --> Grade answer          |
|  POST /api/debate       --> Tesla vs Edison       |
|  POST /api/export       --> Markdown download     |
|  POST /api/upload-pdf   --> PDF processing        |
|  GET  /api/timeline     --> Life events           |
|  GET  /api/memory       --> Dashboard stats       |
|  POST /api/session/*    --> Session management    |
+--------------------------------------------------+
          |
          v
+--------------------------------------------------+
|            Digital Twin Agent (twin.py)           |
|                                                   |
|  Methods:                                         |
|  chat()           -- Full response + sources      |
|  chat_stream()    -- Generator yielding SSE events|
|  generate_quiz()  -- Quiz question via Gemini     |
|  check_quiz()     -- Grade answer in Tesla voice  |
|  debate()         -- Tesla + Edison responses      |
|  _detect_emotion()     -- Classify response tone  |
|  _generate_suggestions()-- Follow-up questions    |
|  _compute_confidence() -- RAG score analysis      |
+--------------------------------------------------+
     |           |            |            |
     v           v            v            v
+----------+ +----------+ +----------+ +----------+
|  Persona | |   RAG    | |  Memory  | |   LLM    |
|  Layer   | | Pipeline | |  System  | |  Layer   |
+----------+ +----------+ +----------+ +----------+
```

## Component Architecture

### 1. Frontend Layer (static/index.html)

Single-page application with embedded CSS and JavaScript.

**Chat System:**
- Messages rendered as DOM elements with role-based styling
- Streaming via Fetch API ReadableStream + SSE parsing
- Character-by-character typing animation (15ms delay)
- Auto-scrolling message container

**Interactive Features:**
- Timeline: Fetches events from `/api/timeline`, renders as vertical timeline with glowing dots
- Knowledge Graph: Canvas-based force-directed layout with ~18 nodes and ~24 edges
- Quiz: Modal with dynamic question loading, option buttons, score tracking
- Debate: Split-panel layout with separate persona colors

**UI System:**
- CSS custom properties for theming (dark/light)
- Glassmorphism effects (backdrop-filter, translucent backgrounds)
- Micro-animations (fadeInUp, electricPulse, bounce, micPulse)
- Responsive breakpoint at 768px with sidebar drawer

### 2. Server Layer (server.py)

Flask application serving static files and 13 REST endpoints.

**Streaming Architecture:**
```
Client                    Server
  |                         |
  |-- POST /api/chat/stream |
  |                         |
  |<-- event: token --------|  (repeated per chunk)
  |<-- event: sources ------|
  |<-- event: confidence ---|
  |<-- event: emotion ------|
  |<-- event: suggestions --|
  |<-- event: done ---------|
  |                         |
```

Each SSE event has the format:
```
event: token
data: {"content": "partial text"}

event: sources
data: {"sources": [{...}]}
```

### 3. Agent Layer (twin.py)

Central orchestrator connecting all subsystems.

**Chat Flow (streaming):**
1. RAG retrieval (5 chunks from ChromaDB)
2. Confidence score computation from RAG distances
3. Memory context retrieval (short-term + long-term)
4. System prompt assembly (persona + RAG + memory)
5. Gemini streaming generation (yields tokens)
6. Post-generation: emotion detection, suggestion generation
7. Memory update (add assistant turn)

**Quiz Flow:**
1. Gemini generates question with JSON output format
2. Frontend displays options
3. User selects answer
4. Gemini grades in Tesla's voice

**Debate Flow:**
1. Tesla response generated using Tesla persona
2. Edison response generated using Edison persona
3. Both returned simultaneously

### 4. Persona Layer

**Tesla Persona (tesla_config.py):**
- 3000+ token system prompt
- Voice patterns: formal Victorian English, Serbian references
- Epistemic style: visualization over experimentation
- Timeline awareness: 1856-1943
- Teaching style: analogies to nature, first principles
- Strict formatting rules: no emoji, no em dashes

**Edison Persona (edison_config.py):**
- Used only in debate mode
- Practical, business-minded, direct speech
- Defends DC power, skeptical of AC
- Values perspiration over inspiration
- Same formatting constraints

### 5. RAG Pipeline

```
User Query
    |
    v
[Embedder: all-MiniLM-L6-v2] --> 384-dim vector
    |
    v
[ChromaDB: cosine similarity search] --> Top 5 chunks
    |
    v
[Retriever: format with source labels] --> Context string
```

**Data Sources (188 documents):**
- "My Inventions" autobiography (Project Gutenberg)
- Wikipedia biography and technical articles
- Wikiquote (200+ quotes)
- YouTube documentary transcripts (8 videos)
- User-uploaded PDFs (added at runtime)

### 6. Memory System

```
         MemoryManager
            /    \
           /      \
   ShortTermBuffer  LongTermMemory
   (list, 20 msgs)  (SQLite DB)
                      /       \
                  sessions   facts
                  table      table
```

**Short-term flow:**
- add_turn() appends to rolling buffer
- format_for_prompt() returns last 10 messages as "Visitor/Tesla" pairs

**Long-term flow:**
- end_session() triggers Gemini summarization
- Summary + topics + entities stored in SQLite
- get_relevant_memories() does keyword search across past summaries
- delete_session() removes session and associated facts

### 7. LLM Layer (gemini_client.py)

**Two generation modes:**
- `generate(system_prompt, messages, stream)`: Full chat with system instruction, history, streaming support
- `generate_simple(prompt)`: Single-turn generation for internal tasks (summaries, emotion detection, suggestions)

**Gemini API usage:**
- Model: gemini-2.5-flash
- System instruction injected per-call (changes with RAG/memory context)
- Chat history formatted with "model" role (Gemini's convention)
- Streaming returns iterator of response chunks

## Data Flow Diagrams

### Streaming Chat (Primary Flow)

```
User types message
    |
    v
Frontend: POST /api/chat/stream {message}
    |
    v
Server: twin.chat_stream(message)
    |
    +---> RAG: retrieve(query, n=5) --> chunks + distances
    +---> Memory: get_context(query) --> past context
    +---> Prompt: build_system_prompt(rag, memory)
    +---> Memory: add_turn("user", message)
    +---> Gemini: generate(prompt, history, stream=True)
    |         |
    |         +---> yields token chunks --> SSE events
    |
    +---> Confidence: compute from RAG distances
    +---> Emotion: Gemini classifies tone
    +---> Suggestions: Gemini generates 3 follow-ups
    +---> Memory: add_turn("assistant", full_response)
    |
    v
Frontend: parses SSE events, renders tokens, shows metadata
```

### PDF Upload Flow

```
User selects PDF file
    |
    v
Frontend: FormData POST /api/upload-pdf
    |
    v
Server:
    +---> pypdf: extract text from all pages
    +---> preprocessor: word_chunks(text, 512, 64)
    +---> embedder: encode chunks
    +---> ChromaDB: add_documents(chunks + metadata)
    |
    v
Response: {status, chunks_added, filename}
```
