from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.analytics import ShadowLog
from app.services.llm.groq_provider import GroqLLM

class ShadowComparisonService:
    def __init__(self, db: Session):
        self.db = db
        # Use 70b model for better accuracy in shadow comparison
        self.shadow_llm = GroqLLM(model="llama-3.3-70b-versatile")
        
    async def compare_turn(
        self,
        session_id: str,
        turn_index: int,
        user_input: str,
        system_prompt: str,
        history: List[Dict[str, str]],
        primary_response: str,
        primary_model_name: str,
        primary_latency: float,
        organization_id: str = None,
        tools: List = None
    ):
        """
        Runs the shadow model and logs comparison metrics.
        Executed in background to avoid blocking the main voice pipeline.
        """
        import time
        start_time = time.time()
        
        try:
            # 1. Generate Shadow Response
            shadow_response_text = ""
            
            if tools:
                try:
                    # Shadow agent also attempts to use tools
                    shadow_resp, _ = await self.shadow_llm.generate_with_tools(
                        user_input, system_prompt, history, tools
                    )
                    shadow_response_text = shadow_resp or ""
                except Exception as tool_err:
                    logger.warning(f"Shadow tool-calling failed, falling back to text: {tool_err}")
                    shadow_response_text = await self.shadow_llm.generate_response(
                        user_input, system_prompt, history
                    )
            else:
                shadow_response_text = await self.shadow_llm.generate_response(
                    user_input, system_prompt, history
                )
                
            shadow_duration = (time.time() - start_time) * 1000
            
            if not shadow_response_text:
                shadow_response_text = "[NO_RESPONSE]"
                
            # 2. Simple Similarity Heuristic (Token Overlap)
            set1 = set(primary_response.lower().split())
            set2 = set(shadow_response_text.lower().split())
            if not set1 or not set2:
                cos_sim = 0.0
            else:
                intersection = set1.intersection(set2)
                cos_sim = len(intersection) / max(len(set1), len(set2))
            
            # 3. Log Comparison
            log = ShadowLog(
                session_id=session_id,
                organization_id=organization_id,
                turn_index=turn_index,
                primary_model=primary_model_name,
                shadow_model=self.shadow_llm.model,
                primary_response=primary_response,
                shadow_response=shadow_response_text,
                similarity_score=float(cos_sim),
                primary_latency_ms=primary_latency,
                shadow_latency_ms=shadow_duration,
                intent_match=(cos_sim > 0.85) # Simple heuristic for now
            )
            self.db.add(log)
            self.db.commit()
            
            logger.info(f"Shadow Run [Turn {turn_index}]: Sim={cos_sim:.2f}, LatencyDiff={shadow_duration - primary_latency:.0f}ms")
            
        except Exception as e:
            logger.error(f"Shadow Comparison Failed: {e}")

# Factory
def get_shadow_service(db: Session):
    return ShadowComparisonService(db)
