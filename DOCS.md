# Voise AI — Documentation Index

Central index for project documentation. **Last updated:** May 2026

---

## Start here

| Document | Audience | Contents |
|----------|----------|----------|
| [README.md](./README.md) | Everyone | Quick start, stack, configuration, demo login |
| [PROJECT_STATUS.md](./PROJECT_STATUS.md) | Everyone | **One-stop status** — all phases, frontend/backend architecture, known gaps |
| [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md) | Engineers / PM | Workflow engine Phases 1–4 (✅ done), API, SAP ingest, operations |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Engineers | Mermaid system diagrams (layers, ER, frontend routes, data flows) |
| [LLM_KNOWLEDGE.md](./LLM_KNOWLEDGE.md) | LLMs / onboarding | Full repo map, API surface, models, config, conventions |

---

## Product & planning

| Document | Contents |
|----------|----------|
| [prd.md](./prd.md) | Product requirements, MVP scope, roadmap |
| [features.md](./features.md) | Full feature catalog + **implementation status** |
| [missing_features.md](./missing_features.md) | Enterprise gap analysis vs BlueMachine-class platforms |
| [AGENTS.md](./AGENTS.md) | Voice agent design philosophy (15 modern agent tenets) |

---

## Technical deep dives

| Document | Contents |
|----------|----------|
| [VOICE_PIPELINE.md](./VOICE_PIPELINE.md) | Real-time voice session loop (Ultravox default, policy, HITL, compliance) |
| [ELEVENLABS_GAP_ANALYSIS.md](./ELEVENLABS_GAP_ANALYSIS.md) | Qwen vs ElevenLabs TTS comparison |
| [AGENTS.md](./AGENTS.md) | Voice agent architecture & modern agent design principles |

---

## Implementation status (summary)

| Area | Status |
|------|--------|
| Voice runtime (Ultravox + Twilio) | ✅ Production path |
| Agent orchestration (policy, tools, memory, HITL, emotion, end-of-call) | ✅ Core shipped |
| Campaigns + outbound dialing | ✅ Shipped |
| **Workflow automation Phase 1** (JSON, engine, templates, instances) | ✅ **Done** |
| **Workflow automation Phase 2** (visual builder, email, SAP ingest, campaign link) | ✅ **Done** |
| **Workflow automation Phase 3** (call-ended advance, Temporal scheduler, config panel, campaign UI, WhatsApp) | ✅ **Done** |
| **Workflow automation Phase 4** (org scoping, WhatsApp provider, condition rules UI) | ✅ **Done** |
| **Multi-layer memory Phase 6** (working memory, procedural memory, governance, TTL) | ✅ **Done** |
| **Voice intelligence Phase 8** (emotion tracking, end-of-call service, cost/time awareness, confidence tiers) | ✅ **Done** |
| **Observability Stack Phase 1** (Prometheus metrics, Grafana, OTEL auto-instrumentation, structured logging, metrics dashboard) | ✅ **Done** |
| **Kubernetes Deployment Phase 7** (35+ k8s manifests, Helm chart, multi-stage Dockerfiles, HPA, Ingress, NetworkPolicy) | ✅ **Done** |
| **WhatsApp Real Provider** (Twilio WhatsApp Business API, template management, inbound webhook, consent tracking, media support) | ✅ **Done** |
| Theme colour refresh | ✅ Done (indigo/violet palette, pink accent) |
| React Doctor cleanup (571+ fixes, 34 files, score 76/100) | ✅ Done |
| Demo seed data | ✅ `backend/scripts/seed_demo_data.py` |

---

## Related paths (not markdown)

- `backend/.env.example` — all environment variables (Ultravox, SMTP, Temporal, etc.)
- `backend/scripts/seed_demo_data.py` — demo user, agents, sample data
- `docker-compose.yml` — Postgres (5435), Redis, Temporal, optional backend image
