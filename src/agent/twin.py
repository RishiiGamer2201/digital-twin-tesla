"""
The Digital Twin Agent.
Ties together: persona, RAG, memory, and LLM.
Main entry point for the application.
"""
from src.persona.prompt_builder import build_system_prompt
from src.persona.edison_config import EDISON_SYSTEM_PROMPT
from src.rag.retriever import Retriever
from src.memory.manager import MemoryManager
from src.llm.gemini_client import GeminiClient
from typing import List, Dict, Generator
import json


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

        # Step 5.5: Sanitize response
        response_text = self._sanitize(response_text)

        # Step 6: Update memory
        self.memory.add_turn("assistant", response_text)

        return response_text, rag_sources

    def chat_stream(self, user_message: str):
        """
        Generator that yields SSE events for streaming chat.
        Yields tuples of (event_type, data_dict).
        """
        # Step 1: RAG retrieval
        rag_context, rag_sources = self.retriever.retrieve(
            user_message, n_results=5
        )

        # Compute confidence from RAG scores
        confidence_level, confidence_score = self._compute_confidence(rag_sources)

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

        # Step 5: Stream response
        stream_response = self.llm.generate(
            system_prompt=system_prompt,
            messages=history,
            stream=True
        )

        full_response = ""
        for chunk in stream_response:
            if hasattr(chunk, 'text') and chunk.text:
                token = self._sanitize(chunk.text)
                full_response += token
                yield ("token", {"content": token})

        # Step 6: Update memory
        self.memory.add_turn("assistant", full_response)

        # Step 7: Yield metadata
        # Sources
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
        yield ("sources", {"sources": sources})

        # Confidence
        yield ("confidence", {
            "level": confidence_level,
            "score": confidence_score
        })

        # Emotion detection
        try:
            emotion = self._detect_emotion(full_response)
            yield ("emotion", {"emotion": emotion})
        except Exception:
            yield ("emotion", {"emotion": "neutral"})

        # Suggestions
        try:
            suggestions = self._generate_suggestions(full_response, user_message)
            yield ("suggestions", {"suggestions": suggestions})
        except Exception:
            yield ("suggestions", {"suggestions": []})

        yield ("done", {})

    def generate_quiz(self, topic: str = "") -> Dict:
        """Generate a quiz question about Tesla or electrical engineering."""
        topic_str = f" about {topic}" if topic else ""
        prompt = (
            f"Generate a multiple-choice quiz question{topic_str} related to "
            "Nikola Tesla, his inventions, or electrical engineering. "
            "Return ONLY valid JSON in this exact format, nothing else:\n"
            '{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], '
            '"correct_index": 0, "explanation": "...", "topic": "..."}'
        )
        raw = self.llm.generate_simple(prompt)
        raw = self._sanitize(raw)
        # Extract JSON from response
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            raw = raw.rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "question": "What year did Tesla patent the AC motor?",
                "options": ["A) 1882", "B) 1887", "C) 1891", "D) 1895"],
                "correct_index": 1,
                "explanation": "Tesla filed his AC motor patents in 1887 through the Tesla Electric Company.",
                "topic": "Patents"
            }

    def check_quiz(self, question: str, user_answer: str, correct_answer: str) -> Dict:
        """Grade a quiz answer in Tesla's voice."""
        prompt = (
            f"You are Nikola Tesla grading a student's answer.\n"
            f"Question: {question}\n"
            f"Student answered: {user_answer}\n"
            f"Correct answer: {correct_answer}\n"
            f"Is the student correct? Give brief feedback as Tesla would. "
            f"Do NOT use em dashes or en dashes. Use plain punctuation only. "
            f"Return ONLY valid JSON: "
            '{"correct": true/false, "feedback": "..."}'
        )
        raw = self.llm.generate_simple(prompt)
        raw = self._sanitize(raw)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            raw = raw.rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            return {
                "correct": is_correct,
                "feedback": "Correct, well done." if is_correct else "Not quite. Study further."
            }

    def debate(self, topic: str) -> Dict:
        """Generate Tesla and Edison responses to a debate topic."""
        # Tesla's response
        tesla_prompt = (
            f"You are Nikola Tesla. Give your position on this topic in 2-3 paragraphs: {topic}\n"
            "Be passionate and defend your views. Do NOT use em dashes or en dashes."
        )
        tesla_response = self._sanitize(self.llm.generate_simple(tesla_prompt))

        # Edison's response
        edison_prompt = (
            f"{EDISON_SYSTEM_PROMPT}\n\n"
            f"Give your position on this topic in 2-3 paragraphs: {topic}\n"
            f"Respond to Tesla's views if relevant. Be direct and practical."
        )
        edison_response = self._sanitize(self.llm.generate_simple(edison_prompt))

        return {
            "tesla_response": tesla_response,
            "edison_response": edison_response,
            "topic": topic
        }

    def _detect_emotion(self, response: str) -> str:
        """Detect emotional tone of Tesla's response."""
        prompt = (
            "Classify this text's emotional tone as exactly one word from: "
            "excited, bitter, nostalgic, philosophical, neutral\n\n"
            f"Text: {response[:500]}\n\nReturn only the single word."
        )
        result = self.llm.generate_simple(prompt).strip().lower()
        valid = {"excited", "bitter", "nostalgic", "philosophical", "neutral"}
        return result if result in valid else "neutral"

    def _generate_suggestions(self, response: str, user_message: str) -> List[str]:
        """Generate 3 follow-up question suggestions."""
        prompt = (
            "Given this conversation with Tesla, suggest 3 short follow-up questions "
            "a curious student might ask. Return ONLY the 3 questions, one per line, "
            "no numbering, no bullets.\n\n"
            f"User asked: {user_message[:200]}\n"
            f"Tesla replied: {response[:400]}"
        )
        result = self.llm.generate_simple(prompt)
        result = self._sanitize(result)
        lines = [l.strip() for l in result.strip().split("\n") if l.strip()]
        return lines[:3]

    def _compute_confidence(self, rag_sources) -> tuple:
        """Compute confidence level from RAG similarity scores."""
        if not rag_sources:
            return "speculative", 0.0
        scores = []
        for s in rag_sources:
            dist = s.get("distance", 1.0)
            # ChromaDB returns distance (lower = better), convert to similarity
            similarity = max(0, 1.0 - dist)
            scores.append(similarity)
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score > 0.5:
            return "grounded", round(avg_score, 2)
        elif avg_score > 0.3:
            return "inferred", round(avg_score, 2)
        else:
            return "speculative", round(avg_score, 2)

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
