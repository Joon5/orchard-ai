# FastAPI Agent Service + Next.js Wiring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a FastAPI microservice (`src/api/`) that exposes `/sms/inbound` (TwiML, for demo/eval) and `/agent/classify` (JSON, for Next.js), then wire Next.js's Twilio webhook to call `/agent/classify` for enriched intent context before Haiku generates the customer reply.

**Architecture:** Python FastAPI runs as a stateless Render service. Next.js calls it with a 4-second timeout and a shared secret; on any failure it falls back gracefully to Haiku-only mode with no customer-facing impact. The existing Next.js state machine, Supabase writes, and TwiML response are unchanged.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, pytest, httpx (TestClient), Pydantic v2. Next.js 14, TypeScript, Vitest. Render (deploy), `.claude/launch.json` (local dev).

**Spec:** `docs/superpowers/specs/2026-05-19-fastapi-nextjs-merge-design.md`

---

## File Map

### New Python files
| File | Responsibility |
|------|---------------|
| `src/api/models.py` | Pydantic request/response schemas |
| `src/api/agent_router.py` | `/agent/classify` business logic — intent + entity extraction |
| `src/api/main.py` | FastAPI app — thin router wiring models + agent_router |
| `tests/conftest.py` | pytest sys.path setup so `from api.main import app` resolves |
| `tests/test_api.py` | pytest suite (5 tests) using FastAPI TestClient |
| `render.yaml` | Render web service deployment config |

### Modified Python files
| File | Change |
|------|--------|
| `requirements.txt` | Add `pytest>=7.4.0` and `httpx>=0.27.0` |

### New Next.js files (in `.worktrees/phase1/`)
| File | Responsibility |
|------|---------------|
| `lib/ai/orchestrator-client.ts` | Typed HTTP client — calls `/agent/classify`, 4s timeout, FALLBACK on error |
| `__tests__/orchestrator-client.test.ts` | Vitest suite (4 tests) — mock fetch |

### Modified Next.js files (in `.worktrees/phase1/`)
| File | Change |
|------|--------|
| `app/api/webhooks/twilio/route.ts` | Import `classifyIntent`, inject context into Haiku system prompt |
| `.env.example` | Add `PYTHON_AGENT_URL` and `PYTHON_AGENT_SECRET` |
| `.claude/launch.json` | Add "Agent API" server entry |

---

## Task 1: Python test infrastructure + failing tests

**Files:**
- Modify: `requirements.txt`
- Create: `tests/conftest.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Add pytest and httpx to requirements.txt**

```
anthropic>=0.25.0
twilio>=8.0.0
python-dotenv>=1.0.0
fastapi>=0.110.0
uvicorn>=0.29.0
pydantic>=2.0.0
python-multipart>=0.0.9
pytest>=7.4.0
httpx>=0.27.0
```

- [ ] **Step 2: Install new dependencies**

Run from project root (activate venv first if using one):
```bash
pip install -r requirements.txt
```
Expected: httpx and pytest install successfully.

- [ ] **Step 3: Create tests/conftest.py**

```python
"""pytest configuration — adds src/ to sys.path so test imports resolve."""
import sys
import os

# Add src/ to path: resolves "from api.main import app" → src/api/main.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Set required env vars before any module is imported
os.environ.setdefault("ORCHARD_AGENT_SECRET", "test-secret")
```

- [ ] **Step 4: Create tests/test_api.py with all 5 tests**

```python
"""
Tests for the Orchard.ai FastAPI agent service.
All LLM calls are mocked — no real API keys required.
Run: pytest tests/test_api.py -v
"""
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create TestClient once for the whole module (app startup is slow)."""
    from api.main import app
    return TestClient(app)


SECRET = "test-secret"  # matches conftest.py os.environ.setdefault


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_health(client):
    """GET /health returns {"status": "ok", "mock_mode": <bool>}."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert isinstance(data["mock_mode"], bool)


def test_sms_inbound_returns_twiml(client):
    """POST /sms/inbound returns valid TwiML XML."""
    res = client.post(
        "/sms/inbound",
        data={
            "From": "+15555550101",
            "To": "+15555550200",
            "Body": "I need my AC fixed this week",
            "MessageSid": "SM_test_123",
            "NumMedia": "0",
        },
    )
    assert res.status_code == 200
    assert "text/xml" in res.headers["content-type"]
    assert "<Response>" in res.text
    assert "<Message>" in res.text


