"""
guardrails.py — ShopBot Guardrail Engine
=========================================
5 guardrails that protect ShopBot from undesirable inputs and outputs.

  G1 — Input Length       : block messages > 500 characters
  G2 — Off-Topic          : redirect questions outside TechMart scope
  G3 — Prompt Injection   : block jailbreak / instruction-override attempts
  G4 — Insufficient Context: refuse when RAG finds no relevant data
  G5 — Response Sanity    : fallback when LLM output is empty or malformed

Usage:
    from guardrails import GuardrailEngine, GuardrailResult
    engine = GuardrailEngine()

    result = engine.check_input(message)
    if result.triggered:
        return result.safe_response   # return to user directly

    result = engine.check_output(question, llm_response, chunks)
    if result.triggered:
        return result.safe_response
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class GuardrailResult:
    triggered: bool
    guardrail: str          # e.g. "G1_INPUT_LENGTH"
    reason: str             # internal explanation
    safe_response: str      # what to show the user
    severity: str = "block" # "block" | "redirect" | "refuse" | "fallback"
    metadata: dict = field(default_factory=dict)

    @staticmethod
    def ok():
        return GuardrailResult(
            triggered=False, guardrail="none",
            reason="", safe_response="", severity="ok"
        )


# ── Guardrail Engine ──────────────────────────────────────────────────────────

class GuardrailEngine:
    """
    Central guardrail engine. Call check_input() before sending to LLM,
    and check_output() before returning the LLM response to the user.
    """

    # ── G1 Config ─────────────────────────────────────────────────────────────
    MAX_INPUT_CHARS = 500

    # ── G2 Config — Off-Topic Keywords ────────────────────────────────────────
    # Positive scope: must contain at least one TechMart-related concept
    IN_SCOPE_TERMS = {
        "product", "laptop", "phone", "headphone", "monitor", "keyboard",
        "tablet", "camera", "speaker", "charger", "cable", "warranty",
        "return", "refund", "shipping", "delivery", "order", "payment",
        "price", "cost", "stock", "available", "techmart", "store",
        "policy", "exchange", "receipt", "invoice", "discount", "offer",
        "buy", "purchase", "track", "cancel", "replace", "repair",
        "dell", "apple", "sony", "samsung", "lenovo", "lg", "hp",
        "xps", "macbook", "ipad", "airpods", "galaxy", "iphone",
    }

    # Topics clearly outside scope
    OFF_TOPIC_PATTERNS = [
        # Medical
        r"\b(fever|medicine|doctor|symptom|diagnos|treat|hospital|drug|disease|covid|pain|headache|illness)\b",
        # Legal / Financial
        r"\b(lawsuit|attorney|lawyer|sue|court|tax|invest|stock market|crypto|bitcoin|loan|mortgage)\b",
        # Politics / Religion
        r"\b(democrat|republican|election|president|prime minister|religion|god|pray|church|mosque|temple)\b",
        # Coding / General tech help
        r"\b(write.*code|debug|algorithm|machine learning|neural network|train.*model|python tutorial|how to program)\b",
        # Personal / Harmful
        r"\b(suicide|self.harm|hurt myself|kill|weapon|drug|illegal)\b",
        # Cooking / Recipes
        r"\b(recipe|cook|bake|ingredient|cuisine)\b",
        # Academic homework
        r"\b(essay|homework|assignment|thesis|dissertation|exam|quiz)\b",
    ]

    # ── G3 Config — Prompt Injection Patterns ─────────────────────────────────
    INJECTION_PATTERNS = [
        r"ignore\b.{0,25}\b(instructions?|rules?|prompt|context|system)",
        r"disregard\b.{0,25}\b(instructions?|rules?|prompt|context|system)",
        r"forget\b.{0,25}\b(everything|instructions?|rules?|context)",
        r"pretend (you are|to be|you're|you have no|you don't have)",
        r"you are now (a|an|the)",
        r"act as (a|an|the) (different|new|unrestricted|evil|jailbreak)",
        r"jailbreak",
        r"\bdan mode\b",
        r"developer mode",
        r"override\b.{0,20}\b(safety|rules|restrictions|guidelines|instructions)",
        r"bypass\b.{0,20}\b(safety|filter|rules|restrictions)",
        r"reveal\b.{0,20}\b(system prompt|instructions|rules|prompt|context)",
        r"print\b.{0,20}\b(system prompt|full prompt|instructions)",
        r"what (is|are) your (system prompt|instructions|rules)",
        r"translate the above",
        r"repeat.*system prompt",
    ]

    # ── G4 Config ─────────────────────────────────────────────────────────────
    MIN_SIMILARITY_THRESHOLD = 0.30   # Below this → refuse
    MIN_CHUNKS_REQUIRED = 1           # At least 1 chunk must be retrieved

    # ── G5 Config ─────────────────────────────────────────────────────────────
    MIN_RESPONSE_CHARS = 20
    ERROR_PREFIXES = ["error:", "exception:", "traceback", "500 internal"]

    # ──────────────────────────────────────────────────────────────────────────

    def check_input(self, message: str) -> GuardrailResult:
        """
        Run all input-side guardrails against the user's message.
        Returns the first triggered GuardrailResult, or GuardrailResult.ok().
        """
        checks = [
            self._g1_input_length,
            self._g3_prompt_injection,
            self._g2_off_topic,
        ]
        for check in checks:
            result = check(message)
            if result.triggered:
                return result
        return GuardrailResult.ok()

    def check_output(
        self,
        question: str,
        response: str,
        chunks: List[dict],
        top_similarity: float = 0.0,
    ) -> GuardrailResult:
        """
        Run all output-side guardrails.
        Returns the first triggered GuardrailResult, or GuardrailResult.ok().
        """
        checks = [
            lambda: self._g4_insufficient_context(question, chunks, top_similarity),
            lambda: self._g5_response_sanity(response),
        ]
        for check in checks:
            result = check()
            if result.triggered:
                return result
        return GuardrailResult.ok()

    # ── G1: Input Length ──────────────────────────────────────────────────────
    def _g1_input_length(self, message: str) -> GuardrailResult:
        if len(message) > self.MAX_INPUT_CHARS:
            return GuardrailResult(
                triggered=True,
                guardrail="G1_INPUT_LENGTH",
                severity="block",
                reason=f"Message is {len(message)} chars — exceeds {self.MAX_INPUT_CHARS} limit",
                safe_response=(
                    f"Your message is too long ({len(message)} characters). "
                    f"Please keep questions under {self.MAX_INPUT_CHARS} characters "
                    f"so I can give you a focused answer."
                ),
                metadata={"message_length": len(message), "limit": self.MAX_INPUT_CHARS}
            )
        return GuardrailResult.ok()

    # ── G2: Off-Topic ─────────────────────────────────────────────────────────
    def _g2_off_topic(self, message: str) -> GuardrailResult:
        msg_lower = message.lower()

        # Check for explicitly off-topic patterns
        for pattern in self.OFF_TOPIC_PATTERNS:
            if re.search(pattern, msg_lower):
                matched = re.search(pattern, msg_lower).group(0)
                return GuardrailResult(
                    triggered=True,
                    guardrail="G2_OFF_TOPIC",
                    severity="redirect",
                    reason=f"Matched off-topic pattern: '{matched}'",
                    safe_response=(
                        "I'm TechMart's ShopBot and I can only help with questions about "
                        "our products, orders, shipping, returns, and store policies. "
                        "For anything else, please contact the appropriate service. "
                        "Is there something about TechMart I can help you with?"
                    ),
                    metadata={"matched_pattern": matched}
                )

        # If message has no TechMart-relevant terms AND is long enough to be a real question
        if len(message.split()) >= 4:
            has_scope = any(term in msg_lower for term in self.IN_SCOPE_TERMS)
            if not has_scope:
                return GuardrailResult(
                    triggered=True,
                    guardrail="G2_OFF_TOPIC",
                    severity="redirect",
                    reason="No TechMart-related terms found in message",
                    safe_response=(
                        "I'm TechMart's ShopBot — I specialise in helping with our "
                        "products, orders, shipping, and return policies. "
                        "Could you rephrase your question to relate to something we sell or a service we offer?"
                    ),
                    metadata={"in_scope_terms_found": 0}
                )

        return GuardrailResult.ok()

    # ── G3: Prompt Injection ──────────────────────────────────────────────────
    def _g3_prompt_injection(self, message: str) -> GuardrailResult:
        msg_lower = message.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, msg_lower):
                matched = re.search(pattern, msg_lower).group(0)
                return GuardrailResult(
                    triggered=True,
                    guardrail="G3_PROMPT_INJECTION",
                    severity="block",
                    reason=f"Injection pattern detected: '{matched}'",
                    safe_response=(
                        "I can't process that request. "
                        "I'm here to help with TechMart products and services — "
                        "feel free to ask about products, orders, or policies!"
                    ),
                    metadata={"matched_pattern": matched}
                )
        return GuardrailResult.ok()

    # ── G4: Insufficient Context ──────────────────────────────────────────────
    def _g4_insufficient_context(
        self, question: str, chunks: List[dict], top_similarity: float
    ) -> GuardrailResult:
        chunks_found = len(chunks)
        best_sim = top_similarity

        # If RAG retrieved nothing or very low similarity
        if chunks_found < self.MIN_CHUNKS_REQUIRED or best_sim < self.MIN_SIMILARITY_THRESHOLD:
            return GuardrailResult(
                triggered=True,
                guardrail="G4_INSUFFICIENT_CONTEXT",
                severity="refuse",
                reason=(
                    f"Only {chunks_found} chunks retrieved, "
                    f"top similarity={best_sim:.3f} (threshold={self.MIN_SIMILARITY_THRESHOLD})"
                ),
                safe_response=(
                    "I don't have enough information in my knowledge base to answer that accurately. "
                    "For this query, please contact TechMart support directly at support@techmart.com "
                    "or call 1-800-TECHMART."
                ),
                metadata={
                    "chunks_retrieved": chunks_found,
                    "top_similarity": best_sim,
                    "threshold": self.MIN_SIMILARITY_THRESHOLD
                }
            )
        return GuardrailResult.ok()

    # ── G5: Response Sanity ───────────────────────────────────────────────────
    def _g5_response_sanity(self, response: str) -> GuardrailResult:
        if not response or not response.strip():
            return GuardrailResult(
                triggered=True,
                guardrail="G5_RESPONSE_SANITY",
                severity="fallback",
                reason="LLM returned empty response",
                safe_response=(
                    "I wasn't able to generate a response right now. "
                    "Please try again or rephrase your question."
                ),
                metadata={"response_length": 0}
            )

        stripped = response.strip()

        if len(stripped) < self.MIN_RESPONSE_CHARS:
            return GuardrailResult(
                triggered=True,
                guardrail="G5_RESPONSE_SANITY",
                severity="fallback",
                reason=f"Response too short: {len(stripped)} chars",
                safe_response=(
                    "I received an incomplete response. "
                    "Please try asking your question again."
                ),
                metadata={"response_length": len(stripped)}
            )

        resp_lower = stripped.lower()
        for prefix in self.ERROR_PREFIXES:
            if resp_lower.startswith(prefix):
                return GuardrailResult(
                    triggered=True,
                    guardrail="G5_RESPONSE_SANITY",
                    severity="fallback",
                    reason=f"Response looks like an error: starts with '{prefix}'",
                    safe_response=(
                        "I encountered a technical issue generating a response. "
                        "Please try again in a moment."
                    ),
                    metadata={"error_prefix": prefix}
                )

        return GuardrailResult.ok()


# ── Convenience singleton ─────────────────────────────────────────────────────
_engine = GuardrailEngine()


def check_input(message: str) -> GuardrailResult:
    return _engine.check_input(message)


def check_output(question, response, chunks, top_similarity=0.0) -> GuardrailResult:
    return _engine.check_output(question, response, chunks, top_similarity)
