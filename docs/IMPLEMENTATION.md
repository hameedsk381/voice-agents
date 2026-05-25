# Voise AI — Enterprise Production-Grade Implementation Plan

Based on 2026 industry research (McKinsey, MongoDB, Google Cloud, Microsoft Agent Framework, OWASP Agentic Top 10, Gartner) and gap analysis against the current codebase.

---

## Overview

The current Voise AI platform is a functional voice-agent MVP with CRUD, basic orchestration, compliance auditing, and analytics. To reach enterprise production-grade, eight capability phases are needed across four architectural pillars: **Reliability**, **Governance**, **Observability**, and **Intelligence**.

---

## Architecture Principles

1. **Deterministic boundaries around stochastic cores** — every LLM call is wrapped with verifiers, pre-checks, and commit/rollback semantics (the Stochastic-Deterministic Boundary pattern).
2. **Fails closed** — denied by default. Every agent action requires explicit policy allowance.
3. **Observable by construction** — every decision, tool call, and state transition emits a trace event.
4. **No shared mutable state** — agents communicate through durable message passing, not shared memory.
5. **Layers are separable** — each phase can ship independently without waiting for the next.

---

## Phase 1: Observability Stack (2-3 weeks)

### Why First
Enterprise procurement's #1 criterion in 2026. 60-72% of agent pilots without observability stall. Required before any production deployment.

### What to Build

#### 1.1 OpenTelemetry Instrumentation

**Backend** (`backend/app/core/telemetry.py` — new file)

```
- Initialize OTel TracerProvider with OTLP exporter
- Add instrumentations: FastAPI, SQLAlchemy, HTTPX, custom agent spans
- Configure span processors (batch export, sampled on production)
- Add resource attributes: service.name=voise-backend, environment=production
```

**Key spans to create:**

| Span Name | When | Attributes |
|-----------|------|------------|
| `agent.call` | Full call lifecycle | `agent_id`, `caller_id`, `language`, `duration_ms` |
| `llm.generate` | Per LLM call | `model`, `provider`, `tokens_in`, `tokens_out`, `latency_ms` |
| `tool.invoke` | Per tool call | `tool_name`, `args`, `result_size`, `success` |
| `stt.transcribe` | Per STT call | `provider`, `audio_duration_ms`, `latency_ms` |
| `tts.synthesize` | Per TTS call | `provider`, `text_length`, `latency_ms` |
| `policy.evaluate` | Per policy check | `rule_count`, `decision`, `risk_score` |
| `compliance.audit` | Per compliance check | `violations`, `risk_score` |

**Wire up in existing services:**

- `ultravox_call.py` — wrap `start_call()`, `end_call()` with `agent.call` span
- `llm/groq_provider.py` — wrap `generate_response()` with `llm.generate` span
- `turn_processor.py` — wrap each turn cycle
- `tts/` and `stt/` providers — wrap synthesize/transcribe

#### 1.2 Trace Store Backend

```
- Deploy LangFuse or Helicone as the trace store (self-hosted OSS or cloud)
- Wire OTel exporter to send spans to the trace store
- Configure 30-day retention (expand to 90/400 in enterprise tier)
```

#### 1.3 Eval Suite

**New service** (`backend/app/services/evaluation_service.py`)

```
class EvaluationService:
    - run_eval_suite(agent_id, golden_set) -> EvalReport
    - run_single_test(agent, test_case) -> TestResult
    - continuous_eval(agent_id, live_sample_rate=0.1)  # sample production traffic
```

**Eval dimensions:**

| Dimension | Method | Metric |
|-----------|--------|--------|
| Groundedness | LLM-as-judge checks response against context | Score 0-1 |
| Instruction following | LLM checks agent followed persona + goals | Pass/fail |
| Safety | Compliance rules evaluated on response | Violation count |
| Task success | Outcome matches success_criteria | SUCCESS/FAILURE/NEUTRAL |
| Latency SLA | Per-call latency percentiles | P50, P95, P99 |
| Cost efficiency | Cost per completed call | $/call |

**Golden test set** (`backend/app/data/eval_sets/`)

