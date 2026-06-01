# Architecture — Digital Twin of Nikola Tesla

## System Architecture Diagram

```mermaid
graph TB
    subgraph UI["Streamlit UI Layer"]
        Chat["Chat Interface"]
        MemDash["Memory Dashboard"]
        Voice["Voice I/O"]
        Sources["Source Citations"]
    end

    subgraph Agent["Digital Twin Agent"]
        Twin["twin.py<br/>Core Orchestrator"]
    end

    subgraph Persona["Persona Layer"]
        Config["tesla_config.py<br/>System Prompt + Metadata"]
        Builder["prompt_builder.py<br/>Dynamic Prompt Assembly"]
    end

    subgraph RAG["RAG Pipeline"]
        Embedder["embedder.py<br/>sentence-transformers<br/>all-MiniLM-L6-v2"]
        VStore["vectorstore.py<br/>ChromaDB<br/>Local Persistence"]
        Retriever["retriever.py<br/>Similarity Search"]
    end

    subgraph Memory["Memory System"]
        STM["short_term.py<br/>Conversation Buffer<br/>Last 20 messages"]
        LTM["long_term.py<br/>SQLite Database<br/>Session Summaries + Facts"]
        Manager["manager.py<br/>Unified Interface"]
    end

    subgraph LLM["LLM Layer"]
        Gemini["gemini_client.py<br/>Gemini 2.5 Flash<br/>Free Tier"]
    end

    subgraph Data["Data Sources"]
        Auto["My Inventions<br/>Autobiography 1919"]
        Articles["Published Articles<br/>1890-1910"]
        Quotes["Wikiquote<br/>200+ Quotes"]
        Wiki["Wikipedia<br/>Biography"]
        YT["YouTube<br/>Documentaries"]
    end

    Chat --> Twin
    Voice --> Twin
    Twin --> Builder
    Twin --> Retriever
    Twin --> Manager
    Twin --> Gemini

    Builder --> Config
    Retriever --> VStore
    VStore --> Embedder
    Manager --> STM
    Manager --> LTM

    Twin --> Sources
    Twin --> MemDash
    Gemini --> Twin

    Data -.->|"One-time<br/>Collection"| VStore
```

## Data Flow

### Query Processing (per user message)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit UI
    participant A as Twin Agent
    participant R as RAG Retriever
    participant M as Memory Manager
    participant P as Prompt Builder
    participant G as Gemini 2.5 Flash

    U->>UI: Enter question
    UI->>A: chat(user_message)
    
    par Parallel Context Retrieval
        A->>R: retrieve(query, n=5)
        R-->>A: rag_context + sources
        A->>M: get_context_for_prompt(query)
        M-->>A: memory_context
    end
    
    A->>P: build_system_prompt(rag, memory)
    P-->>A: full_system_prompt
    
    A->>M: add_turn("user", message)
    A->>M: get_history()
    M-->>A: conversation_history
    
    A->>G: generate(system_prompt, history)
    G-->>A: response_text
    
    A->>M: add_turn("assistant", response)
    A-->>UI: response + sources
    UI-->>U: Display response + citations
```

## Component Details

### 1. Persona Layer
The persona is the creative core. `tesla_config.py` contains:
- **System prompt**: ~3000 tokens of detailed personality, speech patterns, epistemic style, teaching methods
- **Timeline awareness**: Knowledge cutoff at January 1943
- **Metadata**: Biographical facts, institutions, notable works

### 2. RAG Pipeline
- **Embedder**: Uses `all-MiniLM-L6-v2` (384 dimensions) for fast, local embeddings
- **Vector Store**: ChromaDB with cosine similarity, persistent local storage
- **Retriever**: Returns top-5 relevant chunks with formatted source labels

### 3. Memory System
- **Short-term**: Rolling buffer of last 20 messages within a session
- **Long-term**: SQLite database storing session summaries, topics, and entities
- **Summarization**: Uses Gemini to generate structured summaries at end of each session

### 4. LLM Integration
- Gemini 2.5 Flash via Google AI Studio free tier
- 15 requests per minute, 1500 per day
- System instruction support for persona injection
