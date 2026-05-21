# Voise AI

**Voise AI** is an AI-powered voice automation platform for operational workflows: deploy AI outbound call agents for payment reminders, lead qualification, and appointment confirmation.

## What it includes

- **AI Outbound Call Agents** — Natural voice conversations at scale
- **Payment Reminder Calls** — Automated payment collection workflows
- **Lead Qualification Calls** — AI screening, scoring, and routing
- **Appointment Confirmation** — Booking, rescheduling, and no-show reduction

## Project structure

| Path | Stack |
|------|--------|
| `frontend/` | Next.js dashboard & marketing site |
| `backend/` | FastAPI API, sessions, tools, Ultravox integration |
| `docker-compose.yml` | PostgreSQL, Redis, Temporal, API |

## Quick start

1. Copy `backend/.env.example` → `backend/.env` and set `ULTRAVOX_API_KEY`
2. `docker compose up` (or run Postgres/Redis locally)
3. Backend: `cd backend && uvicorn main:app --reload --port 8001`
4. Frontend: `cd frontend && npm run dev`

Open [http://localhost:3000](http://localhost:3000), register, create an agent, and use **Playground → Start call**.

## Configuration

| Variable | Purpose |
|----------|---------|
| `VOICE_RUNTIME=ultravox` | Use Ultravox for all voice (default) |
| `ULTRAVOX_API_KEY` | Required for voice |
| `GROQ_API_KEY` | Optional; analytics/compliance helpers |

## License

Proprietary. Not open source.
