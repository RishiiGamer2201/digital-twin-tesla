"""
Rolling conversation buffer. Keeps last N messages in memory.
Provides short-term recall within a single session.
"""
from typing import List, Dict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ConversationBuffer:
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")

    def add(self, role: str, content: str):
        """Add a message to the conversation buffer."""
        self.messages.append(Message(role=role, content=content))
        if len(self.messages) > self.max_messages:
            # Keep most recent messages
            self.messages = self.messages[-self.max_messages:]

    def get_history(self) -> List[Dict]:
        """Return message history as list of dicts for LLM consumption."""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def format_for_prompt(self) -> str:
        """Format conversation history as readable text for injection into prompts."""
        if not self.messages:
            return ""
        lines = []
        for m in self.messages[-10:]:  # last 10 for prompt context
            prefix = "Visitor" if m.role == "user" else "Tesla"
            lines.append(f"{prefix}: {m.content}")
        return "\n".join(lines)

    def clear(self):
        """Clear the buffer and return old messages."""
        old_messages = self.messages.copy()
        self.messages = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        return old_messages
