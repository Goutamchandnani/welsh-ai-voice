"""
scripts/llm_welsh.py

Phase 4 — Welsh Language Model wrapper using Ollama + Llama 3.2.

This module provides a simple function: respond(text) -> str
which takes Welsh input text and returns a Welsh response.

The system prompt is the key — it forces the model to respond in Welsh
and behave as a helpful Welsh-speaking assistant.
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

WELSH_SYSTEM_PROMPT = """You are Llais, a helpful AI assistant that speaks Welsh (Cymraeg).

Rules:
- ALWAYS respond in Welsh, even if the user writes in English.
- Keep your responses concise and natural (1-3 sentences for conversational exchanges).
- Use natural, modern Welsh as spoken in Wales today.
- If you don't know something, say "Nid wyf yn gwybod" (I don't know).
- Be warm and friendly — like a helpful Welsh-speaking friend.

Example:
User: Sut wyt ti?
You: Dw i'n iawn, diolch yn fawr! Sut alla i dy helpu di heddiw?
"""


def respond(user_text: str, verbose: bool = True) -> str:
    """
    Generate a Welsh response to Welsh input text.

    Args:
        user_text: The Welsh input text from the user.
        verbose:   Whether to print the response as it streams in.

    Returns:
        The full Welsh response string.
    """
    payload = {
        "model": MODEL,
        "system": WELSH_SYSTEM_PROMPT,
        "prompt": user_text,
        "stream": True,
    }

    if verbose:
        print(f"🧠 LLM thinking...", end="", flush=True)

    full_response = ""
    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60) as r:
            r.raise_for_status()
            if verbose:
                print(f"\r🧠 LLM: ", end="", flush=True)
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    full_response += token
                    if verbose:
                        print(token, end="", flush=True)
                    if chunk.get("done"):
                        break
        if verbose:
            print()  # newline after streaming
    except requests.exceptions.ConnectionError:
        return "❌ Error: Ollama is not running. Start it with: ollama serve"
    except Exception as e:
        return f"❌ Error: {e}"

    return full_response.strip()


if __name__ == "__main__":
    print("🐉 Welsh LLM Test (type 'quit' to exit)")
    print("-" * 40)

    test_inputs = [
        "Bore da! Sut wyt ti?",
        "Beth yw prifddinas Cymru?",
        "Sut mae'r tywydd heddiw?",
    ]

    for text in test_inputs:
        print(f"\n👤 User: {text}")
        response = respond(text)
        print(f"\n")
