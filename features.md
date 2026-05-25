# Complete Feature List

## Enterprise Voice AI & Agent Orchestration Platform

> **Doc index:** [DOCS.md](./DOCS.md) · **Last updated:** May 2026

---

## Implementation status (shipped in repo)

| Category | Shipped | Notes |
|----------|---------|--------|
| Ultravox voice runtime + Twilio | ✅ | Default `VOICE_RUNTIME=ultravox` |
| Agent CRUD, playground, knowledge (RAG) | ✅ | Ultravox agent sync |
| Campaigns (CSV, start/pause, dial) | ✅ | Optional `workflow_id` on create/start |
| **Workflow automation Phase 1** | ✅ | JSON definitions, engine, templates, instances — [WORKFLOW_AUTOMATION.md](./WORKFLOW_AUTOMATION.md) |
| **Workflow automation Phase 2** | ✅ | Visual builder, email node, SAP ingest, process-due |
| **Workflow automation Phase 3** | ✅ | Call-ended advance, Temporal scheduler, config panel, campaign WF UI |
| **Workflow automation Phase 4** | ✅ | Org scoping, WhatsApp provider, condition rules UI |
| **Multi-layer memory (Phase 6)** | ✅ | Working/procedural memory, governance, TTL |
| **Voice intelligence (Phase 8)** | ✅ | Emotion tracker, end-of-call service, cost/time awareness |
| Theme colour refresh | ✅ | Indigo/violet palette, pink accent, warm charcoal dark bg |
| React Doctor cleanup | ✅ | 571+ fixes across 34 files, score 76/100 |
| HITL approvals, live monitoring, analytics | ✅ | Dashboard |
| Light/dark theme | ✅ | Settings → Appearance |
| Demo seed | ✅ | `demo@voise.ai` / `DemoVoise2026!` |

Items below are the **full product catalog**; not all rows are implemented yet. See [missing_features.md](./missing_features.md) for enterprise gaps.

---

## 1️⃣ Telephony & Voice Infrastructure

### Call Handling

* Inbound call handling
* Outbound call campaigns
* Scheduled calls
* Call retries & backoff
* Call queuing
* Concurrent call handling
* Call transfer (AI → human)
* Conference calling (AI + human)
* Call recording
* Call playback

### Telephony Integrations

* SIP trunk support
* Twilio adapter
* Exotel adapter
* Plivo adapter
* Custom telephony provider plugin
* WebRTC calling
* Phone number management
* DID mapping per agent

---

## 2️⃣ Speech Processing (STT / TTS)

### Speech-to-Text (STT)

* Real-time streaming STT
* Batch STT (post-call)
* Accent-tolerant transcription
* Noise handling
* Language auto-detection
* Partial (interim) transcripts
* Timestamped transcripts
* Profanity filtering
* Custom vocabulary injection

### Text-to-Speech (TTS)

* Real-time streaming TTS
* Multiple voices per language
* Gender selection
* Voice speed / pitch control
* Emotion / prosody control
* SSML support
* Voice fallback handling
* Custom voice models (enterprise)

---

## 3️⃣ Multilingual & Localization

* Multi-language conversation support
* Language auto-detection
* Per-agent language configuration
* Code-switching (Hindi ↔ English)
* Regional accent handling
* Locale-based responses
* Language-specific scripts
* Translation fallback

---

## 4️⃣ AI Agent System

### Agent Definition

* Agent persona configuration
* Agent goals & constraints
* Role-based agents
* Prompt templates
* System instructions per agent
* Compliance-locked prompts
* Agent versioning

### Agent Types

* Inbound support agent
* Outbound sales agent
* Collections agent
* Onboarding agent
* Supervisor agent
* Validator / compliance agent
* Sentiment analysis agent

---

## 5️⃣ Agent Orchestration Engine

* Multi-agent orchestration
* Supervisor → worker agent model
* Dynamic agent routing
* Context sharing between agents
* Agent fallback & escalation
* Agent failover
* State management per call
* Timeouts & retries
* Human handoff triggers
* Tool invocation control
* Policy-based routing

---

## 6️⃣ Memory & Context Management

* Short-term conversational memory
* Long-term user memory
* Session-based memory
* Cross-call memory
* Memory scoping per agent
* PII-aware memory storage
* Memory expiration policies
* Vector-based memory search
* Transcript summarization

---

## 7️⃣ Workflow & Automation

### Workflow Engine

| Feature | Status |
|---------|--------|
| JSON workflow definitions (v1 schema) | ✅ Shipped |
| Visual workflow builder (`@xyflow/react`) | ✅ Phase 2 |
| Conditional branching (`condition` nodes) | ✅ Shipped |
| Built-in templates (collections, lead qual, appointment) | ✅ Shipped |
| Workflow instances + test runs | ✅ Shipped |
| Wait / retry / `process-due` scheduler | ✅ Shipped |
| Voice call step (campaign dial integration) | ✅ Shipped |
| Email step (SMTP or simulated + audit) | ✅ Phase 2 |
| HITL approval step | ✅ Shipped |
| Escalate / end nodes | ✅ Shipped |
| SAP AR CSV ingest | ✅ Phase 2 |
| Campaign ↔ workflow on start | ✅ Phase 2 |
| YAML definitions | ⏳ JSON only today |
| Parallel execution steps | ⏳ Planned |
| Event-driven auto-advance on call end | ⏳ Phase 3 |

