# FastAPI Agent Service + Next.js Wiring — Design Spec

**Date:** 2026-05-19  
**Sub-project:** 1+2 of the Orchard.ai MVP merge path  
**Goal:** Wire the Python Orchard.ai agent brain into the production Next.js SaaS stack as a stateless microservice, without breaking existing functionality.

---

## Context

Two parallel tracks exist in this repo:

| Track | Path | Branch | Status |
|-------|------|--------|--------|
| Orchard.ai (Python) | `src/` | `main` | v0.1 — Orchestrator + Intake/Booking/SMS agents, eval harness, 2 commits |
| SME Agentic Stack (Next.js) | `.worktrees/phase1/` | `feature/phase1-build` | 24 committed tasks — multi-tenant SaaS, Supabase, Stripe, Twilio webhook, full state machine |

These will be merged: Python agents become the **intent classification brain**, Next.js remains the **production SaaS shell**. Python runs as a separate stateless microservice (FastAPI on Render) that Next.js calls over HTTP.

---

## Architecture

```
Twilio TFN
   │  POST application/x-www-form-urlencoded
   ▼
Next.js  /api/webhooks/twilio
   │  • Twilio signature verification
   │  • Tenant lookup (Supabase)
   │  • Calls Python /agent/classify (4s timeout, graceful fallback)
   │  • Haiku generates guarded customer-facing reply (with intent context)
   │  • State machine update + Supabase write
   │  • TwiML response to Twilio
   │
   │  POST { message, conversation_history }
   │  X-Orchard-Secret: <shared secret>
   ▼
FastAPI  /agent/classify
   │  • Stateless — no DB, no SMS sends, no tenant secrets
   │  • IntakeAgent.classify() + entity extraction
   │  • Returns intent + extracted entities + needs_followup
   ▼
Next.js continues:
   • Injects intent context into Haiku prompt
   • Haiku generates reply with tenant guardrails + FAQ overrides
   • State machine + TwiML as before
```

**Responsibility split:**
- **Python owns:** intent classification, entity extraction (`date`, `service`, `urgency`), eval harness
- **Next.js owns:** tenant config, guardrails, FAQ overrides, customer-facing reply text, state machine, Supabase writes, Twilio webhook entry/response

---

## Files Created / Modified

### New Python files
| File | Responsibility |
|------|---------------|
| `src/api/main.py` | FastAPI app — thin router, mounts endpoints |
| `src/api/models.py` | Pydantic request/response schemas |
| `src/api/agent_router.py` | Business logic for `/agent/classify` |
| `tests/test_api.py` | pytest suite using FastAPI TestClient |
| `render.yaml` | Render deployment config (web service, auto-deploy on push to `main`) |

### New Next.js files
| File | Responsibility |
|------|---------------|
| `lib/ai/orchestrator-client.ts` | Typed HTTP client to `/agent/classify` with timeout + fallback |
| `__tests__/orchestrator-client.test.ts` | Vitest suite — mock fetch, fallback, headers |

### Modified files
| File | Change |
|------|--------|
| `app/api/webhooks/twilio/route.ts` | Call `classifyIntent()` before Haiku reply; inject context if not `unknown` |
| `.env.example` | Add `PYTHON_AGENT_URL`, `PYTHON_AGENT_SECRET` |
| `.claude/launch.json` | Add Agent API entry (uvicorn, port 8000) |
| `requirements.txt` | Already includes `fastapi>=0.110.0`, `uvicorn>=0.29.0`, `pydantic>=2.0.0` — verify versions |

---

## FastAPI Endpoints

### `POST /sms/inbound` — demo/eval only (not in production path)
- **Content-Type:** `application/x-www-form-urlencoded` (Twilio native)
- **Auth:** none (demo endpoint)
- **Flow:** `SMSAgent.parse_inbound(webhook_data)` → `Orchestrator().handle_inbound(message, channel="sms")` → TwiML response
- **Response:** `Content-Type: text/xml`
  ```xml
  <Response><Message>{reply}</Message></Response>
  ```
- **Purpose:** Keeps eval harness working end-to-end. Twilio can point at this for demo/research. Not used by Next.js in production.

### `POST /agent/classify` — production endpoint (called by Next.js)
- **Content-Type:** `application/json`
- **Auth:** `X-Orchard-Secret` header must match `ORCHARD_AGENT_SECRET` env var → 401 if missing or wrong
- **Request:**
  ```json
  {
    "message": "Hi I need my AC looked at this week",
    "conversation_history": [{"role": "user", "content": "..."}]
  }
  ```
- **Response:**
  ```json
  {
    "intent": "booking_request",
    "extracted": {
      "date": "this week",
      "service": "AC",
      "urgency": null
    },
    "needs_followup": false,
    "suggested_response": null
  }
  ```
