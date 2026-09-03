"""
ollama_client.py — Wrapper around Ollama's REST API for ShopBot
Exercise 1: Basic LLM communication
"""

import requests
import time
from typing import Optional


OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "codellama"


def check_ollama_health() -> bool:
    """Check if Ollama server is running and reachable."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def list_available_models() -> list[str]:
    """Return a list of models currently pulled in Ollama."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        data = response.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def generate_response(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    num_predict: int = 512,
) -> dict:
    """
    Send a prompt to Ollama and return the response with metadata.

    Args:
        prompt: The user's question or message
        model: The Ollama model to use (e.g. 'codellama', 'starcoder2')
        system_prompt: Optional system-level instruction for the model
        temperature: Sampling temperature (lower = more deterministic)
        num_predict: Max tokens to generate

    Returns:
        dict with keys: response, model, latency_ms, tokens_used, prompt_tokens
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        }
    }

    if system_prompt:
        payload["system"] = system_prompt

    start_time = time.time()

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return {
            "response": "❌ Could not connect to Ollama. Please ensure Ollama is running on localhost:11434.",
            "error": True,
            "latency_ms": 0,
            "tokens_used": 0,
            "prompt_tokens": 0,
            "model": model,
        }
    except requests.exceptions.Timeout:
        return {
            "response": "❌ Ollama request timed out. The model may be loading — please try again.",
            "error": True,
            "latency_ms": int((time.time() - start_time) * 1000),
            "tokens_used": 0,
            "prompt_tokens": 0,
            "model": model,
        }

    latency_ms = int((time.time() - start_time) * 1000)
    data = response.json()

    return {
        "response": data.get("response", "").strip(),
        "error": False,
        "model": data.get("model", model),
        "latency_ms": latency_ms,
        "tokens_used": data.get("eval_count", 0),
        "prompt_tokens": data.get("prompt_eval_count", 0),
        "total_duration_ms": data.get("total_duration", 0) // 1_000_000,
    }
