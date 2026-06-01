"""
Thin wrapper around Google Gemini 2.5 Flash.
Uses the free tier (15 RPM, 1500 RPD) via Google AI Studio.
Model: gemini-2.5-flash
"""
import google.generativeai as genai
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in your .env file. "
                "Get it free at aistudio.google.com"
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def generate(
        self, system_prompt: str, messages: List[Dict], stream: bool = False
    ):
        """
        Generate response from Gemini.
        messages: list of {"role": "user"/"assistant", "content": text}
        """
        # Create model with system instruction (changes per call due to RAG/memory)
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=system_prompt
        )

        # Gemini uses "model" role, not "assistant"
        gemini_messages = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else m["role"]
            gemini_messages.append({
                "role": role,
                "parts": [m["content"]]
            })

        chat = model.start_chat(
            history=gemini_messages[:-1] if len(gemini_messages) > 1 else []
        )
        last_message = (
            gemini_messages[-1]["parts"][0] if gemini_messages else ""
        )
        response = chat.send_message(last_message, stream=stream)

        if stream:
            return response  # caller iterates
        return response.text

    def generate_simple(self, prompt: str) -> str:
        """Simple single-turn generation for internal tasks (e.g., summarization)."""
        response = self.model.generate_content(prompt)
        return response.text
