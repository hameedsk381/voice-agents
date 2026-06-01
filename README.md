# Voise AI

**Proprietary voice agent platform** — build, deploy, and monitor multilingual voice AI agents with drag-and-drop workflows, multi-provider STT/TTS/LLM, telephony integration, and enterprise-grade compliance.

A self-hosted alternative to Vapi, Retell, and Dograh.

---

## Features

| Area | What you get |
|------|-------------|
| **Voice pipeline** | Google Cloud, Groq, Deepgram, Sarvam AI, Qwen — pick any STT/TTS/LLM combo per agent |
| **Multilingual** | Hindi, Tamil, Telugu, English, and more via Sarvam AI + Google Cloud |
| **Workflow builder** | Visual drag-and-drop canvas (React Flow) + JSON editor + AI generation from text |
| **Telephony** | Twilio inbound/outbound with Media Streams |
| **Campaigns** | CSV upload, bulk outbound dialing, pause/resume, retry logic, per-contact workflow |
| **RAG** | Knowledge base with pgvector embeddings, semantic search injected into live calls |
| **Tools** | HTTP API, call transfer, MCP, Aadhaar/PAN/UPI/GST lookups, and more |
| **Agent memory** | 4-layer: episodic, working, long-term (pgvector), procedural, with TTLs and consent |
| **Compliance** | Per-turn policy engine (permit/deny/escalate), Ed25519 audit chain, PII detection |
| **Human-in-the-loop** | Supervisor takeover, whisper mode, approval queues, live monitoring WebSocket |
| **Multi-agent** | Swarm orchestration with autonomous capability discovery and routing |
| **Observability** | OpenTelemetry, Prometheus metrics, per-span tracing, post-call QA |
| **Analytics** | Call logs, outcome classification, satisfaction estimation, shadow model comparison |
| **Billing** | Subscription management, usage metering, rate cards, cost estimation |
| **WhatsApp** | Twilio WhatsApp Business API with templates and delivery status |

---

## Quick start

### Prerequisites

- Docker & Docker Compose
- API keys for your chosen providers (see Configuration)
- Access to the private repository

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd voice-agents
cp backend/.env.example .env
# Edit .env with your API keys
```

Minimal `.env` for a Google Cloud pipeline:

```env
VOICE_RUNTIME=livekit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=./gcp-key.json
```

### 2. Start the platform

```bash
docker compose up -d
```

This starts: PostgreSQL (pgvector), Redis, Prometheus, Grafana, OpenTelemetry collector, the API backend, and the LiveKit agent.

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Open the dashboard

[http://localhost:3000](http://localhost:3000)

### 5. Seed demo data (optional)

```bash
docker compose exec backend python -m scripts.seed_demo_data
```

| Field | Value |
|-------|-------|
| Email | `demo@voise.ai` |
| Password | `DemoVoise2026!` |

---

## Architecture

```
┌───────────────────────────────────────────────────┐
│                   Frontend (Next.js)               │
│   Dashboard · Workflow Canvas · Campaigns · QA     │
└──────────┬────────────────────────────────────────┘
           │ HTTP / WebSocket
┌──────────▼────────────────────────────────────────┐
│               Backend API (FastAPI)                │
│   Agents · Workflows · Campaigns · Telephony ·     │
│   Memory · Knowledge · Tools · Billing · QA       │
└──────┬──────────┬──────────┬──────────────────────┘
       │          │          │
       ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌──────────┐
│LiveKit   │ │Temporal│ │PostgreSQL│
│Agent     │ │Workflow│ │+ pgvector│
│(WebRTC)  │ │Engine  │ │+ Redis   │
└──────────┘ └────────┘ └──────────┘
       │
       ▼
┌──────────────────────────────────────┐
│   STT · LLM · TTS Providers          │
│   Google · Groq · Deepgram · Sarvam  │
│   Qwen · OpenAI (extensible)         │
└──────────────────────────────────────┘
```

---

## Configuration

### Voice runtimes

| Runtime | Description |
|---------|-------------|
| `livekit` | Production WebRTC pipeline via LiveKit Agents (recommended) |
| `custom` | Legacy WebSocket-based turn processor |

### STT / LLM / TTS providers

Set via `LIVEKIT_STT_MODEL`, `LIVEKIT_LLM_MODEL`, `LIVEKIT_TTS_VOICE` in `.env` or per-agent in the dashboard.

| Provider | STT | TTS | LLM |
|----------|-----|-----|-----|
| Google Cloud | `latest_long` | `hi-IN-Wavenet-A` etc. | `gemini-2.5-flash` |
| Groq | `whisper-large-v3-turbo` | `orpheus-v1-english` | `llama-3.3-70b-versatile` |
| Deepgram | `nova-2` | deepgram voices | — |
| Sarvam AI | `saaras:v3` | `bulbul:v2` (22 Indian langs) | — |

### LiveKit Cloud

Create an account at [livekit.cloud](https://livekit.cloud) and set:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

### Telephony (Twilio)

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+15550001111
```

---

## Project structure

```
├── frontend/              Next.js 16 + React 19 + Tailwind v4
│   └── src/
│       ├── app/           Dashboard pages (16 routes)
│       ├── components/    Workflow canvas, shadcn/ui, charts
│       └── hooks/         Voice session, API client
├── backend/
│   ├── app/
│   │   ├── api/           FastAPI routers (22 modules)
│   │   ├── core/          Config, security, tier gate
│   │   ├── models/        SQLAlchemy models
│   │   ├── schemas/       Pydantic schemas
│   │   ├── services/      STT, TTS, knowledge, tools, etc.
│   │   └── orchestration/ Agent loop, workflow engine, worker
│   ├── livekit_agent.py   LiveKit agent entrypoint
│   └── requirements.txt
├── docker-compose.yml     Full platform stack
├── .env.example           Configuration template
└── README.md
```

---

## Development

```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Frontend
cd frontend
npm install
npm run dev

# LiveKit agent (separate process)
python backend/livekit_agent.py
```

```bash
# Tests
cd backend && pytest -v
```

---

## License

Proprietary. All rights reserved.
