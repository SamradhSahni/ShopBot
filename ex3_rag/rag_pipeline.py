"""
rag_pipeline.py — Full RAG chain for ShopBot
Exercise 3: Context + Question → Ollama → Code Llama → Response
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex1_basic"))
sys.path.insert(0, os.path.dirname(__file__))

from retriever import retrieve, build_context
from ollama_client import generate_response
from prompts import RAG_PROMPT_TEMPLATE, SYSTEM_PROMPT
from typing import Dict, Optional


def rag_chat(
    question: str,
    model: str = "codellama",
    top_k: int = 3,
) -> Dict:
    """
    Full RAG pipeline:
      1. Embed user question
      2. Retrieve top-K relevant chunks via cosine similarity
      3. Build context string
      4. Send (context + question) to Code Llama
      5. Return response with full trace

    Args:
        question: User's question
        model: Ollama model name
        top_k: Number of chunks to retrieve
    Returns:
        Dict with response, retrieved_chunks, context, metrics
    """
    pipeline_start = time.time()

    # Step 1 & 2: Retrieve relevant context
    retrieve_start = time.time()
    chunks = retrieve(question, k=top_k)
    retrieve_ms = int((time.time() - retrieve_start) * 1000)

    # Step 3: Build context
    context = build_context(chunks)

    # Step 4: Build augmented prompt
    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

    # Step 5: Generate response
    llm_result = generate_response(
        prompt=prompt,
        model=model,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.2,
    )

    total_ms = int((time.time() - pipeline_start) * 1000)

    return {
        "question": question,
        "response": llm_result["response"],
        "model": llm_result["model"],
        "retrieved_chunks": chunks,
        "context": context,
        "rag_used": True,
        "metrics": {
            "retrieve_latency_ms": retrieve_ms,
            "llm_latency_ms": llm_result["latency_ms"],
            "total_latency_ms": total_ms,
            "tokens_used": llm_result["tokens_used"],
            "prompt_tokens": llm_result["prompt_tokens"],
            "chunks_retrieved": len(chunks),
            "top_similarity": chunks[0]["similarity_score"] if chunks else 0,
        }
    }


def no_rag_chat(question: str, model: str = "codellama") -> Dict:
    """Chat WITHOUT RAG — used for comparison in Exercise 3."""
    result = generate_response(
        prompt=question,
        model=model,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.2,
    )
    return {
        "question": question,
        "response": result["response"],
        "model": result["model"],
        "retrieved_chunks": [],
        "context": None,
        "rag_used": False,
        "metrics": {
            "retrieve_latency_ms": 0,
            "llm_latency_ms": result["latency_ms"],
            "total_latency_ms": result["latency_ms"],
            "tokens_used": result["tokens_used"],
            "prompt_tokens": result["prompt_tokens"],
            "chunks_retrieved": 0,
            "top_similarity": 0,
        }
    }