def test_classify_requires_secret(client):
    """POST /agent/classify returns 401 if X-Orchard-Secret is missing or wrong."""
    # Missing header
    res = client.post("/agent/classify", json={"message": "I need my AC fixed"})
    assert res.status_code == 401

    # Wrong header
    res = client.post(
        "/agent/classify",
        json={"message": "I need my AC fixed"},
        headers={"X-Orchard-Secret": "wrong-secret"},
    )
    assert res.status_code == 401


def test_classify_happy_path(client):
    """POST /agent/classify returns intent + extracted fields when secret is correct."""
    with patch("utils.llm_client.call_claude", return_value="booking_request"):
        res = client.post(
            "/agent/classify",
            json={"message": "I need my AC fixed this week", "conversation_history": []},
            headers={"X-Orchard-Secret": SECRET},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "booking_request"
    assert "extracted" in data
    assert isinstance(data["extracted"], dict)
    assert "needs_followup" in data
    assert data["needs_followup"] is False
    assert "suggested_response" in data
    assert data["suggested_response"] is None


def test_classify_fallback_on_llm_error(client):
    """POST /agent/classify returns intent=unknown (HTTP 200) when LLM raises."""
    with patch("utils.llm_client.call_claude", side_effect=Exception("Anthropic down")):
        res = client.post(
            "/agent/classify",
            json={"message": "test message"},
            headers={"X-Orchard-Secret": SECRET},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "unknown"
    assert data["needs_followup"] is True
```

- [ ] **Step 5: Run tests to confirm they all fail with ImportError**

```bash
pytest tests/test_api.py -v
```
Expected output — all 5 tests fail with:
```
ModuleNotFoundError: No module named 'api'
```
This confirms the test harness is wired correctly and the tests are genuinely failing.

- [ ] **Step 6: Commit test infrastructure**

```bash
git add requirements.txt tests/conftest.py tests/test_api.py
git commit -m "test: add pytest/httpx infrastructure and failing FastAPI test suite"
```

---

## Task 2: Pydantic models (`src/api/models.py`)

**Files:**
- Create: `src/api/models.py`

- [ ] **Step 1: Create src/api/models.py**

```python
"""
Orchard.ai API — Pydantic schemas.
Request/response models for /sms/inbound and /agent/classify.
"""
from typing import Optional
from pydantic import BaseModel


# ── /agent/classify request ────────────────────────────────────────────────────

class ConversationTurn(BaseModel):
    role: str
    content: str


class ClassifyRequest(BaseModel):
    message: str
    conversation_history: list[ConversationTurn] = []


# ── /agent/classify response ───────────────────────────────────────────────────

class ExtractedEntities(BaseModel):
    date: Optional[str] = None
    service: Optional[str] = None
    urgency: Optional[str] = None


class ClassifyResponse(BaseModel):
    intent: str
    extracted: ExtractedEntities
    needs_followup: bool
    suggested_response: Optional[str] = None


# ── /health response ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    mock_mode: bool
```

- [ ] **Step 2: Re-run tests — still failing (api.main not found), but no model errors**

```bash
pytest tests/test_api.py -v
```
Expected: still `ModuleNotFoundError: No module named 'api'`. Models file is not tested in isolation — this is expected.

---

## Task 3: Agent router (`src/api/agent_router.py`)

**Files:**
- Create: `src/api/agent_router.py`

- [ ] **Step 1: Create src/api/agent_router.py**

```python
"""
Orchard.ai API — Agent router.
Business logic for /agent/classify: intent classification + entity extraction.
"""
import sys
import os
import json

# Add src/ to path so sibling packages (agents/, utils/) are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.intake_agent import IntakeAgent
from utils.llm_client import call_claude
from api.models import ClassifyRequest, ClassifyResponse, ExtractedEntities


# ── Singletons ─────────────────────────────────────────────────────────────────

_intake = IntakeAgent()


# ── Intent → needs_followup mapping ───────────────────────────────────────────

_NEEDS_FOLLOWUP = {"complaint", "emergency", "unknown"}


# ── Entity extraction ──────────────────────────────────────────────────────────

_ENTITY_SYSTEM = """Extract structured data from this customer SMS message.
Return ONLY valid JSON with these exact fields (use null if not found):
{"date": <string or null>, "service": <string or null>, "urgency": <"high"|"low"|null>}

Examples:
- "I need my AC fixed this Thursday" → {"date": "Thursday", "service": "AC", "urgency": null}
- "URGENT: furnace not working" → {"date": null, "service": "furnace", "urgency": "high"}
- "How much for a tune-up?" → {"date": null, "service": "tune-up", "urgency": null}

Return JSON only. No explanation. No markdown."""


def _extract_entities(message: str) -> ExtractedEntities:
    """
    Extract date, service, urgency from message text.
    Returns empty ExtractedEntities on any error (JSON parse, LLM failure, etc).
    """
    try:
        raw = call_claude(
            system_prompt=_ENTITY_SYSTEM,
            user_message=message,
            max_tokens=60,
        )
        # Strip markdown fences if the model wraps in ```json ... ```
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        return ExtractedEntities(
            date=data.get("date"),
            service=data.get("service"),
            urgency=data.get("urgency"),
        )
    except Exception:
        return ExtractedEntities()


# ── Public function ────────────────────────────────────────────────────────────

def classify_message(req: ClassifyRequest) -> ClassifyResponse:
    """
    Classify a customer message and extract entities.

    Uses IntakeAgent for intent classification, then a second LLM call for
    entity extraction. Both calls fall back gracefully on failure.

    Returns ClassifyResponse — never raises.
    """
    try:
        intent = _intake.classify(req.message)
        extracted = _extract_entities(req.message)
    except Exception:
        intent = "unknown"
        extracted = ExtractedEntities()

    return ClassifyResponse(
        intent=intent,
        extracted=extracted,
        needs_followup=intent in _NEEDS_FOLLOWUP,
        suggested_response=None,
    )
```

- [ ] **Step 2: Re-run tests — still failing (api.main not found)**

```bash
pytest tests/test_api.py -v
```
Expected: still `ModuleNotFoundError: No module named 'api'`. Expected — we haven't created `main.py` yet.

---

## Task 4: FastAPI app (`src/api/main.py`) — tests now pass

**Files:**
- Create: `src/api/main.py`

- [ ] **Step 1: Create src/api/main.py**

```python
"""
Orchard.ai — FastAPI Agent Service

Endpoints:
  GET  /health           — readiness probe
  POST /sms/inbound      — Twilio-shaped, returns TwiML (demo/eval use)
  POST /agent/classify   — JSON in/out, called by Next.js in production
"""
import sys
import os

# Add src/ to sys.path so agent/pipeline/utils imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import Response
from api.models import ClassifyRequest, ClassifyResponse, HealthResponse
from api.agent_router import classify_message
from agents.sms_agent import SMSAgent
from pipelines.orchestrator import Orchestrator
from utils.llm_client import is_mock_mode

app = FastAPI(title="Orchard.ai Agent Service", version="0.1.0")

# Agent secret — set ORCHARD_AGENT_SECRET in environment
_AGENT_SECRET = os.getenv("ORCHARD_AGENT_SECRET", "")


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    """Readiness probe used by Render and local dev."""
    return HealthResponse(status="ok", mock_mode=is_mock_mode())


# ── /sms/inbound — Twilio-shaped TwiML endpoint (demo/eval only) ───────────────

@app.post("/sms/inbound")
async def sms_inbound(request: Request):
    """
    Accepts Twilio webhook form data, runs through the full Orchestrator,
    and returns a TwiML <Response>. For demo and eval use only — not in the
    production Next.js path.
    """
    form = await request.form()
    webhook_data = dict(form)

    sms = SMSAgent()
    parsed = sms.parse_inbound(webhook_data)
    message = parsed["body"]

    orch = Orchestrator(customer_phone=parsed["from"])
    result = orch.handle_inbound(message, channel="sms")

    reply = result.get("response", "")
    twiml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{reply}</Message></Response>"
    )
    return Response(content=twiml, media_type="text/xml")


# ── /agent/classify — JSON endpoint called by Next.js ─────────────────────────

@app.post("/agent/classify", response_model=ClassifyResponse)
def agent_classify(
    req: ClassifyRequest,
    x_orchard_secret: str = Header(default=None, alias="X-Orchard-Secret"),
):
    """
    Intent classification + entity extraction.
    Called by Next.js before generating the Haiku customer reply.
    Auth: X-Orchard-Secret header must match ORCHARD_AGENT_SECRET env var.
    Falls back to intent=unknown on any LLM error (HTTP 200, never 500).
    """
    if not _AGENT_SECRET or x_orchard_secret != _AGENT_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Orchard-Secret")

    return classify_message(req)
```

- [ ] **Step 2: Run tests — all 5 should pass**

```bash
pytest tests/test_api.py -v
```
Expected output:
```
tests/test_api.py::test_health PASSED
tests/test_api.py::test_sms_inbound_returns_twiml PASSED
tests/test_api.py::test_classify_requires_secret PASSED
tests/test_api.py::test_classify_happy_path PASSED
tests/test_api.py::test_classify_fallback_on_llm_error PASSED

5 passed
```
If any test fails, fix the failure before continuing.

- [ ] **Step 3: Smoke-test the server locally**

```bash
uvicorn src.api.main:app --reload --port 8000
```
Then in a second terminal:
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok","mock_mode":true}`

Stop the server (Ctrl+C) when done.

- [ ] **Step 4: Commit all Python API files**

```bash
git add src/api/models.py src/api/agent_router.py src/api/main.py tests/test_api.py tests/conftest.py
git commit -m "feat: add FastAPI agent service with /sms/inbound and /agent/classify endpoints"
```

---

## Task 5: Render config + launch.json update

**Files:**
- Create: `render.yaml`
- Modify: `.claude/launch.json`

- [ ] **Step 1: Create render.yaml**

```yaml
# Render deployment config for the Orchard.ai agent microservice.
# To scale from free tier to paid: change plan to "starter" (one-line change).
services:
  - type: web
    name: orchard-agent
    env: python
    plan: free
    pythonVersion: "3.11"
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false          # set manually in Render dashboard
      - key: ORCHARD_AGENT_SECRET
        sync: false          # set manually in Render dashboard
      - key: TWILIO_ACCOUNT_SID
        sync: false
      - key: TWILIO_AUTH_TOKEN
        sync: false
      - key: TWILIO_PHONE_NUMBER
        sync: false
```

- [ ] **Step 2: Add Agent API to .claude/launch.json**

Open `.claude/launch.json`. The current content is:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "Next.js Dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["--prefix", ".worktrees/phase1", "run", "dev"],
      "port": 3000
    },
    {
      "name": "Inngest Dev Server",
      "runtimeExecutable": "npx",
      "runtimeArgs": ["inngest-cli", "dev", "--port", "8288", "-u", "http://localhost:3000/api/inngest"],
      "port": 8288
    }
  ]
}
```

Replace it with:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "Next.js Dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["--prefix", ".worktrees/phase1", "run", "dev"],
      "port": 3000
    },
    {
      "name": "Inngest Dev Server",
      "runtimeExecutable": "npx",
      "runtimeArgs": ["inngest-cli", "dev", "--port", "8288", "-u", "http://localhost:3000/api/inngest"],
      "port": 8288
    },
    {
      "name": "Agent API",
      "runtimeExecutable": "uvicorn",
      "runtimeArgs": ["src.api.main:app", "--reload", "--port", "8000"],
      "port": 8000
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add render.yaml .claude/launch.json
git commit -m "chore: add Render deploy config and Agent API launch entry"
```

