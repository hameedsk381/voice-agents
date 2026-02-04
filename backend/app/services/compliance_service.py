"""
PII Redaction service for compliance and security.
"""
import re
from typing import List, Dict, Any, Union

class PIIRedactor:
    def __init__(self):
        # Common PII Regex Patterns
        self.patterns = {
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "phone": r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            "credit_card": r'\b(?:\d[ -]*?){13,16}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "ipv4": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        }

    def redact_text(self, text: str) -> str:
        """Redacts sensitive information from a string."""
        if not text:
            return text
            
        redacted = text
        for label, pattern in self.patterns.items():
            redacted = re.sub(pattern, f"[{label.upper()}_REDACTED]", redacted)
            
        return redacted

    def redact_transcript(self, transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Redacts an entire conversation history."""
        return [
            {**turn, "content": self.redact_text(turn.get("content", ""))}
            for turn in transcript
        ]

redactor = PIIRedactor()