```
- 10-20 golden test cases per agent type
- Each: input transcript + expected outcome + expected tool calls
- Version-controlled in repo, updated on each agent release
```

#### 1.4 Failure-Mode Dashboard

**New frontend page** (`frontend/src/app/dashboard/observability/page.tsx`)

```
- Real-time trace stream (last 100 calls)
- Per-call trace viewer (waterfall chart of spans)
- Failure-mode aggregator:
  - Top failure reasons by agent
  - Tool failure rate by tool
  - Latency heatmap by hour
  - Cost-per-call trend
- SLA gauges: uptime, P95 latency, success rate
```

#### 1.5 Existing Integration Points

| Current Component | What Connects | How |
|-------------------|--------------|-----|
| `CallLog` model | Trace events are persisted here | OTel span exports to CallLog on call completion |
| `AnalyticsService` | Aggregates from CallLog | Add eval score columns to CallLog |
| `MonitoringService` | Real-time Redis Pub/Sub | Add OTel span export to monitoring stream |
| Dashboard analytics | Aggregate stats | Add trace-level drill-down from summary cards |

---

## Phase 2: Pre-Execution Policy Engine + HITL Approval Gates (3-4 weeks)

### Why Second
Without pre-execution enforcement, agents can attempt destructive actions. Enterprise CIOs require deny-before-execute, not detect-after-the-fact.

### Architecture

```
Agent action request
  ↓
┌─────────────────────────────────┐
│  Policy Engine (deterministic)  │  ← Rules defined in YAML
│                                 │
│  PERMIT ──→ Execute action      │
│  DENY   ──→ Return blocked      │
│  ESCALATE → HITL approval queue │
└─────────────────────────────────┘
```

### What to Build

#### 2.1 Declarative Policy Schema

**New schema** (`backend/app/schemas/policy_rules.py`)

```python
class PolicyRule(BaseModel):
    id: str
    name: str
    description: str
    severity: Literal["info", "warning", "critical"]
    action: Literal["permit", "deny", "escalate"]
    rule_type: Literal["regex", "semantic", "capability", "rate_limit", "budget"]
    config: Dict[str, Any]

class PolicyBundle(BaseModel):
    version: str
    rules: List[PolicyRule]
    default_action: Literal["permit", "deny"] = "deny"  # fail closed
```

Default action is **deny** — every action must be explicitly allowed.

#### 2.2 Deterministic Policy Engine

**New service** (`backend/app/services/policy_service.py`)

```
class PolicyService:
    def evaluate(action: AgentAction, context: PolicyContext) -> PolicyDecision:
        1. Gather applicable rules (global + agent-specific)
        2. Run regex rules (fast path)
        3. Run capability rules (is this tool allowed for this agent?)
        4. Run budget rules (has agent exceeded cost/token limits?)
        5. Run semantic rules (LLM-judge, sampled)
        6. Return PERMIT / DENY / ESCALATE

    Precedence: DENY > ESCALATE > PERMIT
    Fast path (<5ms) for regex + capability rules
    Slow path for semantic rules (async, sampled)
```

#### 2.3 Policy Rule Categories

| Category | Example | Evaluation |
|----------|---------|------------|
| **Regex** | Block phone numbers in output | <1ms, synchronous |
| **Capability** | Agent cannot call delete_customer | <1ms, capability matrix |
| **Budget** | Agent exceeded $5 daily budget | <5ms, Redis counter |
| **Rate limit** | Max 10 API calls/minute | <5ms, Redis sliding window |
| **Semantic** | Check if response contains financial advice | ~500ms, LLM-judge, sampled |
| **Sensitive data** | Block PII in outbound responses | <1ms, regex pre-check |

#### 2.4 Human-in-the-Loop Approval Queue

**New model** (`backend/app/models/approval.py`)

```
class ApprovalRequest(BaseModel):
    id: str (uuid)
    agent_id: str
    action: str  # tool name
    args: Dict  # tool arguments
    reason: str  # why escalation was triggered
    policy_rule: str  # which rule triggered escalation
    status: Literal["pending", "approved", "rejected"]
    requested_at: datetime
    decided_at: Optional[datetime]
    decided_by: Optional[str]  # user ID
```

