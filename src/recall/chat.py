"""LLM-powered chat for recall memories using litellm."""

from typing import List

from .store import Memory


def chat_with_memories(
    question: str,
    memories: List[Memory],
    model: str = "gpt-4o-mini",
) -> str:
    """Send question to LLM with memory context.

    Supports any model via litellm:
    - OpenAI: gpt-4o, gpt-4o-mini, gpt-4-turbo
    - Anthropic: claude-sonnet-4-20250514, claude-3-5-haiku-20241022
    - Ollama: ollama/llama3, ollama/mistral
    - And 100+ more providers

    Set the appropriate API key env var:
    - OPENAI_API_KEY for OpenAI models
    - ANTHROPIC_API_KEY for Claude models
    - No key needed for Ollama (local)
    """
    try:
        import litellm
    except ImportError:
        raise ImportError("litellm package not installed. Run: pip install litellm")

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

    # Use litellm for universal model support
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
    )

    return response.choices[0].message.content