### Business Automation

| Feature | Status |
|---------|--------|
| Payment reminder flows (template) | ✅ Shipped |
| Email triggers | ✅ Shipped |
| WhatsApp messaging w/ templates | ✅ Phase 4 (simulated + Twilio status callback) |
| Organization-scoped workflows | ✅ Phase 4 (all `WorkflowService` methods) |
| Condition rules UI (JSON/visual toggle) | ✅ Phase 4 |
| Multi-layer memory (working, procedural) | ✅ Phase 6 |
| Memory governance (TTL, `do_not_remember` flags) | ✅ Phase 6 |
| Emotion tracking (pace/tone adaptation) | ✅ Phase 8 |
| End-of-call intelligence (outcome, satisfaction, next-steps) | ✅ Phase 8 |
| Cost-aware model downgrade | ✅ Phase 8 |
| Time-aware prompting | ✅ Phase 8 |
| CRM lookup & update | ⏳ Via tools / custom |
| Ticket creation | ⏳ Planned |
| Follow-up SMS | ⏳ Planned |
| API webhooks (workflow) | ⏳ Partial (Ultravox call-ended) |
| Database queries | ⏳ Via tools |

---

## 8️⃣ Tool & API Integrations

* REST API tool calling
* GraphQL support
* Internal tool registry
* Tool permissioning per agent
* Rate limiting per tool
* Tool execution logs
* Tool retries & fallbacks

---

## 9️⃣ Observability & Analytics

### Real-Time Monitoring

* Live call monitoring
* Live transcript streaming
* Agent decision trace
* Tool execution trace

### Analytics

* Call volume analytics
* Success / failure rates
* Drop-off analysis
* Cost per call
* Latency breakdown (STT / LLM / TTS)
* Agent performance metrics
* Language-wise analytics

### Logging

* Full call logs
* Transcripts
* Agent reasoning logs
* Error logs
* Audit logs

---

## 🔟 LLM & Model Management

* Multiple LLM backends
* Model routing rules
* Model fallback logic
* Prompt A/B testing
* Cost tracking per model
* Token usage analytics
* On-prem LLM support
* Fine-tuned model support

---

## 1️⃣1️⃣ Security, Privacy & Compliance

### Security

* Role-based access control (RBAC)
* API key management
* OAuth support
* Secrets management
* Network isolation
* Rate limiting

### Compliance

* Consent capture
* Script locking
* Call disclaimers
* PII masking & redaction
* Data retention policies
* Audit trails
* Region-specific compliance (RBI, GDPR-ready)

---

## 1️⃣2️⃣ Admin & Operations Dashboard

### Agent Management

* Create / edit / clone agents
* Agent status (active / paused)
* Agent assignment to numbers
* Agent version history

### Call Management

* Call search & filtering
* Transcript viewer
* Call playback
* Manual call intervention

### Workflow Management

| Feature | Status |
|---------|--------|
| Workflow creation & editing (Visual + JSON) | ✅ Shipped |
| Publish / enable workflows (`active` status) | ✅ Shipped |
| Workflow versioning (DB `version` field) | ✅ Partial |
| Per-organization workflow isolation | ⏳ Schema ready, filters TBD |

---

## 1️⃣3️⃣ Configuration & Controls

* Environment configs (dev/stage/prod)
* Feature flags
* Rate controls
* Language controls
* Agent throttling
* Fail-safe modes
* Kill switch

---

## 1️⃣4️⃣ Deployment & Infrastructure

* Self-hosted deployment
* Cloud deployment
* On-prem deployment
* Docker support
* Kubernetes support
* Horizontal auto-scaling
* Blue-green deployments
* Health checks

---

## 1️⃣5️⃣ Developer Experience

* REST APIs
* Webhooks
* SDKs (Python / JS)
* CLI tools
* Plugin framework
* Local development mode
* Sandbox environment

---

## 1️⃣6️⃣ Human-in-the-Loop

* Live agent takeover
* Supervisor monitoring
* Agent whisper mode
* Manual overrides
* Feedback tagging
* Training data capture

---

## 1️⃣7️⃣ AI Safety & Quality Controls

* Hallucination detection
* Sentiment analysis
* Toxicity detection
* Response validation
* Script compliance checks
* Confidence scoring
* Auto-escalation rules

---

## 1️⃣8️⃣ Campaign & Batch Operations

* Outbound call campaigns
* Contact list uploads
* Campaign scheduling
* Campaign analytics
* Throttling per campaign
* A/B testing scripts

---

## 1️⃣9️⃣ Marketplace & Extensibility

* Agent template marketplace
* Workflow templates
* Plugin marketplace
* Custom integrations
* Community-contributed agents

---

## 2️⃣0️⃣ Business & Commercial (Optional)

* Multi-tenant support
* Organization management
* Usage-based metering
* Billing hooks
* Cost controls
* SLA configuration

