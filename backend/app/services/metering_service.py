"""
Metering service — rate cards and cost calculation for usage-based billing.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.billing import RateCard


DEFAULT_RATE_CARDS: Dict[str, Dict[str, dict]] = {
    "free": {
        "call_minutes": {"unit": "minutes", "price_per_unit": 0, "included_units": 50},
        "stt_seconds": {"unit": "seconds", "price_per_unit": 0, "included_units": 300},
        "tts_seconds": {"unit": "seconds", "price_per_unit": 0, "included_units": 300},
        "llm_tokens": {"unit": "tokens", "price_per_unit": 0, "included_units": 50_000},
        "messages_sent": {"unit": "count", "price_per_unit": 0, "included_units": 50},
    },
    "professional": {
        "call_minutes": {"unit": "minutes", "price_per_unit": 0.05, "included_units": 2000,
                         "overage_price_per_unit": 0.08},
        "stt_seconds": {"unit": "seconds", "price_per_unit": 0.006, "included_units": 12000,
                        "overage_price_per_unit": 0.01},
        "tts_seconds": {"unit": "seconds", "price_per_unit": 0.004, "included_units": 12000,
                        "overage_price_per_unit": 0.006},
        "llm_tokens": {"unit": "tokens", "price_per_unit": 0.000002, "included_units": 2_000_000,
                       "overage_price_per_unit": 0.000003},
        "messages_sent": {"unit": "count", "price_per_unit": 0.01, "included_units": 2000,
                          "overage_price_per_unit": 0.015},
    },
    "enterprise": {
        "call_minutes": {"unit": "minutes", "price_per_unit": 0.03, "included_units": float("inf")},
        "stt_seconds": {"unit": "seconds", "price_per_unit": 0.004, "included_units": float("inf")},
        "tts_seconds": {"unit": "seconds", "price_per_unit": 0.003, "included_units": float("inf")},
        "llm_tokens": {"unit": "tokens", "price_per_unit": 0.0000015, "included_units": float("inf")},
        "messages_sent": {"unit": "count", "price_per_unit": 0.008, "included_units": float("inf")},
    },
}


class MeteringService:
    def __init__(self, db: Session):
        self.db = db

    def get_rate_card(self, plan: str) -> Dict[str, Any]:
        cards = self.db.query(RateCard).filter(RateCard.plan == plan).all()
        if cards:
            result = {}
            for c in cards:
                result[c.metric] = {
                    "unit": c.unit,
                    "price_per_unit": c.price_per_unit,
                    "included_units": c.included_units,
                    "overage_price_per_unit": c.overage_price_per_unit,
                }
            return result
        return DEFAULT_RATE_CARDS.get(plan, DEFAULT_RATE_CARDS["free"])

    def seed_default_rate_cards(self) -> None:
        for plan, metrics in DEFAULT_RATE_CARDS.items():
            for metric, config in metrics.items():
                existing = self.db.query(RateCard).filter(
                    RateCard.plan == plan,
                    RateCard.metric == metric,
                ).first()
                if not existing:
                    card = RateCard(
                        plan=plan,
                        metric=metric,
                        unit=config["unit"],
                        price_per_unit=config["price_per_unit"],
                        included_units=config["included_units"],
                        overage_price_per_unit=config.get("overage_price_per_unit"),
                    )
                    self.db.add(card)
        self.db.commit()

    def calculate_cost(
        self,
        plan: str,
        usage: Dict[str, float],
    ) -> Dict[str, Any]:
        rate_card = self.get_rate_card(plan)
        total = 0.0
        breakdown = {}
        for metric, quantity in usage.items():
            config = rate_card.get(metric)
            if not config:
                continue
            included = config.get("included_units", 0) or 0
            base_price = config.get("price_per_unit", 0) or 0
            overage_price = config.get("overage_price_per_unit")

            if included == float("inf") or quantity <= included:
                cost = quantity * base_price
                breakdown[metric] = {
                    "quantity": quantity,
                    "included": included,
                    "base_cost": cost,
                    "overage_cost": 0,
                    "total": cost,
                }
                total += cost
                continue

            base_cost = included * base_price
            overage_units = quantity - included
            overage_unit_price = overage_price if overage_price is not None else base_price * 1.5
            overage_cost = overage_units * overage_unit_price
            cost = base_cost + overage_cost
            breakdown[metric] = {
                "quantity": quantity,
                "included": included,
                "base_cost": base_cost,
                "overage_cost": overage_cost,
                "overage_units": overage_units,
                "overage_price_per_unit": overage_unit_price,
                "total": cost,
            }
            total += cost

        return {
            "plan": plan,
            "total_cost": round(total, 6),
            "breakdown": breakdown,
        }

    def estimate_call_cost(
        self,
        plan: str,
        duration_minutes: float = 0,
        stt_seconds: float = 0,
        tts_seconds: float = 0,
        llm_tokens: int = 0,
    ) -> float:
        usage = {}
        if duration_minutes:
            usage["call_minutes"] = duration_minutes
        if stt_seconds:
            usage["stt_seconds"] = stt_seconds
        if tts_seconds:
            usage["tts_seconds"] = tts_seconds
        if llm_tokens:
            usage["llm_tokens"] = llm_tokens
        result = self.calculate_cost(plan, usage)
        return result["total_cost"]
