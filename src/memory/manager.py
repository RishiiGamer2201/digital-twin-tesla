"""
Unified memory manager. Orchestrates short-term + long-term memory.
Uses Gemini to generate session summaries at end of conversation.
"""
from .short_term import ConversationBuffer
from .long_term import LongTermMemory
from typing import List, Dict, Tuple
import json


class MemoryManager:
    def __init__(self, gemini_client=None):
        self.buffer = ConversationBuffer(max_messages=20)
        self.ltm = LongTermMemory()
        self.gemini = gemini_client  # Injected to avoid circular imports

    def add_turn(self, role: str, content: str):
        """Add a conversation turn to the buffer."""
        self.buffer.add(role, content)

    def get_context_for_prompt(self, query: str) -> str:
        """
        Assembles memory context to inject into the system prompt.
        Includes relevant past session summaries from long-term memory.
        """
        parts = []

        # Relevant long-term memories
        memories = self.ltm.get_relevant_memories(query, limit=2)
        if memories:
            mem_lines = []
            for m in memories:
                topics = json.loads(m.get("topics", "[]"))
                mem_lines.append(
                    f"- Previous session ({m['timestamp'][:10]}): "
                    f"{m['summary']} Topics: {', '.join(topics)}"
                )
            parts.append(
                "RELEVANT PAST CONVERSATIONS:\n" + "\n".join(mem_lines)
            )

        return "\n\n".join(parts) if parts else ""

    def end_session(self):
        """Called when user ends conversation. Summarizes and saves to LTM."""
        messages = self.buffer.messages
        if len(messages) < 2:
            return "Session too short to save."

        if self.gemini:
            history_text = "\n".join(
                f"{'Visitor' if m.role == 'user' else 'Tesla'}: {m.content}"
                for m in messages
            )
            summary_prompt = f"""Summarize this conversation in 2-3 sentences. 
Then list: topics discussed (comma-separated), and named entities/concepts (comma-separated).
Format:
SUMMARY: ...
TOPICS: ...
ENTITIES: ...

Conversation:
{history_text[:3000]}"""
            try:
                response = self.gemini.generate_simple(summary_prompt)
                lines = {
                    line.split(":")[0].strip(): ":".join(line.split(":")[1:]).strip()
                    for line in response.strip().split("\n") if ":" in line
                }
                summary = lines.get(
                    "SUMMARY", "Conversation about science and invention"
                )
                topics = [
                    t.strip()
                    for t in lines.get("TOPICS", "electrical engineering").split(",")
                ]
                entities = [
                    e.strip()
                    for e in lines.get("ENTITIES", "").split(",")
                ]
            except Exception:
                summary = "Conversation session"
                topics = ["electrical engineering"]
                entities = []
        else:
            summary = f"Session with {len(messages)} messages"
            topics = ["electrical engineering"]
            entities = []

        self.ltm.save_session(
            session_id=self.buffer.session_id,
            summary=summary,
            topics=topics,
            entities=entities,
            message_count=len(messages)
        )
        self.buffer.clear()
        return summary

    def get_history(self) -> List[Dict]:
        """Return current conversation history."""
        return self.buffer.get_history()
