"""
guardrails.py — ShopBot Guardrail Engine (guardrails-ai powered)
=================================================================
Uses the official guardrails-ai library (https://www.guardrailsai.com)
to implement 5 guardrails protecting ShopBot from undesirable inputs/outputs.

  G1 — Input Length       : ValidLength hub validator (max 500 chars)
  G2 — Off-Topic          : Custom OffTopicValidator (regex + scope check)
  G3 — Prompt Injection   : DetectJailbreak hub validator + custom patterns
  G4 — Insufficient Context: Custom InsufficientContextValidator
  G5 — Response Sanity    : Custom ResponseSanityValidator

Install on Ubuntu VM:
    pip install guardrails-ai
    guardrails hub install hub://guardrails/detect_jailbreak
    guardrails hub install hub://guardrails/valid_length
    guardrails hub install hub://guardrails/toxic_language

Usage:
    from guardrails import GuardrailEngine, GuardrailResult
    engine = GuardrailEngine()
    result = engine.check_input(message)
    if result.triggered:
        return result.safe_response
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

# ── Try importing guardrails-ai library ───────────────────────────────────────
try:
    from guardrails import Guard
    from guardrails.validator_base import (
        FailResult,
        PassResult,
        ValidationResult,
        Validator,
        register_validator,
    )
    GUARDRAILS_AI_AVAILABLE = True
    logger.info("guardrails-ai library loaded successfully")
except ImportError:
    GUARDRAILS_AI_AVAILABLE = False
    logger.warning(
        "guardrails-ai not installed. Falling back to built-in regex engine.\n"
        "Install with: pip install guardrails-ai"
    )

# ── Try importing hub validators ───────────────────────────────────────────────
DETECT_JAILBREAK_AVAILABLE = False
VALID_LENGTH_AVAILABLE = False

if GUARDRAILS_AI_AVAILABLE:
    try:
        from guardrails.hub import DetectJailbreak
        DETECT_JAILBREAK_AVAILABLE = True
        logger.info("Hub validator DetectJailbreak loaded")
    except (ImportError, Exception):
        logger.warning("DetectJailbreak hub validator not installed. Using regex fallback for G3.")

    try:
        from guardrails.hub import ValidLength
        VALID_LENGTH_AVAILABLE = True
        logger.info("Hub validator ValidLength loaded")
    except (ImportError, Exception):
        logger.warning("ValidLength hub validator not installed. Using built-in check for G1.")


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class GuardrailResult:
    triggered: bool
    guardrail: str
    reason: str
    safe_response: str
    severity: str = "block"
    metadata: dict = field(default_factory=dict)

    @staticmethod
    def ok():
        return GuardrailResult(
            triggered=False, guardrail="none",
            reason="", safe_response="", severity="ok"
        )


# ── Custom Validators (guardrails-ai Validator subclasses) ────────────────────
# These work whether guardrails-ai is installed or not — the base class
# is shimmed below if the library is unavailable.

if GUARDRAILS_AI_AVAILABLE:

    # ── G2: Off-Topic Validator ───────────────────────────────────────────────
    @register_validator(name="shopbot-off-topic", data_type="string")
    class OffTopicValidator(Validator):
        """
        G2 — Rejects questions outside TechMart's e-commerce scope.
        Checks against known off-topic patterns and verifies at least one
        TechMart-related term is present in longer messages.
        """
        OFF_TOPIC_PATTERNS = [
            r"\b(fever|medicine|doctor|symptom|diagnos|treat|hospital|disease|covid|pain|headache)\b",
            r"\b(lawsuit|attorney|lawyer|sue|court|invest|stock market|crypto|bitcoin|loan|mortgage)\b",
            r"\b(democrat|republican|election|president|prime minister|religion|god|pray|church|mosque)\b",
            r"\b(write.*code|debug|algorithm|machine learning|neural network|train.*model|python tutorial)\b",
            r"\b(suicide|self.harm|hurt myself|kill|weapon|illegal)\b",
            r"\b(recipe|cook|bake|ingredient|cuisine)\b",
            r"\b(essay|homework|assignment|thesis|dissertation|exam answer)\b",
        ]
        IN_SCOPE_TERMS = {
            "product","laptop","phone","headphone","monitor","keyboard","tablet","camera",
            "speaker","charger","cable","warranty","return","refund","shipping","delivery",
            "order","payment","price","cost","stock","available","techmart","store","policy",
            "exchange","receipt","invoice","discount","buy","purchase","track","cancel",
            "dell","apple","sony","samsung","lenovo","hp","xps","macbook","ipad","galaxy",
        }

        def validate(self, value: str, metadata: dict = {}) -> ValidationResult:
            msg_lower = value.lower()
            for pattern in self.OFF_TOPIC_PATTERNS:
                m = re.search(pattern, msg_lower)
                if m:
                    return FailResult(
                        error_message=f"Off-topic pattern matched: '{m.group(0)}'",
                        fix_value=(
                            "I'm TechMart's ShopBot and I can only help with questions about "
                            "our products, orders, shipping, returns, and store policies. "
                            "Is there something about TechMart I can help you with?"
                        ),
                    )
            # If long message with no TechMart terms → redirect
            if len(value.split()) >= 4:
                if not any(t in msg_lower for t in self.IN_SCOPE_TERMS):
                    return FailResult(
                        error_message="No TechMart-related terms found in message",
                        fix_value=(
                            "I'm TechMart's ShopBot — I specialise in helping with our "
                            "products, orders, shipping, and return policies. "
                            "Could you rephrase your question to relate to something TechMart offers?"
                        ),
                    )
            return PassResult()

    # ── G3: Prompt Injection Custom Patterns ──────────────────────────────────
    @register_validator(name="shopbot-prompt-injection", data_type="string")
    class PromptInjectionValidator(Validator):
        """
        G3 (Regex layer) — Catches prompt injection patterns not caught by
        the ML-based DetectJailbreak hub validator.
        """
        PATTERNS = [
            r"ignore\b.{0,25}\b(instructions?|rules?|prompt|context|system)",
            r"disregard\b.{0,25}\b(instructions?|rules?|prompt|context|system)",
            r"forget\b.{0,25}\b(everything|instructions?|rules?|context)",
            r"pretend (you are|to be|you're|you have no|you don't have)",
            r"you are now (a|an|the)",
            r"act as (a|an) (different|unrestricted|evil|jailbreak)",
            r"\bdan mode\b",
            r"developer mode",
            r"override\b.{0,20}\b(safety|rules|restrictions|guidelines)",
            r"bypass\b.{0,20}\b(safety|filter|rules|restrictions)",
            r"reveal\b.{0,20}\b(system prompt|instructions|rules)",
            r"what (is|are) your (system prompt|instructions|rules)",
        ]

        def validate(self, value: str, metadata: dict = {}) -> ValidationResult:
            msg_lower = value.lower()
            for pattern in self.PATTERNS:
                m = re.search(pattern, msg_lower)
                if m:
                    return FailResult(
                        error_message=f"Prompt injection pattern: '{m.group(0)}'",
                        fix_value=(
                            "I can't process that request. "
                            "I'm here to help with TechMart products and services!"
                        ),
                    )
            return PassResult()

    # ── G4: Insufficient Context Validator ───────────────────────────────────
    @register_validator(name="shopbot-insufficient-context", data_type="string")
    class InsufficientContextValidator(Validator):
        """
        G4 — Applied to LLM output when RAG retrieval finds no relevant chunks
        or similarity is below threshold. Requires metadata:
            metadata = {"chunks": [...], "top_similarity": float}
        """
        MIN_SIMILARITY = 0.30
        MIN_CHUNKS = 1

        def validate(self, value: str, metadata: dict = {}) -> ValidationResult:
            chunks = metadata.get("chunks", [])
            top_sim = metadata.get("top_similarity", 0.0)
            if len(chunks) < self.MIN_CHUNKS or top_sim < self.MIN_SIMILARITY:
                return FailResult(
                    error_message=(
                        f"Insufficient context: {len(chunks)} chunks, "
                        f"top_similarity={top_sim:.3f} < {self.MIN_SIMILARITY}"
                    ),
                    fix_value=(
                        "I don't have enough information in my knowledge base to answer that accurately. "
                        "Please contact TechMart support at support@techmart.com or call 1-800-TECHMART."
                    ),
                )
            return PassResult()

    # ── G5: Response Sanity Validator ─────────────────────────────────────────
    @register_validator(name="shopbot-response-sanity", data_type="string")
    class ResponseSanityValidator(Validator):
        """
        G5 — Catches empty, too-short, or error-string LLM responses.
        """
        MIN_CHARS = 20
        ERROR_PREFIXES = ["error:", "exception:", "traceback", "500 internal"]

        def validate(self, value: str, metadata: dict = {}) -> ValidationResult:
            stripped = (value or "").strip()
            if not stripped:
                return FailResult(
                    error_message="LLM returned empty response",
                    fix_value="I wasn't able to generate a response. Please try again.",
                )
            if len(stripped) < self.MIN_CHARS:
                return FailResult(
                    error_message=f"Response too short: {len(stripped)} chars",
                    fix_value="I received an incomplete response. Please rephrase and try again.",
                )
            for prefix in self.ERROR_PREFIXES:
                if stripped.lower().startswith(prefix):
                    return FailResult(
                        error_message=f"Response looks like an error: '{prefix}'",
                        fix_value="I encountered a technical issue. Please try again in a moment.",
                    )
            return PassResult()


# ── Guard Builder ─────────────────────────────────────────────────────────────

def _build_input_guard() -> Optional["Guard"]:
    """Build the input Guard chain: G1 → G3(hub) → G3(regex) → G2.
    All validators use on_fail='exception' so failures always raise,
    are caught by _check_with_guard, and return triggered=True reliably.
    (on_fail='fix' causes validation_passed=True which silently swallows failures)
    """
    if not GUARDRAILS_AI_AVAILABLE:
        return None
    validators = []

    # G1: Length check
    if VALID_LENGTH_AVAILABLE:
        validators.append(ValidLength(min=1, max=500, on_fail="exception"))
    # G3: Hub ML jailbreak detector (if available)
    if DETECT_JAILBREAK_AVAILABLE:
        validators.append(DetectJailbreak(on_fail="exception"))
    # G3: Regex injection patterns — exception mode
    validators.append(PromptInjectionValidator(on_fail="exception"))
    # G2: Off-topic check — exception mode
    validators.append(OffTopicValidator(on_fail="exception"))

    guard = Guard()
    for v in validators:
        guard = guard.use(v)
    return guard


def _build_output_guard() -> Optional["Guard"]:
    """Build the output Guard chain: G4 → G5."""
    if not GUARDRAILS_AI_AVAILABLE:
        return None
    guard = Guard().use(
        InsufficientContextValidator(on_fail="exception")
    ).use(
        ResponseSanityValidator(on_fail="exception")
    )
    return guard


# ── GuardrailEngine ───────────────────────────────────────────────────────────

class GuardrailEngine:
    """
    Central guardrail engine.
    Uses guardrails-ai Guards when available, falls back to built-in regex.
    """

    MAX_INPUT_CHARS = 500

    # Fallback injection patterns (used when guardrails-ai not installed)
    _FALLBACK_INJECTION = [
        r"ignore\b.{0,25}\b(instructions?|rules?|prompt|context|system)",
        r"disregard\b.{0,25}\b(instructions?|rules?|prompt|context|system)",
        r"forget\b.{0,25}\b(everything|instructions?|rules?|context)",
        r"pretend (you are|to be|you're)",
        r"jailbreak", r"\bdan mode\b",
        r"override\b.{0,20}\b(safety|rules|restrictions)",
    ]
    _FALLBACK_OFFTOPIC = [
        r"\b(fever|medicine|doctor|symptom|treat|hospital|disease)\b",
        r"\b(lawsuit|attorney|crypto|bitcoin|loan|mortgage)\b",
        r"\b(election|president|religion|god|pray|church)\b",
        r"\b(recipe|cook|bake|ingredient)\b",
        r"\b(essay|homework|assignment|thesis|exam answer)\b",
    ]
    _IN_SCOPE = {
        "product","laptop","phone","headphone","monitor","warranty","return","refund",
        "shipping","delivery","order","payment","price","cost","stock","techmart","store",
        "policy","discount","buy","purchase","track","cancel","dell","apple","sony","samsung",
    }

    def __init__(self):
        self._input_guard = None
        self._output_guard = None
        if GUARDRAILS_AI_AVAILABLE:
            try:
                self._input_guard = _build_input_guard()
                self._output_guard = _build_output_guard()
                logger.info("guardrails-ai Guards built successfully")
            except Exception as e:
                logger.warning(f"Failed to build Guards: {e}. Using fallback.")

    # ── Public API ────────────────────────────────────────────────────────────

    def check_input(self, message: str) -> GuardrailResult:
        if self._input_guard is not None:
            return self._check_with_guard(message, self._input_guard, "input")
        return self._fallback_check_input(message)

    def check_output(
        self,
        question: str,
        response: str,
        chunks: List[dict],
        top_similarity: float = 0.0,
    ) -> GuardrailResult:
        if self._output_guard is not None:
            metadata = {"chunks": chunks, "top_similarity": top_similarity}
            return self._check_with_guard(response, self._output_guard, "output", metadata)
        return self._fallback_check_output(question, response, chunks, top_similarity)

    # ── guardrails-ai path ─────────────────────────────────────────────────────

    def _check_with_guard(
        self,
        value: str,
        guard: "Guard",
        mode: str,
        metadata: dict = {},
    ) -> GuardrailResult:
        """
        Run a Guard and map the result to GuardrailResult.
        Uses on_fail='exception' semantics: failures always raise,
        caught here, always returns triggered=True.
        Also detects fix-based failures as a belt-and-suspenders check.
        """
        try:
            outcome = guard.validate(value, metadata=metadata)

            # Check 1: explicit validation failure flag
            if not outcome.validation_passed:
                fixed = outcome.validated_output or value
                err = str(outcome.error) if hasattr(outcome, "error") and outcome.error else ""
                if not err:
                    # Detect from changed output (on_fail='fix' behaviour)
                    err = f"Validator modified output from '{value[:40]}'"
                guardrail_id = self._identify_guardrail(err or fixed, mode)
                severity = {"G1": "block", "G2": "redirect", "G3": "block",
                            "G4": "refuse", "G5": "fallback"}.get(guardrail_id[:2], "block")
                return GuardrailResult(
                    triggered=True, guardrail=guardrail_id,
                    reason=err, safe_response=fixed, severity=severity,
                )

            # Check 2: output was silently changed by a fix validator
            validated_out = outcome.validated_output or value
            if validated_out and validated_out.strip() != value.strip() and len(validated_out) > 5:
                guardrail_id = self._identify_guardrail(validated_out, mode)
                severity = {"G1": "block", "G2": "redirect", "G3": "block",
                            "G4": "refuse", "G5": "fallback"}.get(guardrail_id[:2], "block")
                return GuardrailResult(
                    triggered=True, guardrail=guardrail_id,
                    reason="Validator fix applied", safe_response=validated_out, severity=severity,
                )

            return GuardrailResult.ok()

        except Exception as e:
            # on_fail='exception' path — validator raised, extract guardrail from message
            err_str = str(e)
            guardrail_id = self._identify_guardrail(err_str, mode)
            severity = {"G1": "block", "G2": "redirect", "G3": "block",
                        "G4": "refuse", "G5": "fallback"}.get(guardrail_id[:2], "block")
            safe_map = {
                "G1": f"Your message is too long. Please keep questions under {self.MAX_INPUT_CHARS} characters.",
                "G2": "I'm TechMart's ShopBot — I can only help with TechMart products, orders, shipping, and return policies.",
                "G3": "I can't process that request. I'm here to help with TechMart products and services!",
                "G4": "I don't have enough information to answer that. Contact support@techmart.com.",
                "G5": "I wasn't able to generate a response. Please try again.",
            }
            safe = safe_map.get(guardrail_id[:2], "That request cannot be processed.")
            return GuardrailResult(
                triggered=True, guardrail=guardrail_id,
                reason=err_str, safe_response=safe, severity=severity,
            )

    def _identify_guardrail(self, error_msg: str, mode: str) -> str:
        el = error_msg.lower()
        if "length" in el or "too long" in el or "max" in el:
            return "G1_INPUT_LENGTH"
        if "jailbreak" in el or "injection" in el or "override" in el or "ignore" in el:
            return "G3_PROMPT_INJECTION"
        if "off-topic" in el or "topic" in el or "scope" in el or "techmart" in el:
            return "G2_OFF_TOPIC"
        if "insufficient" in el or "context" in el or "similarity" in el or "chunk" in el:
            return "G4_INSUFFICIENT_CONTEXT"
        if "empty" in el or "short" in el or "sanity" in el:
            return "G5_RESPONSE_SANITY"
        return "G3_PROMPT_INJECTION" if mode == "input" else "G5_RESPONSE_SANITY"

    # ── Fallback path (no guardrails-ai library) ──────────────────────────────

    def _fallback_check_input(self, message: str) -> GuardrailResult:
        # G1
        if len(message) > self.MAX_INPUT_CHARS:
            return GuardrailResult(
                triggered=True, guardrail="G1_INPUT_LENGTH", severity="block",
                reason=f"Message is {len(message)} chars — exceeds {self.MAX_INPUT_CHARS}",
                safe_response=f"Your message is too long ({len(message)} characters). "
                              f"Please keep questions under {self.MAX_INPUT_CHARS} characters.",
            )
        # G3
        msg_lower = message.lower()
        for pat in self._FALLBACK_INJECTION:
            m = re.search(pat, msg_lower)
            if m:
                return GuardrailResult(
                    triggered=True, guardrail="G3_PROMPT_INJECTION", severity="block",
                    reason=f"Injection pattern: '{m.group(0)}'",
                    safe_response="I can't process that request. I'm here to help with TechMart products!",
                )
        # G2
        for pat in self._FALLBACK_OFFTOPIC:
            m = re.search(pat, msg_lower)
            if m:
                return GuardrailResult(
                    triggered=True, guardrail="G2_OFF_TOPIC", severity="redirect",
                    reason=f"Off-topic pattern: '{m.group(0)}'",
                    safe_response="I'm TechMart's ShopBot — I can only help with TechMart products, "
                                  "orders, shipping, and return policies.",
                )
        if len(message.split()) >= 4 and not any(t in msg_lower for t in self._IN_SCOPE):
            return GuardrailResult(
                triggered=True, guardrail="G2_OFF_TOPIC", severity="redirect",
                reason="No TechMart-related terms found",
                safe_response="I'm TechMart's ShopBot — please ask about our products or services!",
            )
        return GuardrailResult.ok()

    def _fallback_check_output(
        self, question: str, response: str, chunks: List[dict], top_sim: float
    ) -> GuardrailResult:
        # G4
        if len(chunks) < 1 or top_sim < 0.30:
            return GuardrailResult(
                triggered=True, guardrail="G4_INSUFFICIENT_CONTEXT", severity="refuse",
                reason=f"{len(chunks)} chunks, top_similarity={top_sim:.3f}",
                safe_response="I don't have enough information to answer that accurately. "
                              "Please contact support@techmart.com or call 1-800-TECHMART.",
            )
        # G5
        stripped = (response or "").strip()
        if not stripped or len(stripped) < 20:
            return GuardrailResult(
                triggered=True, guardrail="G5_RESPONSE_SANITY", severity="fallback",
                reason=f"Response too short or empty ({len(stripped)} chars)",
                safe_response="I wasn't able to generate a response. Please try again.",
            )
        return GuardrailResult.ok()


# ── Module-level convenience functions ────────────────────────────────────────

_engine = GuardrailEngine()


def check_input(message: str) -> GuardrailResult:
    return _engine.check_input(message)


def check_output(
    question: str, response: str, chunks: List[dict], top_similarity: float = 0.0
) -> GuardrailResult:
    return _engine.check_output(question, response, chunks, top_similarity)


def get_engine_info() -> dict:
    """Return info about which guardrail backend is active."""
    return {
        "guardrails_ai_available": GUARDRAILS_AI_AVAILABLE,
        "detect_jailbreak_hub": DETECT_JAILBREAK_AVAILABLE,
        "valid_length_hub": VALID_LENGTH_AVAILABLE,
        "input_guard_active": _engine._input_guard is not None,
        "output_guard_active": _engine._output_guard is not None,
        "mode": "guardrails-ai" if GUARDRAILS_AI_AVAILABLE else "built-in fallback",
    }
