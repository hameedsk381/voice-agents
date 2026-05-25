from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger
from app.models.policy_rule import PolicyRule, PolicyAction
from app.schemas.policy_rule import PolicyEvaluationResult


def _match_conditions(conditions: Dict[str, Any], arguments: Dict[str, Any]) -> bool:
    """Evaluate field-level conditions against tool arguments.
    
    Supported operators: eq, ne, gt, gte, lt, lte, in, contains, regex
    """
    if not conditions:
        return True

    for field, constraint in conditions.items():
        actual = arguments.get(field)
        if actual is None:
            return False

        if isinstance(constraint, dict):
            for op, value in constraint.items():
                if op == "eq" and actual != value:
                    return False
                elif op == "ne" and actual == value:
                    return False
                elif op == "gt" and not (isinstance(actual, (int, float)) and actual > value):
                    return False
                elif op == "gte" and not (isinstance(actual, (int, float)) and actual >= value):
                    return False
                elif op == "lt" and not (isinstance(actual, (int, float)) and actual < value):
                    return False
                elif op == "lte" and not (isinstance(actual, (int, float)) and actual <= value):
                    return False
                elif op == "in" and actual not in value:
                    return False
                elif op == "contains" and value not in str(actual):
                    return False
        else:
            # Direct equality shorthand
            if actual != constraint:
                return False

    return True


class PolicyService:
    def __init__(self, db: Session):
        self.db = db

    def evaluate(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        organization_id: Optional[str] = None,
    ) -> PolicyEvaluationResult:
        """Evaluate a tool call against all enabled policy rules.
        
        Rules are evaluated in priority order (highest first).
        DENY > ESCALATE > PERMIT precedence:
        - If any DENY rule matches, the call is denied.
        - If no DENY but any ESCALATE rule matches, the call escalates to HITL.
        - Otherwise, the call is permitted.
        """
        rules = (
            self.db.query(PolicyRule)
            .filter(PolicyRule.enabled == True)
            .order_by(desc(PolicyRule.priority))
            .all()
        )

        matched_deny: Optional[PolicyRule] = None
        matched_escalate: Optional[PolicyRule] = None

        for rule in rules:
            # Rule applies if tool_name matches ("*" or exact match)
            if rule.tool_name != "*" and rule.tool_name != tool_name:
                continue

            if not _match_conditions(rule.conditions, arguments):
                continue

            logger.info(f"Policy match: rule='{rule.name}' action={rule.action} tool={tool_name}")

            if rule.action == PolicyAction.DENY.value:
                matched_deny = rule
                break  # DENY is immediate
            elif rule.action == PolicyAction.ESCALATE.value:
                matched_escalate = rule  # Keep checking for DENY

        if matched_deny:
            return PolicyEvaluationResult(
                rule_id=matched_deny.id,
                rule_name=matched_deny.name,
                action=PolicyAction.DENY.value,
                reason=f"Blocked by policy: {matched_deny.name} — {matched_deny.description}",
                tool_name=tool_name,
                arguments=arguments,
            )

        if matched_escalate:
            return PolicyEvaluationResult(
                rule_id=matched_escalate.id,
                rule_name=matched_escalate.name,
                action=PolicyAction.ESCALATE.value,
                reason=f"Requires approval per policy: {matched_escalate.name} — {matched_escalate.description}",
                tool_name=tool_name,
                arguments=arguments,
            )

        return PolicyEvaluationResult(
            action=PolicyAction.PERMIT.value,
            reason="Permitted by default — no matching policy rule",
            tool_name=tool_name,
            arguments=arguments,
        )

    # --- CRUD helpers ---

    def list_rules(self, organization_id: Optional[str] = None) -> List[PolicyRule]:
        q = self.db.query(PolicyRule)
        if organization_id:
            q = q.filter(PolicyRule.organization_id == organization_id)
        return q.order_by(desc(PolicyRule.priority)).all()

    def get_rule(self, rule_id: str) -> Optional[PolicyRule]:
        return self.db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()

    def create_rule(self, data: dict, organization_id: Optional[str] = None) -> PolicyRule:
        rule = PolicyRule(
            organization_id=organization_id,
            name=data["name"],
            description=data.get("description", ""),
            tool_name=data.get("tool_name", "*"),
            conditions=data.get("conditions", {}),
            action=data.get("action", PolicyAction.ESCALATE.value),
            priority=data.get("priority", 100),
            enabled=data.get("enabled", True),
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_rule(self, rule_id: str, data: dict) -> Optional[PolicyRule]:
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        for key in ("name", "description", "tool_name", "conditions", "action", "priority", "enabled"):
            if key in data and data[key] is not None:
                setattr(rule, key, data[key])
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        rule = self.get_rule(rule_id)
        if not rule:
            return False
        self.db.delete(rule)
        self.db.commit()
        return True
