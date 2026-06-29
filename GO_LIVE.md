# Voise AI — Go-Live Runbook

Production readiness for the India collections vertical. The code is hardened
(single Ultravox runtime, fail-loud services, gated simulated tools, startup
preflight, readiness probe). **Everything below requires real accounts,
credentials, or a live phone call — only the operator can do it.**

The startup preflight (`app/core/preflight.py`) will refuse to boot in
`ENVIRONMENT=prod` until the hard items in step 2 are satisfied. Treat a clean
boot as the first gate, not the last.

---

## 1. Provision infrastructure

- [ ] Postgres 15 with `pgvector` (compose uses `pgvector/pgvector:pg15`), reachable, backed up.
- [ ] Redis 7 with a password (session history, consent, rate limits).
- [ ] A public HTTPS host for the backend (`SERVER_HOST`) — Twilio, Ultravox, and Razorpay webhooks must reach it. Not localhost.
- [ ] (Optional) Temporal, Prometheus/Grafana, OTEL collector per `docker-compose.yml`.

## 2. Production `.env` (hard preflight gates marked ⛔)

```
ENVIRONMENT=prod
SECRET_KEY=<openssl rand -hex 32>          # ⛔ no default/placeholder
COOKIE_SECURE=true                          # HTTPS-only cookies
SERVER_HOST=api.yourdomain.com              # ⛔ public host, not localhost

ULTRAVOX_API_KEY=<real>                      # ⛔ VOICE_RUNTIME=ultravox
ULTRAVOX_CALLBACK_SECRET=<real>             # sign call.ended webhooks

# Reasoning LLM — at least one key, matching REASONING_LLM_PROVIDER ⛔
ANTHROPIC_API_KEY=<real>                     # preferred (auto → Claude)
GROQ_API_KEY=<real>                          # fallback

# Telephony — set all three together (partial config ⛔)
TWILIO_ACCOUNT_SID=<real>
TWILIO_AUTH_TOKEN=<real>
TWILIO_PHONE_NUMBER=<DLT-registered +91 number>

# Collections payment loop
RAZORPAY_KEY_ID=<live>
RAZORPAY_KEY_SECRET=<live>
RAZORPAY_WEBHOOK_SECRET=<from Razorpay dashboard>

# India compliance — flip ON for live commercial dialing
DLT_ENFORCEMENT=true
AI_DISCLOSURE_REQUIRED=true
ALLOW_SIMULATED_TOOLS=false                  # keep OFF (no fake KYC)

REDIS_PASSWORD=<strong>
DEMO_AGENT_ID=<set after step 4>
```

> Replace the hardcoded `SECRET_KEY` / `REDIS_PASSWORD` in `docker-compose.yml`
> with env references before any real deploy — committed secrets are not safe.

## 3. Migrate + verify boot

```bash
cd backend
pip install -r requirements.txt          # now includes razorpay + anthropic
alembic upgrade head                      # head = f6a7b8c9d0e1
uvicorn main:app --host 0.0.0.0 --port 8001
```

- [ ] Boot succeeds (preflight passed). If it aborts, fix the listed errors.
- [ ] `GET /health` → 200 (liveness).
- [ ] `GET /health/ready` → 200 with `postgres: ok`, `redis: ok` (503 if either is down).

## 4. Seed the collections + demo agents

```bash
python -m scripts.seed_demo_agent        # prints an agent id → DEMO_AGENT_ID
python -m scripts.seed_demo_data         # marketplace templates incl. collections
```

- [ ] Paste the printed id into `DEMO_AGENT_ID`, restart.

## 5. Compliance gate — prove it before dialing anyone

- [ ] DLT: with `DLT_ENFORCEMENT=true`, outbound from a **non-registered** number is refused; from a **registered** number is allowed.
- [ ] Place one real Twilio↔Ultravox call. Confirm the **AI-disclosure sentence is spoken first** and the transcript lands in `CallLog`.
- [ ] DND: add a number to `do_not_call`; a `140`-series call to it is blocked.
- [ ] Calling hours: a call outside 9am–9pm IST is blocked.

## 6. Collections loop — end to end

- [ ] Run the collections agent on a test number.
- [ ] Trigger `record_promise_to_pay` → `CallLog.outcome="SUCCESS"`, reason `promise_to_pay`.
- [ ] Trigger `send_payment_link` → borrower receives an SMS with a **real** Razorpay link (no fake link; service fails loudly if misconfigured).
- [ ] Pay the test link → Razorpay webhook (`payment.captured`, signature-validated) flips outcome to `payment_collected` and writes a usage record.
- [ ] `GET /api/v1/billing/usage` shows the outcome metric and ₹ owed.

## 7. Operational hardening (before scale)

- [ ] Load test concurrent calls; set `ULTRAVOX_MAX_CONCURRENT_CALLS` to your licensed ceiling.
- [ ] Point `/health/ready` at the load balancer / k8s readiness probe (not `/health`).
- [ ] Confirm `LOG_FORMAT=json` + OTEL endpoint wired; Grafana dashboards rendering.
- [ ] Rotate all secrets out of compose into your secrets manager.
- [ ] DB backup + restore drill.

---

## Still simulated (not production integrations)

These are **gated off** (`ALLOW_SIMULATED_TOOLS=false`) and return fake data —
do **not** enable them for real customers until backed by a real vendor:
`verify_aadhaar`, `verify_pan`, `check_gst`, `check_upi_payment`,
`translate_to_hindi`. If a flow needs real KYC, integrate a licensed provider
(e.g. Signzy/IDfy/Karza) and drop the `simulated` flag on that tool.
