"""
Orchard.ai — Intake Agent
Classifies inbound customer messages and generates initial responses.
"""
from utils.llm_client import call_claude

CLASSIFY_SYSTEM = """You are the intake agent for a solo tradesperson (HVAC, plumbing, electrical).
Classify the customer's message into exactly one of these intents:
- booking_request
- general_inquiry
- complaint
- emergency
- unknown

Respond with only the intent label, nothing else."""

RESPOND_SYSTEM = """You are a friendly assistant for a solo tradesperson.
Answer the customer's general inquiry briefly and professionally.
Keep responses under 160 characters when possible (SMS-friendly)."""


class IntakeAgent:
    def classify(self, message: str) -> str:
        """Classify a customer message into an intent category."""
        intent = call_claude(CLASSIFY_SYSTEM, message).strip().lower()
        # Guard against hallucinated intents
        valid = {"booking_request", "general_inquiry", "complaint", "emergency", "unknown"}
        return intent if intent in valid else "unknown"

    def respond(self, message: str) -> dict:
        """Generate a response for general inquiries."""
        response_text = call_claude(RESPOND_SYSTEM, message)
        return {"response": response_text, "intent": "general_inquiry"}
