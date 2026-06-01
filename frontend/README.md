# Voise AI — Frontend

Next.js 16 dashboard and marketing site for Voise AI.

## Stack

- **Next.js 16** (App Router) · **React 19** · **TypeScript**
- **Tailwind CSS v4** — light/dark themes via `ThemeContext`
- **@xyflow/react** — workflow visual editor
- **Sarvam STT/TTS** — voice provider in agent playground
- **recharts** — analytics charts

## Development

```bash
npm install
npm run dev    # http://localhost:3000
```

Requires backend on **port 8001**. API calls use same-origin `/api/v1` (proxied in `next.config.ts`):

```ts
// next.config.ts rewrites /api/v1/* → BACKEND_URL (default http://localhost:8001)
```

Override with `NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1` if needed.

## Key routes

| Route | Purpose |
|-------|---------|
| `/` | Marketing landing |
| `/login`, `/register` | Auth |
| `/dashboard` | Overview |
| `/dashboard/agents` | Agent list & detail (playground) |
| `/dashboard/workflows` | Workflow list, editor (Visual / JSON / SAP / Test) |
| `/dashboard/campaigns` | Campaigns + workflow picker on create |
| `/dashboard/monitoring` | Live sessions |
| `/dashboard/approvals` | HITL queue |
| `/dashboard/settings` | Telephony, compliance, **Appearance** (theme) |

## Project docs

See repo root [DOCS.md](../DOCS.md) and [WORKFLOW_AUTOMATION.md](../WORKFLOW_AUTOMATION.md).
