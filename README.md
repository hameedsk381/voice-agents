# Voise AI

**Voise AI** is an enterprise voice automation platform: deploy AI agents for outbound campaigns, collections follow-up, lead qualification, and appointment confirmation — with **workflow automation**, human-in-the-loop approvals, and live monitoring.

## Capabilities

| Area | What you get |
|------|----------------|
| **Voice** | Ultravox runtime (default) + Twilio telephony; agent playground & live calls |
| **Agents** | Goals, success criteria, tools, knowledge base (RAG), Ultravox sync |
| **Campaigns** | CSV contacts, start/pause, optional **workflow per contact** |
| **Workflows** | Visual + JSON builder, templates (collections, sales, healthcare), SAP CSV ingest, email steps |
| **Operations** | Live monitoring, call logs, analytics, HITL approvals, marketplace templates |
| **Platform** | JWT auth, multi-tenancy, compliance audit, memory governance, shadow model comparison |

**Workflow docs:** [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md) · **All docs:** [DOCS.md](./DOCS.md)

---

## Project structure

| Path | Stack |
|------|--------|
| `frontend/` | Next.js 16, React 19, Tailwind v4, `@xyflow/react` workflow canvas |
| `backend/` | FastAPI, SQLAlchemy, Alembic, Temporal (call workflows), Redis |
| `docker-compose.yml` | PostgreSQL (pgvector), Redis, Temporal |

---

## Quick start

### 1. Environment

```bash
cp backend/.env.example backend/.env
# Required for voice: ULTRAVOX_API_KEY
# Optional: GROQ_API_KEY, TWILIO_*, SMTP_* (workflow email)
```

### 2. Infrastructure

```bash
docker compose up -d postgres redis temporal
cd backend && alembic upgrade head
```

Postgres listens on **5435** (host) per `docker-compose.yml`.

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/v1/*` → `http://localhost:8001` (see `frontend/next.config.ts`), avoiding CORS in local dev.

Open [http://localhost:3000](http://localhost:3000).

### 5. Demo data (optional)

```bash
cd backend
python -m scripts.seed_demo_data
```

| Field | Value |
|-------|--------|
| Email | `demo@voise.ai` |
| Password | `DemoVoise2026!` |

---

## Configuration (essentials)

| Variable | Purpose |
|----------|---------|
| `VOICE_RUNTIME=ultravox` | Default voice stack (Ultravox STT/LLM/TTS) |
| `ULTRAVOX_API_KEY` | Required for voice calls & playground |
| `USE_ULTRAVOX_RUNTIME=true` | Enable Ultravox path in orchestrator |
| `GROQ_API_KEY` | LLM helpers (analytics, compliance, tools) |
| `TWILIO_*` | Outbound/inbound telephony |
| `SMTP_HOST`, `SMTP_FROM`, … | Real email from workflow nodes (else simulated) |
| `TEMPORAL_HOST` | Durable **call** workflows (separate from in-app workflow engine) |
| `POSTGRES_PORT=5435` | Match docker-compose external port |

Full list: `backend/.env.example`.

---

## Workflow automation (shipped)

1. **Dashboard → Workflows** — create from template or blank, edit in **Visual** or **JSON**, **Publish**.
2. **SAP ingest** tab — upload AR CSV → contacts + instances (published workflow required).
3. **Campaigns → New** — attach a published workflow; **Start** runs one instance per pending contact.
4. **Cron** — `POST /api/v1/workflows/process-due` resumes `wait` nodes.

Details: [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md).

**Phase 3:** Ultravox `call.ended` auto-advances workflow instances; Temporal worker runs due-instance scheduler; visual node config panel; campaign page shows per-contact workflow status.

```bash
# Optional: Temporal worker (call workflows + workflow due scheduler)
cd backend && python -m app.orchestration.worker
```

---

## Development

```bash
# Backend tests (workflow)
cd backend && pytest tests/test_workflow_engine.py tests/test_sap_ingest.py -v

# Frontend production build
cd frontend && npm run build
```

---

## Documentation

See **[DOCS.md](./DOCS.md)** for the full index (architecture, PRD, features, voice pipeline, LLM knowledge doc).

---

## License

Proprietary. Not open source.
