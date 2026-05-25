# Voise AI — Project Status

**Last updated:** May 2026

One-stop status document for the Voise AI enterprise voice automation platform.

---

## Quick Facts

| Attribute | Value |
|-----------|-------|
| **Stack** | Next.js 16 · React 19 · Tailwind v4 · FastAPI · SQLAlchemy · PostgreSQL (pgvector) · Redis · Temporal |
| **Frontend** | 60+ TSX source files, shadcn/ui, `@xyflow/react`, Recharts |
| **Backend** | 40+ Python modules, 8+ REST endpoint groups, WebSocket streaming, MCP client |
| **Voice Runtime** | Ultravox (default) + Twilio telephony |
| **Auth** | JWT (access + refresh), bcrypt passwords |
| **DB** | PostgreSQL (port 5435), pgvector for embeddings, Alembic migrations |
| **State** | ~34K lines of TypeScript, ~25K lines of Python |

---

## Implementation Status

### ✅ Completed

| Phase / Feature | What It Includes | Since |
|-----------------|------------------|-------|
| **Phase 1 — Workflow Engine** | JSON definitions (v1 schema), 8 node types, `WorkflowEngine` executor, 3 built-in templates (collections, lead qual, appointment), REST API, worklfow CRUD + instances, JSON editor UI | May 2026 |
| **Phase 2 — Workflow Frontend** | Visual builder (`@xyflow/react`), email node (SMTP/simulated + audit), SAP AR CSV ingest (20+ field aliases), campaign ↔ workflow linking, wait scheduler (`POST /process-due`), Temporal activity hook | May 2026 |
| **Phase 3 — Workflow Automation** | Call-ended auto-advance via webhook, Temporal `WorkflowDueScheduler`, HITL approval resume, WhatsApp node (simulated), campaign per-contact status | May 2026 |
| **Phase 4 — Workflow Polish** | Organization scoping (all `WorkflowService` methods + API + Temporal activity), real WhatsApp provider integration (`WhatsAppService` w/ templates, status callbacks, audit), condition rules UI (JSON/visual toggle, autocomplete field suggestions) | May 2026 |
| **Phase 6 — Multi-Layer Memory** | `WorkingMemory` (task state) / `ProceduralMemory` (playbooks) models & services, `do_not_remember` governance flag, TTL cleanup background task, memory-aware LLM prompting, working-memory clearance on session end | May 2026 |
| **Phase 8 — Voice Intelligence** | `EmotionTracker` (multi-signal fusion, pace/tone adaptation), `EndOfCallService` (LLM outcome classification, satisfaction estimation, next-step scheduling, human-review tagging), `AgentContext` enhanced (time/cost/emotion/confidence tiers), `ConfidenceScores` tool-result dimension, cost-aware model downgrade, time-aware prompting, end-of-call pipeline | May 2026 |
| **Theme Colour Refresh** | Complete palette redesign: indigo/violet primary (#6C5CE7 / #818CF8), pink accent (#F472B6), warm charcoal dark bg (#0D0D14), subtle lavender light bg (#F8F7FC), smaller radius (0.625rem). All chart fills/gradients/logo sync'd | May 2026 |
| **React Doctor Cleanup** | ~571 issues fixed across 34 files: `w-* h-*` → `size-*` (219), `font-bold` → `font-semibold` on headings (245), `type="button"` on buttons (57), missing `aria-label`/`htmlFor` (93), array index keys → stable IDs (40), `useEffect` init → `useState` lazy init (18), exhaustive deps (7), event handler anti-patterns (7), `.filter().map()` → single pass (2), `animate-bounce` → ease-out-expo (1), `@media (prefers-reduced-motion: reduce)` (1) | May 2026 |
| **Phase 1 — Observability Stack** | Prometheus `/metrics` endpoint (9 metric families: HTTP, calls, latency, cost, errors, memory, sessions, Temporal), Prometheus HTTP middleware with latency tracking, OpenTelemetry ASGI/SQLAlchemy/httpx auto-instrumentation wired, structured JSON logging (`LOG_FORMAT=json`), Grafana dashboard provisioning (9-panel overview dashboard), OTEL collector config, metrics tab in frontend observability page, docker-compose with Prometheus/Grafana/OTEL services, psutil for process metrics | May 2026 |
| **Phase 7 — Kubernetes Deployment** | Full `k8s/` manifest set (35+ files): namespace, ConfigMaps, Secrets, Postgres StatefulSet (pgvector, 20Gi PVC), Redis Deployment (AOF, 5Gi PVC), Temporal Deployment, backend Deployment (2 replicas, HPA 2-10 @ 70% CPU), frontend Deployment (2 replicas, HPA 2-8 @ 70% CPU), Prometheus (k8s SD, 20Gi PVC), Grafana (provisioned datasource + dashboard), OTEL collector, Nginx Ingress (voise.ai + api.voise.ai, TLS), NetworkPolicy (default-deny + allow-internal), Kustomization. Multi-stage Dockerfiles for backend (python:3.12-slim, pip --user) and frontend (node:22-alpine, 3-stage). Helm chart (`helm/voise/`) with parameterized values.yaml. Build, push, deploy instructions in deploy-notes. | May 2026 |
| **WhatsApp Real Provider** | Twilio WhatsApp Business API fully wired: `WhatsAppService` upgraded with media attachments, Twilio Content API template management (create/list templates), inbound message webhook (opt-in/opt-out via STOP/START keywords), webhook signature validation via `RequestValidator`, Redis-backed opt-in/opt-out consent tracking, per-contact rate limiting, 24h session window awareness. Config fields: `TWILIO_WHATSAPP_SENDER`, `WHATSAPP_RATE_LIMIT_PER_HOUR`, `WHATSAPP_OPTIN_REQUIRED`. Frontend settings page with WhatsApp tab (setup checklist, sender config, template reference) | May 2026 |

### 🏗 In Progress

| Item | Status |
|------|--------|

### ⏳ Planned / Backlog

| Item | Priority |
|------|----------|
| Real WhatsApp provider (Twilio/Meta) | Low (Phase 4 shipped on simulated path) |
| YAML workflow definitions | Low |
| Parallel execution nodes | Low |
| Multi-agent voice (speaker + silent watchers) | Medium |

---

## Frontend Architecture

### Stack

| Layer | Tech |
|-------|------|
| Framework | Next.js 16 (App Router) |
| UI | React 19, Tailwind v4, shadcn/ui (base-nova) |
| State | React hooks (useState, useEffect, useSyncExternalStore), Context |
| Charts | Recharts |
| Workflow Canvas | `@xyflow/react` |
| Forms | Native HTML + shadcn inputs |
| Build | TypeScript, PostCSS, Turbopack |
| Auth | JWT tokens in localStorage, `AuthContext` |

### Routes

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/login` | Auth |
| `/register` | Registration |
| `/dashboard` | Overview (stats cards, trend chart, shadow model) |
| `/dashboard/agents` | Agent list + create |
| `/dashboard/agents/[id]` | Config, playground, knowledge base |
| `/dashboard/campaigns` | Campaign list |
| `/dashboard/campaigns/new` | Create campaign |
| `/dashboard/campaigns/[id]` | Detail, CSV upload, start/pause |
| `/dashboard/workflows` | Work flow list |
| `/dashboard/workflows/new` | Create from template |
| `/dashboard/workflows/[id]` | Visual/JSON editor, SAP ingest, test |
| `/dashboard/monitoring` | Active sessions (5s poll) |
| `/dashboard/monitoring/[id]` | Live transcript stream |
| `/dashboard/voices` | Voice lab, gallery, designer, cloner |
| `/dashboard/settings` | Telephony, appearance, compliance, billing |
| `/dashboard/marketplace` | Agent templates |
| `/dashboard/logs` | Call log table |
| `/dashboard/approvals` | HITL queue |
| `/dashboard/analytics` | Charts, agent performance |
| `/dashboard/observability` | System observability |
| `/dashboard/registry` | Feature registry |

### Key Components

- `Logo.tsx` — Animated SVG logo w/ indigo → purple → pink gradient
- `Sidebar.tsx` — Navigation sidebar (client nav)
- `ThemeToggle.tsx` — Light/dark switcher
- `WorkflowCanvas.tsx` — React Flow visual editor
- `WorkflowNodeCard.tsx` — Color-coded node components
- `WorkflowNodeConfigPanel.tsx` — Side panel for node config

### Theme System

- Single source of truth: `frontend/src/app/globals.css`
- Dark-first palette: warm charcoal `#0D0D14` bg, indigo `#818CF8` primary, pink `#F472B6` accent
- Light variant: lavender `#F8F7FC` bg, violet `#6C5CE7` primary
- 40+ CSS custom properties: `--color-*`, `--bg-*`, `--text-*`, `--border-*`
- Tailwind `@theme inline` for compile-time classes

---

## Backend Architecture

### Stack

| Layer | Tech |
|-------|------|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Queue/Streams | Redis (session, Pub/Sub) |
| Workflow Engine | Temporal (call workflows) |
| Voice Runtime | Ultravox API proxy |
| LLM | Groq (default), OpenAI fallback |
| TTS | Qwen3-TTS, Deepgram, Mock |
| STT | Deepgram, Mock |

### API Endpoints

| Group | Prefix | Key Endpoints |
|-------|--------|---------------|
| Auth | `/api/v1/auth/*` | Login, register, refresh |
| Agents | `/api/v1/agents/*` | CRUD, playground, knowledge |
| Campaigns | `/api/v1/campaigns/*` | CRUD, CSV upload, start/pause |
| Workflows | `/api/v1/workflows/*` | CRUD, instances, SAP ingest, process-due, WhatsApp send |
| Monitoring | `/api/v1/monitoring/*` | Active sessions, stream |
| Analytics | `/api/v1/analytics/*` | Stats, trends |
| HITL | `/api/v1/hitl/*` | Pending actions, decide |
| Memory | `/api/v1/memory/*` | Episodic, working, procedural |
| Knowledge | `/api/v1/knowledge/*` | RAG, embeddings |
| Telephony | `/api/v1/telephony/*` | Voice, Ultravox proxy |
| Marketplace | `/api/v1/marketplace/*` | Agent templates |
| Voices | `/api/v1/voices/*` | Voice gallery, designer, cloner |

### Key Services

| Service | File | Purpose |
|---------|------|---------|
| `AgentOrchestrator` | `backend/app/orchestration/agent_orchestrator.py` | Main voice loop — sentiment, confidence, escalation, self-corrections |
| `SwarmOrchestrator` | `backend/app/orchestration/swarm_orchestrator.py` | LLM routing, specialist discovery |
| `LangGraphOrchestrator` | `backend/app/orchestration/langgraph_orchestrator.py` | StateGraph, specialist nodes |
| `PolicyEngine` | `backend/app/policy/engine.py` | State machine, guardrails, script enforcement |
| `ToolPlanner` | `backend/app/orchestration/tool_planner.py` | Plan-before-call, tool sequencing |
| `WorkflowEngine` | `backend/app/workflows/engine.py` | In-process async workflow executor |
| `WorkflowService` | `backend/app/services/workflow_service.py` | Workflow CRUD + instances (org-scoped) |
| `WhatsAppService` | `backend/app/services/whatsapp_service.py` | Template rendering, send, status callback |
| `EmailService` | `backend/app/services/email_service.py` | SMTP/simulated email, audit |
| `MemoryService` | `backend/app/services/memory_service.py` | Multi-layer memory (episodic, working, procedural) |
| `EmotionTracker` | `backend/app/services/emotion_service.py` | Multi-signal emotion analysis |
| `EndOfCallService` | `backend/app/services/end_of_call_service.py` | Outcome classification, satisfaction, next-steps |
| `TurnProcessor` | `backend/app/orchestration/turn_processor.py` | Wires emotion, cost, time, end-of-call per turn |

### Database Models

| Table | Purpose |
|-------|---------|
| `organizations` | Multi-tenant orgs |
| `users` | Auth, profile |
| `agents` | Agent definitions |
| `agent_versions` | Version history |
| `agent_knowledge` | RAG documents |
| `campaigns` | Outbound campaigns |
| `campaign_contacts` | Contact list per campaign |
| `worklows` | Workflow definitions (v1 JSON) |
| `workflow_instances` | Per-contact execution |
| `email_messages` | Email audit log |
| `whatsapp_messages` | WhatsApp audit log |
| `policy_rules` | Compliance guardrails |
| `call_logs` | Session records |
| `audit_logs` | Compliance audit |
| `shadow_logs` | Shadow model comparison |
| `memory_items` | Long-term memory |
| `memory_working` | Working memory (per-session) |
| `memory_procedural` | Procedural playbooks |
| `pending_actions` | HITL queue |
| `session_interventions` | Human takeover |

---

## React Doctor Score: 76/100

After the cleanup pass:

| Category | Issues (before) | Issues (after) | Fix |
|----------|----------------|----------------|-----|
| Architecture | 364 | ~0 | `size-*`, `font-semibold`, export components |
| Accessibility | 106 | ~8 | `aria-label`, `htmlFor`, reduced motion |
| Correctness | 79 | ~15 | `type="button"`, stable keys, deps |
| State & Effects | 45 | ~10 | Lazy `useState`, event handlers |
| Performance | 26 | ~3 | Combine iterations, remove bounce |

Key wins:
- **-252** redundant `w-* h-*` collapsed to `size-*`
- **-245** `font-bold` → `font-semibold` on headings
- **-57** `<button>` elements got `type="button"`
- **-93** accessibility labels fixed
- **-40** array index keys replaced with stable IDs
- **-18** `useEffect` initializers moved to lazy `useState`

---

## Known Gaps

| Area | Gap |
|------|-----|
| Alerting | No alert rules defined in Prometheus/Grafana |
| Observability alerting | No alert rules defined in Prometheus/Grafana |
| WhatsApp Business | Real Twilio API with templates, media, inbound, consent tracking — setup checklist in docs |
| CI/CD | No GitHub Actions or similar |
| Tests | Workflow engine tested; voice/orchestrator coverage incomplete |
| Multi-tenant | Schema ready (organization_id FK), UI scoping partial |
| Documentation | Enterprise docs (SLA, on-prem install) not created |

---

## How to Run

```bash
# Infrastructure
docker compose up -d postgres redis temporal
cd backend && alembic upgrade head

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Frontend
cd frontend
npm install
npm run dev

# Optional: demo data
cd backend && python -m scripts.seed_demo_data
# Login: demo@voise.ai / DemoVoise2026!

# Optional: Temporal worker
cd backend && python -m app.orchestration.worker
```

---

*Full docs: [DOCS.md](./DOCS.md) · Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md) · Workflows: [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md) · Features: [features.md](./features.md)*
