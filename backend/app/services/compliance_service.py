import re
from typing import List, Dict, Any, Union
from app.schemas.compliance import ComplianceRule, ComplianceViolation, ComplianceCheckResult, ComplianceSeverity
from app.services.llm.groq_provider import GroqLLM
from app.core.config import settings
import json
from loguru import logger

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

class ComplianceValidator:
    """The 'Shadow Agent' that audits every turn for regulatory safety."""
    
    def __init__(self, llm_service=None):
        self.llm = llm_service or GroqLLM()
        self.redactor = PIIRedactor()

    async def validate_turn(
        self, 
        user_input: str, 
        ai_response: str, 
        rules: List[ComplianceRule],
        turn_index: int
    ) -> ComplianceCheckResult:
        """Evaluate a single turn against compliance rules."""
        violations = []
        risk_score = 0.0
        
        # 1. Fast Regex Checks
        for rule in rules:
            if rule.rule_type == "mandatory_phrase":
                phrases = rule.config.get("phrases", [])
                if not any(p.lower() in ai_response.lower() for p in phrases):
                    violations.append(ComplianceViolation(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        reason=f"Missing mandatory phrase from: {phrases}",
                        turn_index=turn_index
                    ))

        # 2. LLM Semantic Audit (If complex rules exist)
        llm_rules = [r for r in rules if r.rule_type == "llm_check"]
        if llm_rules:
            audit_prompt = self._build_audit_prompt(user_input, ai_response, llm_rules)
            try:
                # We use a structured output prompt to get violations back as JSON
                response_text = await self.llm.generate_response(
                    audit_prompt,
                    "You are a strict regulatory compliance auditor for voice calls.",
                    []
                )
                
                # Cleanup potential markdown code blocks
                clean_json = response_text.replace("```json", "").replace("```", "").strip()
                audit_data = json.loads(clean_json)
                
                for v in audit_data.get("violations", []):
                    violations.append(ComplianceViolation(
                        rule_id=v["rule_id"],
                        rule_name=v["rule_name"],
                        severity=v.get("severity", "warning"),
                        reason=v["reason"],
                        turn_index=turn_index,
                        matched_text=v.get("quote")
                    ))
            except Exception as e:
                logger.error(f"Compliance LLM Audit failed: {e}")

        # Calculate Risk Score
        if violations:
            severity_weights = {"info": 0.1, "warning": 0.4, "critical": 1.0}
            max_weight = max([severity_weights.get(v.severity.value, 0.4) for v in violations])
            risk_score = min(1.0, max_weight * (1 + 0.1 * len(violations)))

        return ComplianceCheckResult(
            session_id="", # To be filled by caller
            agent_id="",
            violations=violations,
            is_compliant=len([v for v in violations if v.severity == "critical"]) == 0,
            risk_score=risk_score
        )

    def _build_audit_prompt(self, user_input: str, ai_response: str, rules: List[ComplianceRule]) -> str:
        rules_str = "\n".join([f"- [{r.id}] {r.name}: {r.description}" for r in rules])
        return f"""
Audit the following turn between a USER and an AI AGENT for compliance violations.

USER: "{user_input}"
AI AGENT: "{ai_response}"

RULES TO CHECK:
{rules_str}

Respond STRICTLY in JSON format:
{{
  "violations": [
    {{
      "rule_id": "rule_id",
      "rule_name": "rule_name",
      "reason": "Why the rule was violated",
      "severity": "info|warning|critical",
      "quote": "The specific problematic part of the text"
    }}
  ]
}}
"""

from app.models.compliance import RegulatoryPolicy
from sqlalchemy.orm import Session

def get_baseline_rules(db: Session = None, organization_id: str = None) -> List[ComplianceRule]:
    """Standard safety and regulatory rules."""
    rules = [
        ComplianceRule(
            id="CR-01",
            name="Regulatory Disclosure",
            description="The agent must disclose it is an AI and the call is recorded.",
            severity=ComplianceSeverity.CRITICAL,
            rule_type="llm_check"
        ),
        ComplianceRule(
            id="CR-02",
            name="No Financial Advice",
            description="The agent must not provide specific financial or investment advice.",
            severity=ComplianceSeverity.CRITICAL,
            rule_type="llm_check"
        ),
        ComplianceRule(
            id="CR-03",
            name="Professional Conduct",
            description="The agent must remain professional and polite at all times.",
            severity=ComplianceSeverity.WARNING,
            rule_type="llm_check"
        )
    ]
    
    # If DB and Org provided, fetch custom rules
    if db and organization_id:
        policies = db.query(RegulatoryPolicy).filter(
            RegulatoryPolicy.organization_id == organization_id
        ).all()
        for p in policies:
            for r_data in (p.rules or []):
                # Convert JSON back to ComplianceRule
                rules.append(ComplianceRule(**r_data))
                
    return rules

redactor = PIIRedactor()
compliance_validator = ComplianceValidator()
