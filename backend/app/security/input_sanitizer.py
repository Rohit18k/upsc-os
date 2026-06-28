"""
Input sanitization layer for AI endpoints.
Protects against prompt injection, token flooding, and malicious content patterns.
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger("security.input_sanitizer")

# Maximum allowed input lengths by endpoint type
MAX_CHAT_LENGTH = 5000  # ~1250 tokens
MAX_ANSWER_LENGTH = 15000  # ~3750 tokens for mains answers
MAX_SUBJECT_LENGTH = 200

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?previous",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(?:if\s+you\s+are\s+)?a",
    r"pretend\s+(?:to\s+be|you\s+are)",
    r"system\s*:\s*",
    r"\[INST\]",
    r"\[/INST\]",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<<SYS>>",
    r"<</SYS>>",
    r"```\s*system",
    r"ADMIN\s*OVERRIDE",
    r"DEVELOPER\s*MODE",
    r"DAN\s*MODE",
    r"jailbreak",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def sanitize_ai_input(
    text: str,
    max_length: int = MAX_CHAT_LENGTH,
    context: str = "chat",
) -> Tuple[str, Optional[str]]:
    """
    Sanitize user input for AI endpoints.

    Returns:
        Tuple of (sanitized_text, warning_message).
        warning_message is None if input is clean.

    Raises:
        ValueError if input is rejected entirely.
    """
    if not text or not text.strip():
        raise ValueError("Input cannot be empty")

    # Strip and normalize whitespace
    cleaned = text.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Length check
    if len(cleaned) > max_length:
        raise ValueError(
            f"Input exceeds maximum length of {max_length} characters "
            f"for {context} endpoint ({len(cleaned)} provided)"
        )

    # Check for prompt injection patterns
    warning = None
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(cleaned):
            logger.warning(
                f"Potential prompt injection detected in {context}: "
                f"pattern={pattern.pattern}, input_preview={cleaned[:100]}"
            )
            warning = "Input contains suspicious patterns and has been flagged for review"
            # Remove the injection attempt
            cleaned = pattern.sub("[FILTERED]", cleaned)

    # Check for excessive special characters (potential encoding attacks)
    special_char_ratio = sum(1 for c in cleaned if not c.isalnum() and not c.isspace()) / max(len(cleaned), 1)
    if special_char_ratio > 0.5:
        logger.warning(f"High special character ratio ({special_char_ratio:.2f}) in {context} input")
        warning = "Input contains an unusually high ratio of special characters"

    # Check for null bytes
    if "\x00" in cleaned:
        cleaned = cleaned.replace("\x00", "")
        warning = "Input contained null bytes which were removed"

    return cleaned, warning


def sanitize_chat_input(text: str) -> Tuple[str, Optional[str]]:
    """Sanitize mentor/tutor chat input."""
    return sanitize_ai_input(text, max_length=MAX_CHAT_LENGTH, context="chat")


def sanitize_answer_input(text: str) -> Tuple[str, Optional[str]]:
    """Sanitize answer review input (longer allowed)."""
    return sanitize_ai_input(text, max_length=MAX_ANSWER_LENGTH, context="answer_review")


def sanitize_subject_input(text: str) -> Tuple[str, Optional[str]]:
    """Sanitize subject/topic input (short)."""
    return sanitize_ai_input(text, max_length=MAX_SUBJECT_LENGTH, context="subject")