---

## Task 6: Next.js orchestrator-client — failing tests first

**Files:**
- Create: `.worktrees/phase1/__tests__/orchestrator-client.test.ts`

All steps in Tasks 6-8 run from within `.worktrees/phase1/` directory context. Run `npm` and `npx vitest` commands from `/Users/jonathan/SME Agentic Stack/.worktrees/phase1/`.

- [ ] **Step 1: Create .worktrees/phase1/__tests__/orchestrator-client.test.ts**

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Set env vars before importing the module under test
process.env.PYTHON_AGENT_URL = 'http://localhost:8000'
process.env.PYTHON_AGENT_SECRET = 'test-secret'

// Mock global fetch before module import
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// Import after env + fetch are set up
const { classifyIntent, FALLBACK } = await import('@/lib/ai/orchestrator-client')

describe('classifyIntent', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('returns parsed result on HTTP 200', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        intent: 'booking_request',
        extracted: { date: 'Thursday', service: 'AC', urgency: null },
        needs_followup: false,
        suggested_response: null,
      }),
    })

    const result = await classifyIntent('I need my AC fixed this Thursday')

    expect(result.intent).toBe('booking_request')
    expect(result.extracted.service).toBe('AC')
    expect(result.extracted.date).toBe('Thursday')
    expect(result.needs_followup).toBe(false)
  })

  it('falls back on timeout (AbortError)', async () => {
    const abortError = new DOMException('The operation was aborted', 'AbortError')
    mockFetch.mockRejectedValueOnce(abortError)

    const result = await classifyIntent('test message')

    expect(result.intent).toBe('unknown')
    expect(result.needs_followup).toBe(true)
    expect(result.suggested_response).toBeNull()
  })

  it('falls back on non-200 response', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })

    const result = await classifyIntent('test message')

    expect(result.intent).toBe('unknown')
    expect(result.needs_followup).toBe(true)
  })

  it('sends X-Orchard-Secret header in every request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        intent: 'unknown',
        extracted: {},
        needs_followup: true,
        suggested_response: null,
      }),
    })

    await classifyIntent('any message')

    const [_url, options] = mockFetch.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Record<string, string>
    expect(headers['X-Orchard-Secret']).toBe('test-secret')
    expect(headers['Content-Type']).toBe('application/json')
  })
})
```

- [ ] **Step 2: Run tests — confirm they fail with module not found**

From `.worktrees/phase1/`:
```bash
npx vitest run __tests__/orchestrator-client.test.ts
```
Expected failure:
```
Error: Cannot find module '@/lib/ai/orchestrator-client'
```

---

## Task 7: Implement Next.js orchestrator-client

**Files:**
- Create: `.worktrees/phase1/lib/ai/orchestrator-client.ts`

- [ ] **Step 1: Create .worktrees/phase1/lib/ai/orchestrator-client.ts**

```typescript
/**
 * Orchard.ai orchestrator client.
 *
 * Calls the Python FastAPI /agent/classify endpoint for intent classification
 * and entity extraction. Falls back gracefully on any failure (timeout, network
 * error, non-200 response) so the Twilio webhook is never blocked.
 *
 * Timeout: 4 seconds — well within Twilio's 15-second webhook limit.
 */

