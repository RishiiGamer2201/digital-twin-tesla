"""
Dynamically assembles the full system prompt by combining:
- Base persona
- Retrieved context (RAG)
- Memory context
- Timeline context
"""
from .tesla_config import TESLA_SYSTEM_PROMPT, TESLA_METADATA


def build_system_prompt(rag_context: str = "", memory_context: str = "") -> str:
    prompt_parts = [TESLA_SYSTEM_PROMPT]

    if memory_context:
        prompt_parts.append(f"""
====================================
MEMORY: WHAT YOU KNOW ABOUT THIS PERSON
====================================
{memory_context}
        """)

    if rag_context:
        prompt_parts.append(f"""
====================================
YOUR OWN WRITINGS, PATENTS, AND LECTURES (use these to ground your answers)
====================================
{rag_context}

When these passages are relevant, draw from them naturally -
as if recalling what you wrote or demonstrated, not as if reading from a document.
        """)

    return "\n".join(prompt_parts)
