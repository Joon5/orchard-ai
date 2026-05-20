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
