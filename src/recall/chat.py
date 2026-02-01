"""Claude-powered chat for recall memories."""

import os
from typing import List

from .store import Memory


def chat_with_memories(
    question: str,
    memories: List[Memory],
    model: str = "claude-sonnet-4-20250514",
) -> str:
    """Send question to Claude with memory context."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Get your API key at https://console.anthropic.com/"
        )

    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")

    # Build context from memories
    if memories:
        memory_context = "\n\n".join(
            f"[Memory #{m.id} | Score: {m.score:.2f}]\n{m.content}" for m in memories
        )
        system_prompt = (
            "You are a helpful assistant that answers questions based on the user's "
            "stored memories. Use the provided memories to give accurate, relevant answers. "
            "If the memories don't contain enough information to fully answer the question, "
            "say so and provide what information you can."
        )
        user_message = f"""Here are relevant memories from the user's knowledge base:

{memory_context}

---

Based on these memories, please answer the following question:
{question}"""
    else:
        system_prompt = (
            "You are a helpful assistant. The user asked a question but no relevant "
            "memories were found in their knowledge base."
        )
        user_message = f"""No relevant memories were found for this question.

Question: {question}

Please let the user know that no matching memories were found and suggest they \
add relevant information using `recall add`."""

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text