**New endpoint** (`backend/app/api/endpoints/approvals.py`)

```
GET  /approvals/            - List pending approvals
POST /approvals/{id}/approve - Approve action
POST /approvals/{id}/reject  - Reject action
GET  /approvals/history     - Approval history
```

**New frontend** — Approval queue panel in the existing `/dashboard/approvals` page.

**Integration with existing `turn_processor.py`:**

```python
# Before executing any tool:
decision = await policy_service.evaluate(action, context)
if decision == PolicyDecision.DENY:
    return "I'm sorry, I cannot perform that action."
if decision == PolicyDecision.ESCALATE:
    approval = await ApprovalService.create_request(action, context)
    return "Let me check with my supervisor about that."
    # Wait for HITL approval (async via WebSocket or polling)
```

#### 2.5 Wire Into Existing Components

| Current File | Change |
|-------------|--------|
| `turn_processor.py` | Add `policy_service.evaluate()` before every tool call and response send |
| `policy_engine.py` | Extend to call `PolicyService` instead of inline checks |
| `compliance_service.py` | Keep for post-hoc audit, add pre-execution hook to PolicyService |
| `orchestrator.py` | Add policy evaluation before call creation |
| `ultravox_call.py` | Add policy check before tool execution in agent loop |

---

## Phase 3: Durable Execution (2-3 weeks)

### Why Third
Without durable execution, a crash mid-call loses all state. Required for long-running or complex workflows.

### What to Build

#### 3.1 Checkpoint Store

**New service** (`backend/app/services/checkpoint_service.py`)

```python
class CheckpointService:
    async def save(session_id: str, turn_index: int, state: Dict):
        # Serialize: conversation history, tool results, current goal, agent state
        # Store in Postgres (call_checkpoints table)

    async def load(session_id: str) -> Optional[Checkpoint]:
        # Load most recent checkpoint

    async def list_sessions(agent_id: str) -> List[SessionInfo]:
        # List active sessions for recovery
```

**New model** (`backend/app/models/checkpoint.py`)

```
class CallCheckpoint(Base):
    id: str PK
    session_id: str (indexed)
    agent_id: str
    turn_index: int
    state_json: JSON  # full serialized state
    created_at: datetime
```

#### 3.2 Crash Recovery Handler

```python
# In turn_processor.py:
async def resume_after_crash(session_id: str) -> bool:
    checkpoint = await checkpoint_service.load(session_id)
    if not checkpoint:
        return False
    
    # Restore state, replay last turn if incomplete
    # Continue from last completed turn
```

#### 3.3 Integration Points

| Current File | Change |
|-------------|--------|
| `turn_processor.py` | Save checkpoint after each completed turn; load checkpoint on start |
| `ultravox_call.py` | Add crash recovery hook in call setup |
| `analytics_service.py` | Add checkpoint metadata to CallLog |

---

## Phase 4: Multi-Agent Orchestration (4-6 weeks)

### Why Fourth
Complex use cases need agent chaining: a call agent hands off to a payment agent, which escalates to a human agent.

### What to Build

#### 4.1 DAG Workflow Engine

**New service** (`backend/app/services/workflow_engine.py`)

```
class WorkflowEngine:
    def create_workflow(definition: WorkflowDefinition) -> WorkflowInstance
    def execute_step(instance_id, step_name) -> StepResult
    def fan_out(instance_id, steps: List[Step]) -> List[StepResult]
    def fan_in(instance_id, join_key: str) -> StepResult
    def handle_dead_letter(instance_id, failed_step) -> None
```

**Workflow definition** (YAML or JSON):

```yaml
workflow:
  id: payment-collection
  steps:
    - name: classify_intent
      agent: classifier
      input: $call.transcript
      output: intent
    
    - name: collect_payment
      agent: payment-agent
      depends_on: [classify_intent]
      condition: $intent == "payment"
      input: $call.caller_id
      output: payment_result
    
    - name: escalate_human
      agent: escalation
      depends_on: [collect_payment]
      condition: $payment_result == "failed" || $call.turns > 10
      output: escalation_ticket
```

