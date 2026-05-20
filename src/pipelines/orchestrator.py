"""
Orchard.ai — Central Orchestrator
Routes inbound customer events to the appropriate agent and manages handoffs.

Entry point: Orchestrator().handle_inbound(message, channel)
"""
import sys
import os

# Allow running from src/pipelines/ or from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.intake_agent import IntakeAgent
from agents.booking_agent import BookingAgent
from agents.sms_agent import SMSAgent
from utils.logger import log_event
from utils.llm_client import is_mock_mode


class Orchestrator:
    """
    Central router. Receives a message, classifies intent, routes to the
    correct agent, and returns a structured result dict.

    Args:
        availability: Optional list of open calendar slots (strings) to inject
                      into the booking agent. Pass [] or None if not connected.
        customer_phone: Default outbound SMS destination.
    """

    def __init__(self, availability: list = None, customer_phone: str = None):
        self.intake  = IntakeAgent()
        self.booking = BookingAgent(availability=availability or [])
        self.sms     = SMSAgent(default_to=customer_phone)

    def handle_inbound(self, message: str, channel: str = "sms") -> dict:
        """
        Main entry point. Classify a message and route to the correct agent.

        Args:
            message: Raw inbound customer text.
            channel: "sms" (default) or "web". SMS triggers outbound reply.

        Returns:
            {
              "response":      str,           # text to send back to customer
              "intent":        str,           # classified intent
              "needs_followup": bool,         # True if manual follow-up needed
              "sms_result":    dict | None,   # result of SMSAgent.send() if channel="sms"
            }
        """
        message = (message or "").strip()
        if not message:
            return self._fallback("empty message")

        log_event("inbound", {"channel": channel, "message": message, "mock": is_mock_mode()})

        # ── Step 1: Classify intent ────────────────────────────────────────────
        intent = self.intake.classify(message)
        log_event("intent_classified", {"intent": intent})

        # ── Step 2: Route to agent ─────────────────────────────────────────────
        if intent == "emergency":
            result = self.intake.handle_emergency()

        elif intent == "booking_request":
            result = self.booking.handle(message)

        elif intent == "general_inquiry":
            result = self.intake.respond(message)

        elif intent == "complaint":
            # Complaints get a human-escalation response + flagged for follow-up
            result = {
                "response": (
                    "I'm sorry to hear that. I'm flagging your message for our team "
                    "and someone will call you within the hour."
                ),
                "intent": "complaint",
                "needs_followup": True,
            }

        else:
            result = self._fallback(intent)

        # Ensure needs_followup key always present
        result.setdefault("needs_followup", False)

        # ── Step 3: Send reply via channel ─────────────────────────────────────
        sms_result = None
        if channel == "sms":
            sms_result = self.sms.send(result["response"])
            log_event("sms_dispatched", sms_result)

        result["sms_result"] = sms_result
        log_event("handled", {"intent": intent, "needs_followup": result["needs_followup"]})
        return result

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _fallback(self, reason: str = "") -> dict:
        log_event("fallback", {"reason": reason})
        return {
            "response": "Thanks for reaching out! Someone from our team will follow up with you shortly.",
            "intent": "unknown",
            "needs_followup": True,
        }


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("Orchard.ai Orchestrator — quick test\n")
    test_messages = [
        "Hi I need my AC looked at this week",
        "How much does a tune-up cost?",
        "My furnace stopped working and it's freezing in here",
        "Nobody showed up last Tuesday and I still need service",
    ]

    orch = Orchestrator(availability=["Thursday 9am", "Friday 2pm"])

    for msg in test_messages:
        print(f"Customer: {msg}")
        result = orch.handle_inbound(msg, channel="sms")
        print(f"Intent:   {result['intent']}")
        print(f"Reply:    {result['response']}")
        print(f"Followup: {result['needs_followup']}")
        print()
