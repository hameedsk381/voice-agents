import time
from typing import Dict, List, Optional
from loguru import logger

class ProviderHealth:
    def __init__(self):
        self.provider_stats: Dict[str, Dict[str, Any]] = {
            "groq": {"latency": [], "failures": 0, "successes": 0},
            "openai": {"latency": [], "failures": 0, "successes": 0},
            "anthropic": {"latency": [], "failures": 0, "successes": 0},
        }

    def record_success(self, provider: str, latency: float):
        if provider not in self.provider_stats:
            self.provider_stats[provider] = {"latency": [], "failures": 0, "successes": 0}
        
        self.provider_stats[provider]["successes"] += 1
        self.provider_stats[provider]["latency"].append(latency)
        # Keep only last 20 latencies
        self.provider_stats[provider]["latency"] = self.provider_stats[provider]["latency"][-20:]

    def record_failure(self, provider: str):
        if provider not in self.provider_stats:
            self.provider_stats[provider] = {"latency": [], "failures": 0, "successes": 0}
        self.provider_stats[provider]["failures"] += 1

    def get_health_score(self, provider: str) -> float:
        """Returns a score from 0.0 (dead) to 1.0 (perfect)."""
        stats = self.provider_stats.get(provider)
        if not stats: return 0.0
        
        total = stats["successes"] + stats["failures"]
        if total == 0: return 1.0 # Default to healthy
        
        success_rate = stats["successes"] / total
        
        # Latency factor (penalty for avg > 2s)
        avg_latency = sum(stats["latency"]) / len(stats["latency"]) if stats["latency"] else 0
        latency_penalty = 0
        if avg_latency > 2000: # 2 seconds
            latency_penalty = min(0.5, (avg_latency - 2000) / 4000)
            
        return max(0.0, success_rate - latency_penalty)

health_manager = ProviderHealth()
