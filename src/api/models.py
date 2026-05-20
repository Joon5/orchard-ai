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
