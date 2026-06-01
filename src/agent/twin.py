"""
The Digital Twin Agent.
Ties together: persona, RAG, memory, and LLM.
Main entry point for the application.
"""
from src.persona.prompt_builder import build_system_prompt
from src.rag.retriever import Retriever
from src.memory.manager import MemoryManager
from src.llm.gemini_client import GeminiClient
from typing import List, Dict, Generator


class DigitalTwin:
    def __init__(self):
        print("Initializing Digital Twin of Nikola Tesla...")
        self.llm = GeminiClient()
        self.retriever = Retriever()
        self.memory = MemoryManager(gemini_client=self.llm)
        print("Digital Twin ready. Tesla awaits your questions.")

    def chat(self, user_message: str, stream: bool = True):
        """
        Process a user message and return Tesla's response.
        1. Retrieve relevant RAG context
        2. Retrieve relevant memory context
        3. Build system prompt
        4. Generate response
        5. Update memory
        """
        # Step 1: RAG retrieval
        rag_context, rag_sources = self.retriever.retrieve(
            user_message, n_results=5
        )

        # Step 2: Memory context
        memory_context = self.memory.get_context_for_prompt(user_message)

        # Step 3: Build system prompt
        system_prompt = build_system_prompt(
            rag_context=rag_context,
            memory_context=memory_context
        )

        # Step 4: Add user message to buffer + get history
        self.memory.add_turn("user", user_message)
        history = self.memory.get_history()

        # Step 5: Generate
        response_text = self.llm.generate(
            system_prompt=system_prompt,
            messages=history,
            stream=False
        )

        # Step 5.5: Sanitize response (remove em/en dashes)
        response_text = self._sanitize(response_text)

        # Step 6: Update memory
        self.memory.add_turn("assistant", response_text)

        return response_text, rag_sources

    @staticmethod
    def _sanitize(text: str) -> str:
        """Remove em dashes, en dashes, and other non-ASCII punctuation."""
        text = text.replace("\u2014", ", ")   # em dash
        text = text.replace("\u2013", "-")    # en dash
        text = text.replace("\u2018", "'")    # left single quote
        text = text.replace("\u2019", "'")    # right single quote
        text = text.replace("\u201C", '"')    # left double quote
        text = text.replace("\u201D", '"')    # right double quote
        text = text.replace("\u2026", "...")   # ellipsis
        text = text.replace("\u00A0", " ")    # non-breaking space
        return text

    def end_session(self) -> str:
        """End the current session, saving summary to long-term memory."""
        return self.memory.end_session()

    def get_memory_stats(self) -> Dict:
        """Returns memory statistics for the dashboard."""
        sessions = self.memory.ltm.get_all_sessions()
        facts = self.memory.ltm.get_recent_facts()
        return {
            "total_sessions": len(sessions),
            "recent_sessions": sessions[:5],
            "recent_facts": facts,
            "current_session_messages": len(self.memory.buffer.messages)
        }
