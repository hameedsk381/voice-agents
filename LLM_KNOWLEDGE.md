# Voise AI — LLM Knowledge Doc

This document is optimized for LLM consumption. It provides a complete, structured view of the project.

**Last updated:** May 2026 · **Workflow automation:** Phase 1 & 2 ✅ — see [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md) · **Doc index:** [DOCS.md](./DOCS.md)

---

## 1. IDENTITY

**Voise AI** is an AI-powered voice automation platform for operational workflows. It lets teams deploy AI outbound call agents for payment reminders, lead qualification, and appointment confirmation.

**Tagline:** A real-time autonomous system with goals, constraints, memory, tools, confidence, and recovery — not just LLM + STT + TTS.

---

## 2. REPOSITORY STRUCTURE

```
voice-agents/
├── backend/                          # FastAPI Python backend
│   ├── main.py                       # FastAPI entry point, CORS, health check
│   ├── requirements.txt              # FastAPI 0.109, SQLAlchemy 2.0, Temporal, OpenAI, etc.
│   ├── alembic.ini
│   ├── alembic/                      # 24+ migration files
│   ├── scripts/
│   │   └── seed_demo_data.py         # Demo user demo@voise.ai / DemoVoise2026!
│   │   ├── env.py
│   │   └── versions/                 # Migrations: initial schema → multi-tenancy → memory governance
│   ├── test_agents_direct.py         # WebSocket agent tests
│   ├── test_langgraph.py             # LangGraph multi-agent routing tests
│   ├── test_smart_agent.py           # Smart agent (sentiment, RAG, reflection) tests
│   └── app/
│       ├── __init__.py
│       ├── core/                     # Config, DB, security, logging, Redis
│       │   ├── config.py             # Pydantic Settings (.env): DB, Redis, Temporal, API keys
│       │   ├── database.py           # SQLAlchemy engine + SessionLocal + get_db()
│       │   ├── deps.py               # Auth deps: get_current_user, require_roles()
│       │   ├── security.py           # JWT (python-jose), bcrypt (passlib)
│       │   ├── logging.py            # Loguru bridge
│       │   └── redis.py              # Async Redis pool
│       ├── api/
│       │   ├── api.py                # Root router, includes 14 endpoint modules
│       │   └── endpoints/
│       │       ├── auth.py           # Register, login, refresh, user CRUD, admin ops
│       │       ├── agents.py         # Agent CRUD + version management + pinning
│       │       ├── orchestrator.py   # **CORE (1404 lines)**: WebSocket voice loop, REST chat, Ultravox proxy
│       │       ├── memory.py         # Memorize, retrieve, GDPR delete
│       │       ├── knowledge.py      # Agent knowledge base (RAG) CRUD + query
│       │       ├── telephony.py      # Twilio voice webhooks, Ultravox data WS, outbound
│       │       ├── voices.py         # List, design, clone, delete TTS voices
│       │       ├── monitoring.py     # Active sessions, session WS stream, global WS stream
│       │       ├── campaigns.py      # Campaign CRUD + CSV + start (workflow_id optional)
│       │       ├── workflows.py      # Workflow CRUD, instances, SAP ingest, process-due
│       │       ├── analytics.py      # Overview, trends, agent perf, shadow stats, call logs
│       │       ├── hitl.py           # Pending actions, approve/reject, takeover/whisper
│       │       ├── marketplace.py    # Agent templates, install
│       │       └── ultravox_webhooks.py # Ultravox call.ended webhooks
│       ├── schemas/                  # Pydantic models
│       │   ├── agent.py              # AgentCreate, AgentVersion, etc.
│       │   ├── knowledge.py          # KnowledgeBase, KnowledgeCreate
│       │   ├── compliance.py         # ComplianceRule, Violation, CheckResult, Severity
│       │   ├── policy.py             # ConversationPolicy, State, Transition, Guardrail
│       │   └── orchestrator.py       # ChatRequest, ChatResponse
│       ├── models/                   # SQLAlchemy ORM models
│       │   ├── agent.py              # Agent, AgentVersion
│       │   ├── workflow.py           # Workflow, WorkflowInstance, EmailMessage
│       │   ├── user.py               # User + UserRole enum
│       │   ├── tenant.py             # Organization (multi-tenancy root)
│       │   ├── memory.py             # MemoryItem, ConversationSummary, UserProfile (with pgvector)
│       │   ├── knowledge.py          # AgentKnowledge (RAG chunks with pgvector)
│       │   ├── compliance.py         # AuditLog, RegulatoryPolicy
│       │   ├── campaign.py           # Campaign, CampaignContact + enums
│       │   ├── analytics.py          # CallLog, ShadowLog
│       │   └── hitl.py              # PendingAction, SessionIntervention
│       ├── workflows/                # **IN-APP WORKFLOW AUTOMATION (Ph1+2 done)**
│       │   ├── schema.py             # WorkflowDefinitionV1, NodeType, ConditionRule
│       │   ├── engine.py             # WorkflowEngine: execute nodes until wait/done
│       │   ├── templates.py          # collections, lead-qual, appointment templates
│       │   └── sap_ingest.py         # SAP AR CSV field normalization
│       ├── orchestration/            # **VOICE SESSION BRAIN**
│       │   ├── agent_orchestrator.py # AgentOrchestrator, AgentContext, ConfidenceScores
│       │   ├── turn_processor.py     # Turn pipeline (extracted from monolith)
│       │   ├── audio_handler.py      # Audio / TTS streaming helpers
│       │   ├── tool_executor.py      # Tool execution
│       │   ├── websocket_proxy.py    # WS proxy utilities
│       │   ├── agent_swarm.py        # SwarmOrchestrator
│       │   ├── langgraph_orchestrator.py # LangGraph StateGraph
│       │   ├── session_manager.py    # Redis session persistence
│       │   ├── policy_engine.py      # PolicyEngine
│       │   ├── tool_planner.py       # ToolPlanner
│       │   ├── workflows.py          # Temporal CallWorkflow (telephony lifecycle)
│       │   ├── workflow_activities.py # Temporal: process_due_workflow_instances (stub wire-up)
│       │   ├── ultravox_call.py / ultravox_twilio.py # Ultravox + Twilio integration
│       │   └── worker.py             # Temporal worker
│       └── services/
│           ├── llm/
│           │   ├── base.py           # Abstract LLMProvider
│           │   ├── groq_provider.py  # GroqLLM: llama-3.3-70b, tool-calling, streaming
│           │   ├── openai_provider.py # OpenAILLM: gpt-3.5-turbo
│           │   ├── enterprise_llm.py # EnterpriseLLM: multi-provider with health-aware failover
│           │   └── health_manager.py # ProviderHealth: tracks latency + failures per model
│           ├── tts/
│           │   ├── base.py           # Abstract TTSProvider
│           │   ├── qwen_provider.py  # QwenTTS: local server (port 8008), voice design, cloning
│           │   ├── deepgram_provider.py # DeepgramTTS: aura-asteria-en, multilingual
│           │   └── mock_provider.py  # MockTTS: b"mock_audio_data" + 0.5s delay
│           ├── stt/
│           │   ├── base.py           # Abstract STTProvider
│           │   ├── deepgram_provider.py # DeepgramSTT: nova-2, streaming
│           │   └── mock_provider.py  # MockSTT: fixed transcript + 0.5s delay
│           ├── tools/
│           │   ├── base.py           # Abstract BaseTool with execute() + to_schema()
│           │   ├── registry.py       # 8 built-in tools: GetOrderStatus, CheckBalance, ScheduleCallback, TransferToHuman, WebSearch, RefundCustomer (approval-gated), SearchKnowledge, UpdateProfile
│           │   └── mcp_service.py    # MCPClient: connects to external MCP servers for tool discovery
│           ├── memory/
│           │   └── memory_service.py # MemoryService: memorize, retrieve (semantic), summarize, profile, consent
│           ├── analytics_service.py  # AnalyticsService: call logs, HMAC signing, outcome classification
│           ├── campaign_service.py   # CampaignService: CRUD, contacts, start (+ workflow instances)
│           ├── workflow_service.py   # WorkflowService: CRUD, instances, advance, SAP ingest, process-due
│           ├── email_service.py      # EmailService: SMTP or simulated + email_messages audit
│           ├── compliance_service.py # PIIRedactor + ComplianceValidator (regex + LLM audit)
│           ├── hitl_service.py       # HITLService: pending actions, intervention (whisper/takeover)
│           ├── knowledge_service.py  # KnowledgeService: RAG add/query/delete with embeddings
│           ├── marketplace_service.py # MarketplaceService: 7 pre-built agent templates
│           ├── monitoring_service.py # MonitoringService: Redis Pub/Sub broadcast
│           ├── shadow_service.py     # ShadowComparisonService: shadow LLM comparison per turn
│           ├── telephony_service.py  # TelephonyService: Twilio TwiML + outbound calls
│           ├── ultravox_service.py   # UltravoxService: API client for Ultravox voice platform
│           └── voice_ux_service.py   # VoiceUXService: backchannel tokens, latency fillers
├── frontend/                         # Next.js 16 + React 19 + Tailwind v4
│   ├── package.json                  # Next.js 16.1.6, React 19, @xyflow/react, ultravox-client, recharts
│   ├── next.config.ts
│   ├── tsconfig.json                 # Path alias @/* → ./src/*
│   ├── eslint.config.mjs
│   ├── postcss.config.mjs
│   └── src/
│       ├── app/                      # App Router pages
│       │   ├── layout.tsx            # Root layout: Geist fonts, global CSS, AuthProvider
│       │   ├── page.tsx              # Landing page: Navbar, Hero, Features, CTA, Footer
│       │   ├── login/page.tsx        # Email/password login
│       │   ├── register/page.tsx     # Registration form
│       │   └── dashboard/
│       │       ├── layout.tsx        # Auth-guarded layout: Sidebar + header + content
│       │       ├── page.tsx          # Overview: stats cards, trend chart, system health, shadow model
│       │       ├── agents/
│       │       │   ├── page.tsx      # Agent list + create modal
│       │       │   └── [id]/page.tsx # Agent detail (771 lines): Config, Playground (WS chat), Knowledge Base
│       │       ├── campaigns/
│       │       │   ├── page.tsx      # Campaign list with progress cards
│       │       │   ├── new/page.tsx  # Create + optional workflow_id picker
│       │       │   └── [id]/page.tsx # CSV upload, start/pause, stats
│       │       ├── workflows/
│       │       │   ├── page.tsx      # Workflow list
│       │       │   ├── new/page.tsx  # Create from template
│       │       │   └── [id]/page.tsx # Visual · JSON · SAP ingest · Test & runs
│       │       ├── voices/page.tsx   # Voice Lab
│       │       ├── settings/page.tsx # Telephony, Profile, Compliance, Billing, Appearance
│       │       ├── monitoring/ ...
│       │       ├── marketplace/page.tsx
│       │       ├── logs/page.tsx
│       │       ├── approvals/page.tsx
│       │       └── analytics/page.tsx
│       ├── components/
│       │   ├── workflows/WorkflowCanvas.tsx, WorkflowNodeCard.tsx  # @xyflow/react
│       │   ├── ThemeToggle.tsx, Stats.tsx, Testimonials.tsx
│       │   ├── dashboard/Sidebar.tsx # incl. Workflows nav
│       │   └── ui/card.tsx
│       ├── contexts/
│       │   ├── AuthContext.tsx
│       │   └── ThemeContext.tsx      # light | dark | system
│       └── lib/
│           ├── api-url.ts            # /api/v1 rewrite (browser) or direct backend URL
│           ├── api.ts
│           └── workflowFlow.ts
├── docker-compose.yml
├── DOCS.md, WORKFLOW_AUTOMATION.md, ARCHITECTURE.md
├── AGENTS.md, VOICE_PIPELINE.md, features.md, missing_features.md, prd.md
├── README.md
└── LLM_KNOWLEDGE.md
```

