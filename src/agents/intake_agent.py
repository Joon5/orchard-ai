"""
Orchard.ai — Intake Agent
First-touch classifier and general inquiry responder for an HVAC business.

Responsibilities:
  - Classify inbound customer messages into one of five intent categories
  - Generate short, SMS-friendly replies for general inquiries
  - Surface emergency signals immediately for priority routing

Failure risks: see docs/failure-modes.md → Category 1 (intent misclassification)
"""
from utils.llm_client import call_claude

# ── System prompts ─────────────────────────────────────────────────────────────

CLASSIFY_SYSTEM = """You are the intake agent for an HVAC (heating, ventilation, and air conditioning) business.
A customer has sent a message. Classify it into EXACTLY ONE of these intent categories:

  booking_request  — customer wants to schedule a visit, repair, tune-up, or installation
  general_inquiry  — customer is asking a question (price, hours, services, location, etc.)
  complaint        — customer is expressing dissatisfaction about a past or missed service
  emergency        — customer describes an urgent situation (no heat in winter, AC failure in heat, flooding, smoke, gas smell)
  unknown          — message is unclear, spam, or doesn't fit any category

Rules:
- If the message contains BOTH a complaint AND a booking signal, classify as: booking_request
- If the message contains an emergency signal, always classify as: emergency
- Respond with ONLY the intent label. No explanation. No punctuation. Lowercase only.

Examples:
  "I need my AC looked at this week"              → booking_request
  "How much does a tune-up cost?"                 → general_inquiry
  "Nobody showed up for my appointment"           → complaint
  "Nobody showed up and I still need you to come" → booking_request
  "My furnace stopped working and it's freezing"  → emergency
  "Hi"                                            → unknown"""

RESPOND_SYSTEM = """You are a friendly, professional assistant for an HVAC business called Orchard.ai.
Answer the customer's question briefly and helpfully.

Rules:
- Keep responses under 155 characters (SMS-friendly)
- Be warm but efficient — no filler phrases like "Great question!"
- Always end with a soft call-to-action (offer to book, call, or help further)
- If you don't know specific details (exact pricing, exact hours), give a realistic range and invite them to call

Business context:
- Services: AC repair, furnace repair, tune-ups, new installations, emergency calls
- Tune-up price range: $79–$129
- Repair price range: $150–$400+ depending on parts
- Hours: Mon–Sat 8am–6pm; emergency calls 24/7
- Response time: same-day or next-day for most calls"""

EMERGENCY_RESPONSE = (
    "This sounds urgent — please call us immediately at {{PHONE}}. "
    "We handle HVAC emergencies 24/7."
)

# ── Valid intent set ───────────────────────────────────────────────────────────

VALID_INTENTS = frozenset({
    "booking_request",
    "general_inquiry",
    "complaint",
    "emergency",
    "unknown",
})


# ── Agent class ────────────────────────────────────────────────────────────────

class IntakeAgent:
    """Classifies inbound messages and handles general inquiries."""

    def classify(self, message: str) -> str:
        """
        Classify a customer message into an intent category.

        Returns one of: booking_request, general_inquiry, complaint, emergency, unknown
        Never raises — unknown is the safe fallback.
        """
        if not message or not message.strip():
            return "unknown"

        try:
            raw = call_claude(
                system_prompt=CLASSIFY_SYSTEM,
                user_message=message.strip(),
                max_tokens=10,  # intent label only — tiny output
            )
            intent = raw.strip().lower().rstrip(".")
            return intent if intent in VALID_INTENTS else "unknown"
        except Exception:
            return "unknown"

    def respond(self, message: str) -> dict:
        """
        Generate a response for a general inquiry.

        Returns: {"response": str, "intent": "general_inquiry"}
        """
        try:
            text = call_claude(
                system_prompt=RESPOND_SYSTEM,
                user_message=message.strip(),
                max_tokens=100,
            )
            # Hard cap at 155 chars for SMS safety
            if len(text) > 155:
                text = text[:152] + "..."
        except Exception:
            text = "Happy to help! Give us a call or text back with your question and we'll get right back to you."

        return {"response": text, "intent": "general_inquiry"}

    def handle_emergency(self) -> dict:
        """Return a canned emergency response for immediate routing."""
        return {
            "response": EMERGENCY_RESPONSE,
            "intent": "emergency",
            "priority": "high",
        }