#### 4.2 Agent Registry

**New endpoint** (`backend/app/api/endpoints/agent_registry.py`)

```
GET  /registry/agents       - List all agents with capabilities
POST /registry/agents       - Register agent
GET  /registry/capabilities - List available capabilities
```

**Agent capability model:**

```python
class AgentCapability(BaseModel):
    agent_id: str
    name: str
    description: str
    capabilities: List[str]  # ["voice-call", "payment-collection", "language-hi"]
    input_schema: Dict
    output_schema: Dict
    cost_per_call: float
```

#### 4.3 Inter-Agent Communication Protocol

```
- Agents communicate through a message bus (Redis Streams or NATS)
- Each message has: source_agent_id, target_agent_id, payload, trace_id, correlation_id
- Supports: request/response, fire-and-forget, pub/sub
- All messages are logged for audit
```

#### 4.4 Integration Points

| Current File | Change |
|-------------|--------|
| `workflows/` directory | Extend existing workflow model to support DAG execution |
| `agent_config.py` | Add capability resolution for agent routing |
| `orchestrator.py` | Add workflow engine call before agent execution |

---

## Phase 5: Agent Identity + Cryptographic Audit Chain (2-3 weeks)

### Why Fifth
SOC 2 and EU AI Act compliance require provable agent identity and tamper-proof audit trails.

### What to Build

#### 5.1 Agent Identity

```python
# backend/app/services/identity_service.py
class IdentityService:
    def issue_agent_identity(agent_id: str) -> AgentIdentity:
        # Generate Ed25519 keypair
        # Issue SPIFFE-compatible certificate
        # Store public key in identity store
        # Return signed identity document
    
    def verify_action(action: AgentAction, signature: str) -> bool:
        # Verify HMAC-SHA256 signature matches agent's identity
    
    def rotate_keys(agent_id: str) -> None:
        # Periodic key rotation
```

#### 5.2 Audit Chain

```python
# backend/app/services/audit_service.py
class AuditService:
    def append(entry: AuditEntry) -> AuditChain:
        # Create entry with: timestamp, agent_id, action, args_hash, 
        #   previous_entry_hash, signature
        # Store in append-only audit_logs table
        # Return updated chain head
    
    def verify_chain(agent_id: str) -> bool:
        # Walk linked list of entries, verify each signature
        # Ensure no entries have been tampered with
    
    def export_for_compliance(agent_id: str, start: datetime, end: datetime) -> AuditReport:
        # Generate compliance-ready report
```

**New model** — extend existing `AuditLog` with chain fields:

```
- signature: str (HMAC-SHA256 of entry)
- previous_hash: str (SHA256 of previous entry)
- chain_head: bool (is this the latest entry?)
```

#### 5.3 Integration Points

| Current File | Change |
|-------------|--------|
| `compliance_service.py` | Add identity verification before compliance check |
| `turn_processor.py` | Sign every turn with agent identity |
| `audit_log` model | Add chain fields |
| `ultravox_call.py` | Add agent identity to call setup |

---

## Phase 6: Multi-Layer Memory (3-4 weeks)

### Why Sixth
Agents repeat mistakes without persistent memory across sessions. Reduces error rate, improves personalization.

### Architecture

```
┌─────────────────────────────────────────┐
│           Memory Service                 │
│                                         │
│  Episodic  │  Working  │  Long-term     │
│  (this     │  (this    │  (across       │
│   call)    │   task)   │   calls)       │
│                                         │
│  Procedural (how to do things)          │
│  Memory Governance (TTLs, consent)      │
└─────────────────────────────────────────┘
```

### What to Build

#### 6.1 Memory Store

**New service** (`backend/app/services/memory_service.py`)