---

## 3. ARCHITECTURE LAYERS

### Layer Stack (top → bottom)

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI (main.py)                         │
│            CORS (localhost:3000), /health, /                 │
├─────────────────────────────────────────────────────────────┤
│                 API Router (api.py)                          │
│    14 modules: auth, agents, orchestrator, workflows, ...   │
├─────────────────────────────────────────────────────────────┤
│              API Endpoints (endpoints/)                      │
│    HTTP REST endpoints + 4 WebSocket endpoints              │
├─────────────────────────────────────────────────────────────┤
│                  Service Layer                               │
│  LLM (Groq/OpenAI/Enterprise) │ TTS (Qwen/Deepgram/Mock)    │
│  STT (Deepgram/Mock) │ Memory │ Compliance │ HITL │ Tools   │
│  Analytics │ Campaign │ Shadow │ Telephony │ Ultravox       │
├─────────────────────────────────────────────────────────────┤
│              Orchestration Layer (THE BRAIN)                 │
│  AgentOrchestrator │ SwarmOrchestrator │ LangGraph          │
│  PolicyEngine │ ToolPlanner │ SessionManager (Redis)        │
│  Temporal Workflows (CallWorkflow) │ Worker                 │
├─────────────────────────────────────────────────────────────┤
│              Database Model Layer + SQLAlchemy ORM           │
│  13 models: Agent, User, Org, MemoryItem, CallLog, ...      │
│  PostgreSQL + pgvector for 384-dim embeddings               │
└─────────────────────────────────────────────────────────────┘
```

### Cross-Cutting Concerns
- **Config:** pydantic-settings from `.env`
- **Auth:** JWT (24h access, 7d refresh) + bcrypt + RBAC (admin/manager/agent/viewer)
- **Multi-tenancy:** `organization_id` column on all major entities
- **Async:** asyncio throughout, async WebSocket handlers
- **Durable Workflows:** Temporal.io for call lifecycle
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- **Caching/Session:** Redis (async) for session state, Pub/Sub for monitoring & HITL
- **Logging:** Loguru with standard logging bridge

---

## 4. THE VOICE SESSION LOOP (WebSocket — orchestrator.py)

This is the **core loop**. Every user utterance goes through these stages:

```
1. SENTIMENT TRACKING → moving average update
2. FAST PATH CHECK → simple ack/greeting bypasses LLM (cost saving)
3. HITL CHECK → if takeover mode, read human response from Redis queue
4. POLICY INPUT GUARD → validate intent + guardrails → state transition
5. AGENT SELECTION → swarm routing or standard agent
6. AUTONOMOUS DISCOVERY → if swarm fails, search all agents for capability match
7. RAG KNOWLEDGE RETRIEVAL → semantic search over agent's knowledge base
8. RESPONSE GENERATION → EnterpriseLLM (with latency budget: 2.5s)
9. TOOL PLANNING → ToolPlanner: plan statement + sequential tool calls
10. POLICY OUTPUT GUARD → script enforcement + output guardrails
11. SELF-CORRECTION → reflect_and_correct if confidence is low
12. ESCALATION CHECK → failure conditions, sentiment drop, repetition
13. COMPLIANCE AUDIT → background AuditLog write
14. SHADOW COMPARISON → background ShadowLog (cheaper model comparison)
15. TTS SYNTHESIS → stream audio chunks back via WebSocket
16. SILENCE DETECTION → 30s timeout → nudge
17. POST-CALL → summarization + memory extraction
```

### WebSocket Protocol (agent playground)
```
Client → Server: { type: "transcript", text: "user said this" }
Server → Client: { type: "text_chunk", text: "partial response..." }
Server → Client: { type: "audio_chunk", audio: "base64_encoded_wav" }
Server → Client: { type: "tool_plan", plan: "I'll check your order..." }
Server → Client: { type: "tool_execution", tool: "get_order_status", result: {...} }
Server → Client: { type: "agent_switch", from: "support", to: "sales" }
Server → Client: { type: "end_response" }
```

---

## 5. MODERN VOICE AGENT FEATURES (from AGENTS.md)

The platform implements all 15 tenets from the design philosophy:

| # | Feature | Implementation |
|---|---------|---------------|
| 1 | Goal & Success Model | `Agent.goals`, `success_criteria`, `failure_conditions`, `exit_actions` columns |
| 2 | Tool Planning | `ToolPlanner` class — LLM-based plan generation before execution |
| 3 | Multi-Layer Memory | 4 types: episodic (history), working (context), long-term (MemoryItem/UserProfile), procedural (tools) |
| 4 | Memory Governance | TTLs (`expires_at`), `memory_type` (user_claim/system_verified), `is_sensitive`, consent management |
| 5 | Confidence Awareness | `ConfidenceScores` per pipeline stage, low-confidence handling in orchestrator |
| 6 | Self-Correction | `AgentOrchestrator.reflect_and_correct()` method |
| 7 | Emotional Tracking | Sentiment slope analysis, moving average, escalation on sustained negativity |
| 8 | Turn Control | Barge-in handling, silence detection, response cancellation |
| 9 | Failure Recovery | Repetition detection, escalation triggers, failure conditions per agent |
| 10 | Policy Compliance | `PolicyEngine` + `ComplianceValidator` (shadow audit per turn) |
| 11 | Multi-Agent | `SwarmOrchestrator` (LLM routing), `LangGraphOrchestrator` (StateGraph with specialist nodes) |
| 12 | Time Awareness | Latency budget (2.5s), silence timeout (30s), call duration tracking |
| 13 | Cost Awareness | `token_limit` per agent, `fallback_model`, `EnterpriseLLM` health-aware failover |
| 14 | Explainability | Decision trace events, tool call logs, compliance audit trail |
| 15 | End-of-Call Intelligence | Outcome classification, call summarization, memory extraction, HMAC-signed transcripts |

---

## 6. DATABASE MODELS (13 Entities)

### Agent System
- **Agent** — `id, name, role, persona, organization_id, language, tools (JSON), goals, success_criteria, failure_conditions, exit_actions, config, token_limit, fallback_model, is_active, active_version_id, created_at, updated_at`
- **AgentVersion** — `id, agent_id, version_number, persona, tools, policy, success_criteria, failure_conditions, exit_actions, token_limit, fallback_model, created_by, change_log, weight (A/B), is_canary`
- **Workflow** — `id, name, description, category, definition (JSON v1), version, status (draft|active|archived), is_template, template_slug, organization_id, created_by`
- **WorkflowInstance** — `id, workflow_id, status (running|waiting|completed|failed), current_node_id, context (JSON), wait_until, campaign_id, contact_id, agent_id, outcome, error_message`
- **EmailMessage** — `id, workflow_instance_id, to_address, template, subject, status (sent|simulated|failed), sent_at`

### User & Tenant
- **User** — `id, email, hashed_password, full_name, role (admin|manager|agent|viewer), is_active, is_superuser`
- **Organization** — `id, name, domain, subscription_plan, is_active, settings (JSON)`

### Memory System
- **MemoryItem** — `id, user_id, agent_id, organization_id, category, memory_type (user_claim|system_verified|regulated_fact), key, value, source_session_id, confidence, expires_at, is_sensitive, embedding (Vector 384)`
- **ConversationSummary** — `id, session_id, user_id, agent_id, organization_id, summary, key_points (JSON), action_items (JSON), sentiment, turn_count, duration_seconds, outcome, embedding (Vector 384)`
- **UserProfile** — `id, user_id, organization_id, name, preferred_language, total_calls, avg_sentiment, preferences (JSON), consent_status, requires_escalation`

### Knowledge
- **AgentKnowledge** — `id, agent_id, organization_id, title, content, data_metadata (JSON), embedding (Vector 384)`

### Compliance
- **AuditLog** — `id, session_id, organization_id, turn_index, user_message (redacted), ai_response (redacted), is_compliant, violations (JSON), risk_score, agent_id, state_name`
- **RegulatoryPolicy** — `id, name, organization_id, description, rules (JSON)`

### Campaigns
- **Campaign** — `id, name, organization_id, agent_id, workflow_id, status (draft|scheduled|running|paused|completed|cancelled), start_time, concurrency_limit, retry_config, stats`
- **CampaignContact** — `id, campaign_id, phone_number, contact_name, custom_data (JSON), status, attempts, session_id, error_message`

### Analytics & Ops
- **CallLog** — `id, session_id, agent_id, organization_id, caller_id, campaign_id, start_time, end_time, duration_seconds, avg_latency_ms, total_turns, total_tokens, estimated_cost, status, end_reason, outcome, outcome_reason, transcript (JSON), signature (HMAC)`
- **ShadowLog** — `id, session_id, organization_id, turn_index, primary_model, shadow_model, primary_response, shadow_response, similarity_score, intent_match, latencies`

### HITL
- **PendingAction** — `id, session_id, agent_id, organization_id, action_type, description, payload (JSON), status (pending|approved|rejected|expired), processed_by`
- **SessionIntervention** — `id, session_id, user_id, organization_id, mode (ai_only|whisper|takeover|monitoring), is_active`

---

## 7. API SURFACE

### REST Endpoints (`/api/v1/`)

| Module | Routes |
|--------|--------|
| **auth** | POST register, POST login, POST refresh, GET/PUT /me, POST change-password, admin CRUD for users |
| **agents** | CRUD + POST versions + POST pin |
| **orchestrator** | POST /chat (REST), GET /voices (proxy) |
| **memory** | POST /memorize, POST /retrieve, GET /user/{id}, GET /context/{id}, DELETE /user/{id} (GDPR) |
| **knowledge** | POST/GET /{agent_id}, GET /{agent_id}/query, DELETE /{id} |
| **telephony** | POST /voice (Twilio webhook), POST /voice/{agent_id}, POST /outbound |
| **voices** | GET /, POST /design, POST /register, DELETE /{id} |
| **monitoring** | GET /active-sessions, GET /session/{id} |
| **campaigns** | CRUD + contacts + upload-csv + start (starts workflow instances if workflow_id set) |
| **workflows** | Templates, CRUD, publish, instances, advance, GET /active, POST /process-due, POST /ingest/sap-csv |
| **analytics** | GET /overview, GET /daily-trends, GET /agent-performance, GET /shadow-stats, GET /, GET /recent-calls |
| **hitl** | GET /pending, POST /{id}/decide, POST /sessions/{id}/takeover, POST /sessions/{id}/release, POST /sessions/{id}/respond |
| **marketplace** | GET /templates, POST /install/{id} |

### WebSocket Endpoints
| Endpoint | Purpose |
|----------|---------|
| `ws://.../api/v1/orchestrator/ws/{agent_id}?voice={voice}` | Main voice session (agent playground) |
| `ws://.../api/v1/telephony/ultravox-data` | Ultravox data connection for Twilio calls |
| `ws://.../api/v1/telephony/stream/{agent_id}` | Legacy Twilio media stream fallback |
| `ws://.../api/v1/monitoring/stream/all` | Global monitoring stream (all sessions) |
| `ws://.../api/v1/monitoring/stream/{session_id}` | Per-session monitoring stream |