- **Intents:** `booking_request`, `general_inquiry`, `complaint`, `emergency`, `unknown`
- **Fallback behavior:** if Anthropic call raises → return `intent: "unknown"`, HTTP 200 (not 500). Next.js falls back to Haiku-only flow.

### `GET /health`
- **Response:** `{"status": "ok", "mock_mode": bool}`
- Used as Render health check probe.

---

## Next.js: `lib/ai/orchestrator-client.ts`

```typescript
export interface ClassifyResult {
  intent: string;
  extracted: { date?: string; service?: string; urgency?: string };
  needs_followup: boolean;
  suggested_response: string | null;
}

const FALLBACK: ClassifyResult = {
  intent: "unknown",
  extracted: {},
  needs_followup: true,
  suggested_response: null,
};

export async function classifyIntent(
  message: string,
  history: Array<{ role: string; content: string }> = []
): Promise<ClassifyResult> {
  // 4-second timeout — well within Twilio's 15s webhook limit
  // Falls back to FALLBACK on any error (timeout, 4xx, 5xx, network)
}
```

**Integration into `app/api/webhooks/twilio/route.ts`:**
- Call `classifyIntent(inboundBody, conversationHistory)` after parsing the message
- If `result.intent !== "unknown"`: prepend context to Haiku system prompt:
  `"Customer intent: {intent}. Extracted info: {JSON.stringify(extracted)}"`
- If `"unknown"`: Haiku handles everything as before — zero regression
- The state machine, Supabase writes, and TwiML response are **unchanged**

---

## Deployment

### Python (Render)
- **Start command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
- **Python version:** 3.11
- **Instance type:** Free tier for MVP launch. Upgrade to Starter ($7/mo) as soon as first customer is live — free tier spins down after inactivity, which adds cold-start latency to the first SMS after a quiet period.
- **Auto-deploy:** on push to `main`
- **Env vars (set in Render dashboard):** `ANTHROPIC_API_KEY`, `ORCHARD_AGENT_SECRET`, `TWILIO_*`

### Next.js (Vercel)
- **New env vars:** `PYTHON_AGENT_URL` (Render URL), `PYTHON_AGENT_SECRET`
- No other Vercel config changes

### Local dev (all three servers)
```
Port 3000 — Next.js dev     (npm run dev in .worktrees/phase1/)
Port 8288 — Inngest dev     (inngest-cli dev)
Port 8000 — Agent API       (uvicorn src.api.main:app --reload)
```
All three entries in `.claude/launch.json`.

**One-time Python setup:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY, ORCHARD_AGENT_SECRET
```

---

## Testing

### Python — `tests/test_api.py` (pytest + FastAPI TestClient)
| Test | What it verifies |
|------|-----------------|
| `test_sms_inbound_returns_twiml` | POST form data → `text/xml` response, `<Response><Message>` in body |
| `test_classify_happy_path` | Mock `call_claude` → booking_request → correct JSON shape |
| `test_classify_requires_secret` | Missing header → 401; wrong header → 401 |
| `test_classify_fallback_on_llm_error` | Mock `call_claude` raises → `intent: "unknown"`, HTTP 200 |
| `test_health` | GET /health → `{"status": "ok"}` |

### Next.js — `__tests__/orchestrator-client.test.ts` (Vitest)
| Test | What it verifies |
|------|-----------------|
| `returns parsed result on success` | Mock fetch 200 → typed ClassifyResult returned |
| `falls back on timeout` | Mock fetch throws AbortError → FALLBACK returned |
| `falls back on non-200` | Mock fetch 500 → FALLBACK returned |
| `sends correct headers` | Verify `X-Orchard-Secret` is present in fetch call |

### Existing test suites — unchanged
- `evals/intake_evals.py` — still runs against `IntakeAgent` directly
- `__tests__/acceptance.test.ts` — unchanged (state machine, RLS, rate limiting untouched)

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Python service down | `classifyIntent` catches fetch error → FALLBACK → Haiku handles alone |
| Python timeout (>4s) | AbortSignal fires → FALLBACK → Haiku handles alone |
| Python returns 4xx/5xx | Non-200 check → FALLBACK → Haiku handles alone |
| Anthropic down (Python side) | `agent_router.py` catches exception → returns `intent: "unknown"`, HTTP 200 |
| Bad `X-Orchard-Secret` | 401 — Next.js logs warning, uses FALLBACK |

In every failure case: the customer gets a reply (from Haiku alone), and the incident is logged. No silent drops.

---

## Scale path

The Python service is fully stateless — no DB connections, no shared state. Scaling from Render free → paid is a one-line change in `render.yaml` (`plan: starter`). Horizontal scaling (multiple instances) works without any code changes. When load justifies it, move to `plan: standard` with auto-scaling.