```
class MemoryService:
    # Episodic — conversation turns (already exists in transcript)
    
    # Working — current task state
    async def set_working(agent_id: str, key: str, value: Any, ttl: int = 300)
    async def get_working(agent_id: str, key: str) -> Optional[Any]
    
    # Long-term — across calls
    async def store_long_term(agent_id: str, caller_id: str, 
                               fact: str, category: str, ttl: Optional[int])
    async def recall(agent_id: str, caller_id: str, 
                     category: Optional[str]) -> List[MemoryFact]
    
    # Procedural — how to execute common patterns
    async def store_procedure(agent_id: str, name: str, steps: List[str])
    async def recall_procedure(agent_id: str, name: str) -> Optional[List[str]]
    
    # Governance
    async def set_consent(caller_id: str, consent_type: str, granted: bool)
    async def forget(caller_id: str, category: Optional[str])
    async def get_ttl(memory_id: str) -> int
```

**New model** (`backend/app/models/memory.py`):

```
class MemoryFact(Base):
    id, agent_id, caller_id, fact, category (str),
    ttl_seconds (int), consent_granted (bool),
    created_at, expires_at (indexed)

class WorkingMemory(Base):
    agent_id, session_id, key, value (JSON),
    created_at, expires_at

class ProceduralMemory(Base):
    agent_id, name, steps (JSON), created_at, updated_at
```

#### 6.2 Memory-Aware Agent Prompting

Update `build_system_prompt()` in `ultravox_call.py`:

```python
# Before building system prompt:
working = await memory_service.get_working(agent_id, "current_goal")
long_term = await memory_service.recall(agent_id, caller_id, category="preferences")
procedure = await memory_service.recall_procedure(agent_id, "payment_collection")

# Inject into system prompt template
prompt = f"""
{base_prompt}

CONTEXT FROM PAST INTERACTIONS:
{format_memories(long_term)}

CURRENT TASK:
{working}

PROCEDURE TO FOLLOW:
{format_procedure(procedure)}
"""
```

#### 6.3 Memory Governance

```
- PII-aware: never store PII in memory (redact before write)
- Consent-aware: check caller consent before reading/writing long-term memory
- TTL enforcement: periodic cleanup of expired memories
- "Forget me" endpoint: GDPR Article 17 compliance
- Memory audit log: every read/write is logged
```

---

## Phase 7: Kubernetes Deployment (2-3 weeks)

### Why Seventh
Horizontal scaling, HA, and CI/CD are required for production SLA commitments.

### What to Build

#### 7.1 Helm Chart

```
voise-chart/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment-backend.yaml
│   ├── deployment-frontend.yaml
│   ├── statefulset-postgres.yaml
│   ├── statefulset-redis.yaml
│   ├── service-backend.yaml
│   ├── service-frontend.yaml
│   ├── ingress.yaml
│   ├── hpa-backend.yaml
│   ├── configmap.yaml
│   └── secrets.yaml
```

#### 7.2 Scaling Configuration

```
- Backend: HorizontalPodAutoscaler (CPU > 70% → scale up)
- Frontend: static deployment behind CDN
- Postgres: StatefulSet with persistent volumes, replica for HA
- Redis: StatefulSet with sentinel for HA
```

#### 7.3 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- Build Docker images
- Push to container registry
- Run migration jobs
- Canary deploy (10% traffic, 5 min observation)
- Full rollout
- Smoke tests
```

---

## Phase 8: Voice-Specific Intelligence (4-6 weeks)

### Why Eighth
Differentiator that makes Voise AI feel human rather than robotic. Premium feature for enterprise CX.

### What to Build

#### 8.1 Confidence-Aware Decisioning

```
- Track confidence at every layer:
  - STT confidence score per utterance
  - Intent classification confidence
  - Tool result confidence (did the API succeed?)
  - LLM self-confidence (ask LLM to rate its own certainty)

- Decision matrix:
  - High confidence → proceed normally
  - Medium confidence → ask clarifying question
  - Low confidence → conservative response, offer escalation
```

#### 8.2 Emotional State Tracking

```
# backend/app/services/emotion_service.py
class EmotionTracker:
    def analyze_turn(text: str, silence_duration: float, 
                     interrupt_frequency: int) -> EmotionalState:
        # Extract: sentiment, frustration level, hesitation markers
        # Track trend across turns (not single-point)
    
    def should_adapt(history: List[EmotionalState]) -> Adaptation:
        # Slower pace when confused
        # Calmer tone when angry
        # Shorter responses under stress