---

## 8. CONFIGURATION (backend/.env)

```env
# Core
SECRET_KEY=your-secret-key

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5435
POSTGRES_DB=voise

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Temporal (call lifecycle workflows — separate from in-app WorkflowEngine)
TEMPORAL_HOST=localhost:7233

# Workflow email (optional — simulated if unset)
# SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_USE_TLS

# Voice runtime
VOICE_RUNTIME=ultravox
USE_ULTRAVOX_RUNTIME=true
ULTRAVOX_API_KEY=...

# API Keys (all optional)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
DEEPGRAM_API_KEY=...
ULTRAVOX_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...

# Host
SERVER_HOST=localhost:8001
```

---

## 9. KEY DESIGN DECISIONS

1. **Dual Runtime:** Self-hosted WebSocket pipeline OR Ultravox proxy mode. Backend can work as control-plane with Ultravox handling real-time voice.

2. **Shadow Model Pattern:** Every turn's LLM response is compared against a cheaper shadow model (Llama-3.1-8b) in the background. Results logged to `ShadowLog` for quality/cost analysis.

3. **Compliance as a Silent Agent:** `ComplianceValidator` audits every turn using regex + LLM checks. Writes to `AuditLog` with risk scores. This is the "one speaking agent, many silent agents" concept.

4. **Memory Governance:** 4 memory types (`user_claim`, `system_verified`, `regulated_fact`, `assumption`). TTLs, PII-aware storage (redacted at write time), consent-gated writes, and "do not remember" detection.