export interface ExtractedEntities {
  date?: string | null
  service?: string | null
  urgency?: string | null
}

export interface ClassifyResult {
  intent: string
  extracted: ExtractedEntities
  needs_followup: boolean
  suggested_response: string | null
}

/** Returned on any failure — Next.js continues with Haiku-only mode. */
export const FALLBACK: ClassifyResult = {
  intent: 'unknown',
  extracted: {},
  needs_followup: true,
  suggested_response: null,
}

export async function classifyIntent(
  message: string,
  conversationHistory: Array<{ role: string; content: string }> = []
): Promise<ClassifyResult> {
  const url = process.env.PYTHON_AGENT_URL
  const secret = process.env.PYTHON_AGENT_SECRET

  // If not configured (local dev without Python service), return FALLBACK silently
  if (!url || !secret) {
    return FALLBACK
  }

  try {
    const res = await fetch(`${url}/agent/classify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Orchard-Secret': secret,
      },
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory,
      }),
      signal: AbortSignal.timeout(4000), // 4-second hard timeout
    })

    if (!res.ok) {
      return FALLBACK
    }

    const data = await res.json()
    return {
      intent: data.intent ?? 'unknown',
      extracted: data.extracted ?? {},
      needs_followup: data.needs_followup ?? true,
      suggested_response: data.suggested_response ?? null,
    }
  } catch {
    // Covers: AbortError (timeout), network error, JSON parse error
    return FALLBACK
  }
}
```

- [ ] **Step 2: Run tests — all 4 should pass**

From `.worktrees/phase1/`:
```bash
npx vitest run __tests__/orchestrator-client.test.ts
```
Expected output:
```
✓ __tests__/orchestrator-client.test.ts (4)
  ✓ classifyIntent > returns parsed result on HTTP 200
  ✓ classifyIntent > falls back on timeout (AbortError)
  ✓ classifyIntent > falls back on non-200 response
  ✓ classifyIntent > sends X-Orchard-Secret header in every request

Test Files  1 passed (1)
Tests       4 passed (4)
```

- [ ] **Step 3: Run full Next.js test suite to confirm no regressions**

From `.worktrees/phase1/`:
```bash
npx vitest run
```
Expected: all pre-existing tests still pass, 4 new tests pass, 0 failures.

- [ ] **Step 4: Commit**

From project root (the worktree commits to the main git repo):
```bash
git add .worktrees/phase1/lib/ai/orchestrator-client.ts .worktrees/phase1/__tests__/orchestrator-client.test.ts
git commit -m "feat: add orchestrator-client with 4s timeout and graceful fallback"
```

---

## Task 8: Wire orchestrator-client into Twilio webhook + update .env.example

**Files:**
- Modify: `.worktrees/phase1/app/api/webhooks/twilio/route.ts`
- Modify: `.worktrees/phase1/.env.example`

- [ ] **Step 1: Add import to top of route.ts**

In `.worktrees/phase1/app/api/webhooks/twilio/route.ts`, add one import after the existing imports (after line 9, after `import { buildSystemPrompt } from '@/lib/ai/guardrails'`):

```typescript
import { classifyIntent } from '@/lib/ai/orchestrator-client'
```

The full import block at the top of the file should look like:
```typescript
import { NextResponse } from 'next/server'
import { twilioSignatureGuard } from '@/lib/twilio/verify'
import { createServiceClient } from '@/lib/supabase/server'
import { sendSms } from '@/lib/twilio/sms'
import { transitionStatus, writeEvent } from '@/lib/booking/state-machine'
import { deleteCalendarEvent } from '@/lib/google/calendar'
import { dispatchOwnerNotification } from '@/lib/notifications/dispatcher'
import { chat } from '@/lib/ai/haiku'
import { buildSystemPrompt } from '@/lib/ai/guardrails'
import { classifyIntent } from '@/lib/ai/orchestrator-client'
```

- [ ] **Step 2: Inject classify call into the "General AI reply" section**

Find the "General AI reply" section near the bottom of the file (around line 235):
```typescript
  // General AI reply
  const { data: services } = await db.from('services').select('*').eq('tenant_id', tenant.id).eq('active', true)
  const systemPrompt = buildSystemPrompt(tenant, services ?? [])

  const replyText = await chat({
    systemPrompt,
    messages: [{ role: 'user', content: body }],
  }).catch(() => `Thanks for reaching out! For immediate help, call ${tenant.phone}.`)
```

Replace it with:
```typescript
  // General AI reply
  const { data: services } = await db.from('services').select('*').eq('tenant_id', tenant.id).eq('active', true)
  const systemPrompt = buildSystemPrompt(tenant, services ?? [])

  // Call Python agent for intent classification (4s timeout, falls back silently)
  const classification = await classifyIntent(body)
  const enrichedSystemPrompt =
    classification.intent !== 'unknown'
      ? `${systemPrompt}\n\nContext: Customer intent classified as "${classification.intent}". Extracted info: ${JSON.stringify(classification.extracted)}.`
      : systemPrompt

  const replyText = await chat({
    systemPrompt: enrichedSystemPrompt,
    messages: [{ role: 'user', content: body }],
  }).catch(() => `Thanks for reaching out! For immediate help, call ${tenant.phone}.`)
```

- [ ] **Step 3: Add env vars to .env.example**

Open `.worktrees/phase1/.env.example`. Add these two lines at the end of the file:

```
# Python Agent Microservice
PYTHON_AGENT_URL=http://localhost:8000
PYTHON_AGENT_SECRET=changeme
```

- [ ] **Step 4: Run the full Next.js test suite**

From `.worktrees/phase1/`:
```bash
npx vitest run
```
Expected: all tests pass, 0 failures. The webhook modification is in a code path not covered by existing tests (no mock for the Python service), so no test regressions are expected.

- [ ] **Step 5: Run a TypeScript check on the modified file**

From `.worktrees/phase1/`:
```bash
npx tsc --noEmit --skipLibCheck 2>&1 | grep "webhooks/twilio"
```
Expected: no new errors on `app/api/webhooks/twilio/route.ts`. (Pre-existing TS errors in other files are out of scope for this task.)

- [ ] **Step 6: Commit**

```bash
git add .worktrees/phase1/app/api/webhooks/twilio/route.ts .worktrees/phase1/.env.example
git commit -m "feat: wire Python agent classifier into Twilio webhook for enriched Haiku context"
```

---

## Done

After all 8 tasks:

- `pytest tests/test_api.py -v` → 5 passing
- `npx vitest run` (from `.worktrees/phase1/`) → all tests passing including 4 new orchestrator-client tests
- `uvicorn src.api.main:app --reload --port 8000` starts cleanly
- `curl http://localhost:8000/health` → `{"status":"ok","mock_mode":true}`
- Next.js Twilio webhook calls Python for intent context, falls back silently if Python is down

**Next steps after this plan:**
1. Push to GitHub (`origin main`)
2. Create Render web service — point at this repo, set env vars in dashboard
3. Deploy Next.js to Vercel — add `PYTHON_AGENT_URL` (Render URL) + `PYTHON_AGENT_SECRET`
4. Confirm `/health` on Render URL before pointing Vercel at it
