# Product Requirements Document (PRD)

## Product Name: **Voise AI**

> **Doc index:** [DOCS.md](./DOCS.md) · **Workflow implementation:** [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md) (Phase 1 & 2 ✅)

## Version

v1.0 (MVP → Enterprise Beta)

## Owner

Product + Engineering

## Target Release

90–120 days MVP

---

## 1. 🎯 Problem Statement

Enterprises rely heavily on **voice-based workflows** (calls, reminders, onboarding, collections, support). Existing solutions are:

* Closed-source & vendor-locked
* Expensive at scale
* Hard to customize
* Poor at multilingual / Indian dialects
* Not designed for **AI agent orchestration**

There is a need for an **open, modular, enterprise-grade Voice AI platform** that allows businesses to:

* Build
* Deploy
* Orchestrate
* Monitor
  AI voice agents at scale — **without lock-in**.

---

## 2. 🧠 Product Vision

> Build an **open-source, enterprise-grade Voice AI Operating System** where companies can deploy multiple AI voice agents, control them centrally, and integrate with existing business workflows.

---

## 3. 👤 Target Users

### Primary

* Enterprise AI teams
* Contact-center transformation teams
* Fintech / BFSI ops teams
* AI solution builders (like you)

### Secondary

* BPOs
* SaaS companies with voice workflows
* System integrators

---

## 4. 🧩 Core Use Cases

| Use Case             | Description                          |
| -------------------- | ------------------------------------ |
| Inbound Voice Agent  | Customer support, FAQs               |
| Outbound Voice Agent | Reminders, collections, onboarding   |
| Voice + Workflow     | Call → CRM → Ticket → Follow-up      |
| Multilingual Voice   | English + Hindi + regional languages |
| Agent Swarms         | Multiple agents collaborating        |
| Compliance Calls     | Regulated scripts with logging       |

---

## 5. 🏗️ High-Level Architecture

```
Telephony (SIP / Twilio / Exotel)
        ↓
Speech-to-Text (STT)
        ↓
Agent Orchestrator (Brain)
        ↓
LLM / Tools / Workflows
        ↓
Text-to-Speech (TTS)
        ↓
Call Response
```

### Core Design Principles

* **Pluggable components**
* **Open-source first**
* **Self-hostable**
* **Observability by default**

---

## 6. 🧱 System Components

### 6.1 Voice Pipeline

#### STT (Speech to Text)

* Default: **Whisper / Faster-Whisper**
* Optional: Vosk, Coqui STT

#### TTS (Text to Speech)

* Default: **Coqui TTS**
* Optional: Piper, OpenVoice

#### Telephony

* SIP support
* Twilio / Exotel adapters
* WebRTC support (later)

---

### 6.2 Agent Orchestration Engine (CORE)

This is your **secret sauce**.

#### Responsibilities

* Manage multiple agents
* Route conversations
* Maintain state
* Invoke tools
* Failover between agents

#### Requirements

* Stateless execution
* Persistent memory layer
* Timeouts & retries
* Human handoff

#### Suggested Stack

* **Temporal (OSS)** for orchestration
* **FastAPI** for agent APIs
* **Redis** for session state
* **Postgres** for long-term memory

---

### 6.3 AI Agent Framework

Each agent has:

```yaml
agent_id:
persona:
goals:
tools:
memory_scope:
language:
compliance_rules:
```

#### Agent Types

* Single-task agent
* Supervisor agent
* Validator / compliance agent

Frameworks (pluggable):

* LangGraph
* CrewAI
* Custom FSM-based agents

---

### 6.4 Workflow Engine

| Capability | Status |
|------------|--------|
| JSON workflow definitions (v1) | ✅ **Done (Phase 1)** |
| In-process executor + instances | ✅ **Done (Phase 1)** |
| Built-in templates (collections, sales, healthcare) | ✅ **Done (Phase 1)** |
| Visual workflow builder | ✅ **Done (Phase 2)** |
| Email steps (SMTP / simulated) | ✅ **Done (Phase 2)** |
| SAP AR CSV ingest | ✅ **Done (Phase 2)** |
| Campaign ↔ workflow automation | ✅ **Done (Phase 2)** |
| Call-ended auto-advance | ⏳ Phase 3 |

Example (collections template):

```
VIP check → Voice call → Retry/wait → Email → Aging check → HITL → Escalate → End
```

**Reference:** [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md)

