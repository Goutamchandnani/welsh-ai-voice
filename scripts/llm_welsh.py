"""
scripts/llm_welsh.py

Phase 4 — Welsh Language Model wrapper using Ollama + Llama 3.1 8B.

This module provides a simple function: respond(text) -> str
which takes Welsh input text and returns a Welsh response.

The system prompt is the key — it forces the model to respond in Welsh
and behave as a helpful Welsh-speaking assistant.
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"

WELSH_SYSTEM_PROMPT = """Rwyt ti'n gynorthwyydd AI o'r enw Llais sy'n siarad Cymraeg yn rhugl.

Rheolau:
- Ateba BOB AMSER yn Gymraeg, waeth beth fo iaith y defnyddiwr.
- Cadw atebion yn gryno a naturiol (1-3 brawddeg ar gyfer sgwrs).
- Defnyddia Gymraeg naturiol, modern fel y'i siaredir yng Nghymru heddiw.
- Os nad wyt ti'n gwybod rhywbeth, dywed "Nid wyf yn gwybod".
- Bydd yn gynnes a chyfeillgar — fel ffrind Cymraeg cymwynasgar.
- Paid byth ag ymateb yn Saesneg.

Enghraifft:
Defnyddiwr: Sut wyt ti?
Ti: Dw i'n iawn, diolch yn fawr! Sut alla i dy helpu di heddiw?

Defnyddiwr: Beth yw prifddinas Cymru?
Ti: Caerdydd yw prifddinas Cymru — dinas brysur ar lan afon Taf.
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