5. **Multi-Tenancy:** `organization_id` on all major entities. Isolation at the query level.

6. **A/B Testing:** `AgentVersion.weight` + `is_canary` for gradual, canary-based agent deployments.

7. **Cost Awareness:** Token budgets per agent, automatic fallback to cheaper model on overage, health-aware provider selection.

8. **Time Awareness:** Silence detection (30s → nudge), latency budget (2.5s), call duration tracking.

---

## 10. FRONTEND KEY FACTS

- **Framework:** Next.js 16 App Router, React 19, TypeScript
- **Styling:** Tailwind CSS v4, light + dark themes (`ThemeContext`, CSS variables in `globals.css`)
- **API base:** `getApiBaseUrl()` — browser uses `/api/v1` (Next.js rewrite → backend :8001)
- **State:** Single AuthContext; all other state is local `useState`/`useEffect` per page
- **Data Fetching:** Direct fetch calls in `useEffect` + polling intervals; no React Query/SWR
- **Charts:** recharts (AreaChart, BarChart)
- **Animations:** framer-motion (landing page), CSS animations
- **Real-time:** WebSocket for playground/monitoring; **ultravox-client** for Ultravox WebRTC playground calls
- **Workflow UI:** `@xyflow/react` visual graph editor synced with JSON definition
- **No component library** — custom UI components

