"""
Orchard.ai — Booking Agent
Handles scheduling requests, confirmations, and calendar context injection.
"""
from utils.llm_client import call_claude

BOOKING_SYSTEM = """You are a scheduling assistant for a solo tradesperson.
Your job is to confirm or propose appointment times based on customer requests.

IMPORTANT: Never confirm a specific time slot without calendar context.
If no availability data is provided, ask the customer for their preferred
time and say you'll confirm within the hour.

Keep responses under 160 characters (SMS-friendly)."""


class BookingAgent:
    def __init__(self, availability: list = None):
        # availability: list of open time slots from calendar integration
        # e.g. ["Monday 9am", "Tuesday 2pm"] — inject at runtime
        self.availability = availability or []

    def handle(self, message: str) -> dict:
        """Process a booking request. Injects availability context if present."""
        context = ""
        if self.availability:
            slots = ", ".join(self.availability)
            context = f"\n\nAvailable slots: {slots}"

        prompt = f"Customer message: {message}{context}"
        response_text = call_claude(BOOKING_SYSTEM, prompt)
        return {"response": response_text, "intent": "booking_request"}
