# Design Decisions -- Digital Twin of Nikola Tesla

## Why Nikola Tesla?

Nikola Tesla was chosen as the scientist for this Digital Twin for several compelling reasons:

1. **Distinctive Voice**: Tesla had a uniquely formal, visionary speaking style. His Victorian-era English combined with Serbian heritage creates a highly recognizable persona that an LLM can emulate effectively.

2. **Public Domain Material**: Tesla's autobiography *"My Inventions"* (1919) is in the public domain. His published articles, patents, and interview transcripts are freely available online.

3. **Rich Biographical Record**: Tesla's life is exceptionally well-documented, from his childhood visions in Smiljan to his final years at the New Yorker Hotel. This gives the RAG pipeline substantial material to ground responses in.

4. **Technical Depth**: Tesla's work spans AC power systems, high-frequency phenomena, wireless communication, and early robotics. This provides deep technical content for advanced questions.

5. **Cultural Impact**: Tesla is widely recognized and admired, making the Digital Twin immediately engaging to users.

---

## Why Flask over Streamlit?

The project originally used Streamlit but was migrated to Flask + vanilla HTML/CSS/JS. Here is why:

| Factor | Flask + HTML/CSS/JS | Streamlit |
|---|---|---|
| Streaming | Full SSE support, real-time tokens | Limited, reruns entire script |
| Control | Complete control over UI/UX | Constrained to Streamlit widgets |
| Voice | Browser Web Speech API (native) | Requires server-side audio processing |
| Modals | Native overlay modals | Not natively supported |
| Performance | No full-page reruns | Reruns entire script on every interaction |
| Canvas/Graphs | Full Canvas API access | Requires third-party components |
| Mobile | Responsive CSS with media queries | Limited responsive control |
| Deployment | Standard WSGI, any hosting | Requires Streamlit Cloud or server |

**Decision**: Flask provides the flexibility needed for streaming responses, interactive modals (timeline, quiz, debate, knowledge graph), and browser-native voice. Streamlit's rerun model was particularly problematic for voice output and streaming.

---

## Why sentence-transformers over API Embeddings?

| Factor | sentence-transformers | API Embeddings (e.g., OpenAI) |
|---|---|---|
| Cost | Free | $0.0001/1K tokens |
| Privacy | All data stays local | Data sent to cloud |
| Speed | ~50ms per batch locally | Network latency + processing |
| Quality | Good for retrieval (384 dims) | Slightly better (1536 dims) |
| Setup | `pip install` only | API key + billing required |

**Decision**: For a free-tier project with local data, sentence-transformers provides sufficient quality with zero cost and complete privacy.

---

## Why ChromaDB over Pinecone/Weaviate?

- **Zero cost**: No cloud hosting fees
- **Zero config**: No server to run, just `PersistentClient(path=".chroma")`
- **Python-native**: Integrates directly with our embedding pipeline
- **Persistent**: Data survives between runs automatically
- **Sufficient scale**: For ~500-2000 document chunks, ChromaDB is more than adequate
- **Runtime expansion**: Supports adding new documents (PDF uploads) without rebuilding

---

## Why SQLite for Long-Term Memory?

- **Built into Python**: No external dependency or server needed
- **Persistent**: Survives app restarts automatically
- **Simple**: Standard SQL for session and fact storage
- **Lightweight**: Single file (`memory.db`), easy to back up or reset
- **Sufficient**: For storing conversation summaries and key facts, a full database system like PostgreSQL would be overkill

---

## Chunking Strategy

**Parameters**: 512 words per chunk, 64-word overlap

**Rationale**:
- **512 words** (~400 tokens): Fits well within the embedding model's context window while containing enough content for meaningful retrieval
- **64-word overlap**: Ensures that concepts split across chunk boundaries are still retrievable from either chunk
- **Word-based**: Simpler and faster than token-based chunking, with negligible quality difference for English text

---

## Persona Engineering: System Prompt > Fine-tuning

For this use case, a detailed system prompt is superior to fine-tuning because:

1. **No training data needed**: Fine-tuning requires thousands of examples; we don't have thousands of Tesla Q&A pairs
2. **Immediate iteration**: We can adjust Tesla's personality by editing text, not retraining a model
3. **Assignment requirement**: The project requires Gemini 2.5 Flash, which doesn't support fine-tuning on the free tier
4. **Sufficient quality**: Modern LLMs respond remarkably well to detailed persona instructions
5. **Transparency**: The entire persona definition is readable in `tesla_config.py`

---

## Streaming Architecture: SSE over WebSockets

**Why SSE (Server-Sent Events)?**

| Factor | SSE | WebSockets |
|---|---|---|
| Complexity | Simple HTTP response | Requires connection upgrade |
| Flask support | Native (Response generator) | Requires flask-socketio |
| Unidirectional | Perfect for token streaming | Overkill, we only stream server to client |
| Reconnection | Built-in auto-reconnect | Must implement manually |
| Debugging | Visible in browser dev tools | Harder to inspect |

**Decision**: SSE is simpler, requires no additional dependencies, and is ideal for our use case (server streams tokens to client). WebSockets would add unnecessary complexity.