---

## 11. SERVICE PROVIDER PATTERN

All external AI services use an abstract base class with multiple implementations:

```python
class LLMProvider:    # generate_response(), generate_stream()
  ├── GroqLLM         # llama-3.3-70b-versatile (primary), llama-3.1-8b-instant (fallback)
  ├── OpenAILLM       # gpt-3.5-turbo
  └── EnterpriseLLM   # Primary + fallback with health-aware switching

class TTSProvider:     # synthesize(), synthesize_stream()
  ├── QwenTTS         # Local server (port 8008), voice design/cloning
  ├── DeepgramTTS     # aura-asteria-en, multilingual models
  └── MockTTS         # Testing

class STTProvider:     # transcribe()
  ├── DeepgramSTT     # nova-2, streaming
  └── MockSTT         # Testing
```

Tool system uses `BaseTool.execute()` interface with 8 built-in tools + MCP client for external tool servers.

---

## 12. INFRASTRUCTURE (docker-compose.yml)

```yaml
services:
  postgres: pgvector/pgvector:pg15 on 5435
  redis: redis:7 on 6379
  temporal: temporalio/auto-setup with Postgres backend on 7233 (gRPC) + 8233 (UI)
```

Backend runs locally (commented out in compose). Expected on port 8001.

---

## 13. MIGRATION HISTORY (24+ alembic migrations, chronological)

