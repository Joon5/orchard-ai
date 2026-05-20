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