---

### 6.5 Multilingual & Localization

MVP:

* English
* Hindi

Later:

* Tamil, Telugu, Kannada, Marathi

Requirements:

* Language auto-detection
* Accent-tolerant STT
* Regional TTS voices

---

## 7. 📊 Observability & Monitoring (CRITICAL)

### Metrics

* Call success rate
* Latency (STT → LLM → TTS)
* Cost per call
* Drop-off rate
* Agent performance

### Tools

* **Prometheus + Grafana**
* **Langfuse** for LLM tracing
* **OpenTelemetry**

### Logs

* Call transcript
* Agent decisions
* Tool calls
* Errors

---

## 8. 🔐 Security & Compliance

### MVP

* Role-based access (RBAC)
* API keys
* Encrypted storage

### Enterprise

* Audit logs
* PII redaction
* Consent recording
* Script locking

---

## 9. 🖥️ Admin Dashboard (Web App)

### Key Screens

| Screen | Route | Status |
|--------|-------|--------|
| Agent Management | `/dashboard/agents` | ✅ |
| Workflow Editor (Visual, JSON, SAP, Test) | `/dashboard/workflows/[id]` | ✅ Ph1+2 |
| Campaigns | `/dashboard/campaigns` | ✅ + workflow picker |
| Call Logs & Transcripts | `/dashboard/logs` | ✅ |
| Live Call Monitoring | `/dashboard/monitoring` | ✅ |
| HITL Approvals | `/dashboard/approvals` | ✅ |
| Metrics Dashboard | `/dashboard/analytics` | ✅ |
| Configuration & theme | `/dashboard/settings` | ✅ |

### Tech

* React / Next.js
* Tailwind
* WebSockets for live calls

---

## 10. 🚀 MVP Scope (Must-Have)

| Requirement | Status |
|-------------|--------|
| Inbound + Outbound calling (Twilio + Ultravox) | ✅ |
| Agent per call + playground | ✅ |
| Voice pipeline (Ultravox default; custom fallback) | ✅ |
| Temporal call workflows | ✅ Infrastructure |
| Admin dashboard | ✅ |
| Workflow editor (JSON + visual) + templates | ✅ Ph1+2 |
| Campaigns + optional workflow automation | ✅ |
| Observability (monitoring, logs, analytics) | ✅ |
| HITL approvals | ✅ |
| English + Hindi (agent language config) | ✅ Partial |

---

## 11. 🔮 Roadmap (updated May 2026)

### Shipped (formerly “Post-MVP”)

* ✅ Visual workflow builder (in-app automation Phase 2)
* ✅ JSON workflow engine + templates (Phase 1)
* ✅ Human-in-the-loop (approvals dashboard + workflow `hitl_approval` node)
* ✅ Agent marketplace (template install)
* ✅ Ultravox voice runtime + agent sync

### Workflow Phase 3 (next)

* Call-ended webhook → auto-advance workflow instances
* Temporal worker registration for `process_due_workflow_instances`
* Visual node config panel (no JSON editing)
* Campaign detail: per-contact workflow instance status
* WhatsApp / SMS omnichannel nodes

### Broader platform

* Agent swarms (partial — LangGraph/swarm in orchestrator)
* Voice cloning (Voice Lab — Qwen path)
* On-device edge agents
* Deeper CRM connectors

---

## 12. 🧪 Non-Functional Requirements

| Area        | Requirement          |
| ----------- | -------------------- |
| Latency     | < 500ms response     |
| Uptime      | 99.9%                |
| Scalability | 10k concurrent calls |
| Deployment  | Docker + Kubernetes  |
| Hosting     | On-prem / cloud      |

---

## 13. 🛠️ Open Source Strategy

### Core

* Apache 2.0 / MIT license

### Plugins

* Telephony adapters
* STT/TTS providers
* LLM backends

### Business Model (Optional)

* Hosted version
* Enterprise support
* Compliance modules

---

## 14. 📍 Success Metrics

* Time to deploy agent < 1 day
* Cost per call ↓ 50%
* Call resolution rate ↑
* Enterprise adoption

---

## 15. 🧠 Competitive Differentiation vs BlueMachine

| BlueMachine   | Your Platform               |
| ------------- | --------------------------- |
| Closed        | Open                        |
| Vendor locked | Pluggable                   |
| Voice-first   | Voice + agent orchestration |
| India-focused | Global + local              |