1. Initial schema (agents, legacy workflows table)
2. Memory tables with pgvector
3. Users table
4. Campaigns
5. Call logs
6. HITL pending actions
7. Shadow logs, agent versions, session interventions, memory_type
8. Compliance (audit_logs, regulatory_policies)
9. Goals/success criteria/failure conditions on agents
10. CallLog outcome + outcome_reason
11. Memory governance (expires_at, is_sensitive, consent_status)
12. Cost awareness (token_limit, fallback_model)
13. Multi-tenancy (organization_id across all entities)
14. A/B testing (weight, is_canary on agent_versions)
15. Empty migration
16. HMAC signature on call_logs
17-19. More organization_id additions + config JSON column + agent_knowledge table
20. Agent description column
21. Campaign call_config
22. **a1b2c3d4e5f6** — workflow automation: workflow_instances, workflow metadata columns
23. **b2c3d4e5f6a7** — email_messages for workflow email steps

---

## 13b. IN-APP WORKFLOW AUTOMATION (Phase 1 & 2 — Done)

**Not** Temporal `CallWorkflow` — this is a separate JSON-graph engine in `app/workflows/`.

| Piece | Role |
|-------|------|
| `WorkflowDefinitionV1` | Nodes: start, condition, voice_call, wait, email, hitl_approval, escalate, end |
| `WorkflowEngine` | Executes until wait/completed; voice_call uses `CampaignService.dial_contact` |
| `WorkflowService` | CRUD, `create_instance`, `advance_instance`, `process_due_instances`, `ingest_sap_rows` |
| Templates | `collections-payment-reminder`, `lead-qualification`, `appointment-confirmation` |
| Campaign link | `campaign.workflow_id` → `start_campaign()` spawns instance per pending contact |

Full reference: [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md).

---

## 14. ENTRY POINTS

### To start backend:
```bash
cd backend
pip install -r requirements.txt
# Ensure .env is configured
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### To start frontend:
```bash
cd frontend
npm install
npm run dev  # defaults to port 3000
```

### To start infrastructure:
```bash
docker-compose up postgres redis temporal
```

### DB migrations:
```bash
cd backend
alembic upgrade head
```