**Implementation**: The backend uses Flask's `Response` with a generator function and `text/event-stream` content type. The frontend uses the Fetch API's `ReadableStream` reader (not `EventSource`, which doesn't support POST bodies).

---

## Confidence Badge System

**How confidence is computed:**
1. ChromaDB returns cosine distances for each retrieved chunk
2. Distances are converted to similarity scores: `similarity = 1 - distance`
3. The average similarity across top-5 results determines the confidence level:
   - **Grounded** (> 0.5): Response is strongly supported by source material
   - **Inferred** (0.3 - 0.5): Some relevant sources found, but response involves inference
   - **Speculative** (< 0.3): Little to no relevant source material; response relies on persona

**Why these thresholds?** Based on empirical testing with the MiniLM embedding model and Tesla's corpus. Questions about topics covered in "My Inventions" typically score > 0.6, while post-1943 topics score < 0.2.

---

## Emotion Detection Approach

**Method**: Post-generation classification via a separate Gemini call.

**Why not sentiment analysis libraries?** Tesla's emotional range (excited about inventions, bitter about Edison, nostalgic about Serbia) doesn't map well to standard positive/negative sentiment. A custom 5-class classification (excited, bitter, nostalgic, philosophical, neutral) better captures the nuanced emotional palette of Tesla's persona.

**Cost**: One additional Gemini API call per message (~0.1s). Acceptable given the free tier limit of 15 RPM.

---

## Topic Suggestions Design

**Method**: After generating Tesla's response, a separate Gemini call generates 3 follow-up questions based on the conversation context.

**Why Gemini-generated instead of hardcoded?** Dynamic suggestions respond to the actual conversation flow. If the user asks about the Tesla Coil, suggestions will be about resonance, high-frequency experiments, and Colorado Springs, not generic topics.

**UX Design**: Suggestions appear as rounded pill buttons below the message. Clicking one sends it as a new message, creating a natural exploration flow. Limited to 3 to avoid overwhelming the user.

---

## Edison Persona for Debate Mode

**Design Principles:**
- Historically accurate, not a caricature
- Edison was brilliant in his own way: practical, tenacious, commercially savvy
- He genuinely believed DC was safer (and it was, for short distances)
- His "brute force" method was actually systematic empirical testing
- He was competitive but also respected by peers

**Voice differentiation from Tesla:**
- Edison: plain, direct, American English. Business metaphors.
- Tesla: formal, eloquent, Victorian. Nature metaphors.

**Formatting**: Both personas are constrained to ASCII-only punctuation (no em dashes, no en dashes) to maintain consistent text rendering.

---

## Knowledge Graph: Canvas over D3.js

**Why plain Canvas instead of D3.js?**
- **Zero dependencies**: No CDN or npm package needed
- **Simpler code**: ~60 lines for a basic force-directed layout
- **Sufficient for ~20 nodes**: D3.js is overkill for a small, static graph
- **Faster loading**: No external library to download
- **Interactive**: Click events on canvas nodes still work for navigation

**Layout algorithm**: Simple force-directed simulation (80 iterations):
- Repulsion: nodes push apart when closer than 100px
- Attraction: connected nodes pull toward 120px distance
- Boundary clamping: nodes stay within canvas bounds

---

## Voice Architecture: Browser APIs over Server-Side

**Why Web Speech API instead of gTTS + SpeechRecognition?**

| Factor | Web Speech API | Server-side (gTTS/SpeechRecognition) |
|---|---|---|
| Latency | Instant (browser-native) | Network round-trip + processing |
| Dependencies | None (built into browser) | pip packages + ffmpeg |
| Format issues | None | WAV/MP3/M4A conversion needed |
| Cost | Free | Free but more complex |
| Reliability | Very high in Chrome/Edge | Audio format bugs, temp file issues |

**Decision**: The original Streamlit version used server-side voice (gTTS for output, SpeechRecognition for input). This caused format conversion issues (M4A to WAV) and audio persistence bugs. Browser-native Web Speech API eliminated all of these problems with zero server-side dependencies.

---

## UI Design Choices

### Color System
- **Dark theme (default)**: Deep navy (#06060f) with electric blue accents (#00d4ff). Evokes Tesla's electrical experiments.
- **Light theme**: Clean white (#f0f2f8) with deeper blue accents (#0077cc). For users who prefer light mode.
- **CSS custom properties**: All colors defined as variables, enabling instant theme switching.

### Typography
- **Playfair Display** (serif): Used for headings and the brand title. Gives a Victorian-era feel matching Tesla's time period.
- **Inter** (sans-serif): Used for body text. Clean, modern, highly readable at small sizes.

### Layout
- **Sidebar + main content**: Classic dashboard layout. Sidebar contains controls and stats; main area is the chat.
- **Modal overlays**: Timeline, quiz, debate, and knowledge graph open as centered modals over the chat. This keeps the chat always accessible underneath.
- **Toolbar**: Row of pill buttons below the header for quick access to interactive features.

### Animations
- **electricPulse**: Brand title glows like electricity (text-shadow animation)
- **fadeInUp**: Messages slide up and fade in when added
- **bounce**: Thinking indicator dots pulse
- **micPulse**: Recording button pulses red
- All transitions: 0.2-0.3s ease for smooth state changes

### Mobile Strategy
- Sidebar hidden by default on screens < 768px
- Hamburger menu slides sidebar in as overlay
- Backdrop closes sidebar on tap
- All modals and features remain functional on mobile

---

## PDF Upload: Runtime Knowledge Expansion

**Why allow PDF uploads?**

The base knowledge base (188 documents) covers Tesla's most well-known works. But researchers or students might have access to:
- Tesla's lesser-known patents
- Academic papers about Tesla
- Recently digitized historical documents
- Their own study notes about Tesla

**Processing pipeline:**
1. File uploaded via multipart form
2. pypdf extracts text from all pages
3. preprocessor chunks text (512 words, 64 overlap)
4. Each chunk gets metadata: source_type="user_upload", work=filename
5. Embeddings generated and added to ChromaDB
6. Future queries will retrieve from uploaded material

**Safety**: Only PDF files accepted. Text extraction is sandboxed to pypdf. No arbitrary code execution.