```

**Tracked signals:**

| Signal | Source | Meaning |
|--------|--------|---------|
| Sentiment score | LLM text analysis | Positive/negative trend |
| Silence duration | Voice activity detection | Hesitation, confusion |
| Interrupt frequency | Barge-in detection | Frustration, urgency |
| Turn cadence | Turn timing | Engagement level |
| Response length | Agent output | Verbosity under stress |

#### 8.3 Self-Correction

```
- Mid-sentence correction: detect hallucination mid-stream, 
  emit "Sorry, let me correct that" and restart
- Apology + rephrase flows for known failure modes
- Recovery from tool errors with conversational grace
```

#### 8.4 Turn & Interruption Control

```
- Turn ownership tracking: who has the floor
- Barge-in detection: detect when user interrupts
- Graceful yield: stop speaking, let user finish, resume intelligently
- Partial utterance rollback: don't act on incomplete input
```

#### 8.5 Time Awareness

```
- Track call_duration, silence_time, remaining budget
- Speed up near call end (shorter responses)
- Summarize if time is running out
- Avoid new topics late in call
```

#### 8.6 Cost Awareness

```
- Track real-time cost per call (tokens × model rate)
- Set cost budgets per call/agent/campaign
- Auto-downgrade model when approaching budget
- Surface cost data in agent decision loop
```

#### 8.7 End-of-Call Intelligence

```python
# After call ends:
class EndOfCallService:
    def classify_outcome(transcript) -> Outcome:  # exists partially
    def estimate_satisfaction(transcript, emotion_history) -> float
    def generate_summary(transcript) -> str
    def schedule_next_steps(summary) -> List[NextStep]
    def write_memories(summary, facts) -> None  # feed long-term memory
    def tag_for_human_review(transcript, flags) -> bool
```

---

## Implementation Order

```
Week 1-3:   Phase 1 (Observability) — required for all production use
Week 4-7:   Phase 2 (Policy Engine + HITL) — unblocks enterprise security review
Week 8-10:  Phase 3 (Durable Execution) — enables long-running calls
Week 11-16: Phase 4 (Multi-Agent Orchestration) — complex use cases
Week 17-19: Phase 5 (Agent Identity + Audit) — SOC 2 compliance
Week 20-23: Phase 6 (Multi-Layer Memory) — agent intelligence
Week 24-26: Phase 7 (Kubernetes) — production reliability
Week 27-32: Phase 8 (Voice Intelligence) — CX differentiator
```

**Total: ~32 weeks for full enterprise readiness.**
**Minimum viable enterprise (Phases 1-3): ~10 weeks.**

---

## File Change Summary

| Phase | New Files | Modified Files |
|-------|-----------|----------------|
| 1 | `core/telemetry.py`, `services/evaluation_service.py`, `data/eval_sets/` | `turn_processor.py`, `groq_provider.py`, `stt/*`, `tts/*`, `ultravox_call.py` |
| 2 | `schemas/policy_rules.py`, `services/policy_service.py`, `models/approval.py`, `endpoints/approvals.py` | `turn_processor.py`, `policy_engine.py`, `compliance_service.py`, `orchestrator.py`, `ultravox_call.py` |
| 3 | `models/checkpoint.py`, `services/checkpoint_service.py` | `turn_processor.py`, `ultravox_call.py`, `analytics_service.py` |
| 4 | `services/workflow_engine.py`, `models/workflow_instance.py`, `endpoints/agent_registry.py` | `agent_config.py`, `orchestrator.py`, `workflows/` |
| 5 | `services/identity_service.py`, `services/audit_service.py` | `compliance_service.py`, `turn_processor.py`, `ultravox_call.py` |
| 6 | `models/memory.py`, `services/memory_service.py`, `services/emotion_service.py` | `ultravox_call.py`, `turn_processor.py` |
| 7 | `charts/voise-chart/`, `.github/workflows/deploy.yml` | `Dockerfile`, `docker-compose.yml` |
| 8 | `services/emotion_service.py` (if not phase 6), `services/end_of_call_service.py` | `turn_processor.py`, `ultravox_call.py`, `analytics_service.py` |
