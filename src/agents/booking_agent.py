"""
Orchard.ai — Booking Agent
Handles scheduling requests for an HVAC business.

Key design principle: NEVER confirm a time slot without calendar context.
If availability is not injected, propose a soft "we'll confirm shortly" response.

Failure risks: see docs/failure-modes.md → Category 2 (booking hallucination)
"""
from utils.llm_client import call_claude

# ── System prompts ─────────────────────────────────────────────────────────────

BOOKING_SYSTEM = """You are the scheduling assistant for an HVAC business called Orchard.ai.
A customer wants to book a service visit.

Your job:
1. Acknowledge their request warmly
2. If available time slots are provided below, offer them specifically
3. If NO slots are provided, do NOT invent times — instead say you'll confirm availability shortly
4. Ask for their address if not already provided
5. Keep the response under 155 characters (SMS limit)

Rules:
- Never confirm a specific time you haven't been given
- Never say "I'll check" — either you have slots or you don't
- Be direct and friendly; no filler phrases
- Always end by asking what they need next (address, confirmation, etc.)"""

BOOKING_WITH_SLOTS_SYSTEM = """You are the scheduling assistant for an HVAC business called Orchard.ai.
A customer wants to book a service visit.

Available time slots (from the calendar): {slots}

Offer these slots clearly and ask the customer to pick one.
Keep response under 155 characters. Be warm and direct.
After they pick a slot, ask for their address to finalize the booking."""

NO_SLOTS_RESPONSE = (
    "Got it! We'll check our schedule and text you back within the hour "
    "to confirm a time. What's your address?"
)

CONFIRM_SYSTEM = """You are confirming an HVAC appointment for a customer.
Given: the chosen slot and customer details, write a short SMS confirmation.
Include: what service, when, and that someone will arrive in the appointment window.
Keep under 155 characters."""


# ── Agent class ────────────────────────────────────────────────────────────────

class BookingAgent:
    """
    Handles scheduling requests with optional calendar context injection.

    Usage:
        agent = BookingAgent(availability=["Thursday 9am", "Friday 2pm"])
        result = agent.handle("I need my AC fixed this week")
    """

    def __init__(self, availability: list = None):
        """
        Args:
            availability: List of open time slot strings from your calendar integration.
                          Pass an empty list or None if calendar is not connected yet.
                          Example: ["Thursday 9am", "Friday 2pm", "Saturday 10am"]
        """
        self.availability = availability or []

    def handle(self, message: str, customer_data: dict = None) -> dict:
        """
        Process a booking request and return a response.

        Args:
            message:       The customer's raw message.
            customer_data: Optional dict with keys like 'name', 'address', 'phone'.

        Returns:
            {"response": str, "intent": "booking_request", "needs_followup": bool}
        """
        message = message.strip()
        customer_data = customer_data or {}

        try:
            if self.availability:
                # We have real slots — offer them
                slots_str = ", ".join(self.availability)
                system = BOOKING_WITH_SLOTS_SYSTEM.format(slots=slots_str)
                context = self._build_context(message, customer_data)
                response_text = call_claude(
                    system_prompt=system,
                    user_message=context,
                    max_tokens=100,
                )
                needs_followup = False
            else:
                # No calendar context — use safe no-hallucination response
                response_text = NO_SLOTS_RESPONSE
                needs_followup = True

        except Exception:
            response_text = NO_SLOTS_RESPONSE
            needs_followup = True

        # Enforce SMS length limit
        if len(response_text) > 155:
            response_text = response_text[:152] + "..."

        return {
            "response": response_text,
            "intent": "booking_request",
            "needs_followup": needs_followup,
        }

    def confirm(self, slot: str, service: str, customer_name: str = "") -> dict:
        """
        Generate a final booking confirmation SMS once slot is agreed.

        Args:
            slot:          Confirmed time, e.g. "Thursday March 20 at 9am"
            service:       Type of service, e.g. "AC tune-up"
            customer_name: Optional customer first name for personalization.

        Returns:
            {"response": str, "intent": "booking_confirmed"}
        """
        greeting = f"Hi {customer_name}! " if customer_name else ""
        prompt = f"{greeting}Service: {service}. Slot: {slot}."

        try:
            text = call_claude(
                system_prompt=CONFIRM_SYSTEM,
                user_message=prompt,
                max_tokens=80,
            )
            if len(text) > 155:
                text = text[:152] + "..."
        except Exception:
            text = (
                f"Confirmed! Your {service} is booked for {slot}. "
                "We'll text you when we're on the way."
            )[:155]

        return {"response": text, "intent": "booking_confirmed"}

    def _build_context(self, message: str, customer_data: dict) -> str:
        """Build a context string for the LLM that includes customer details if known."""
        lines = [f"Customer message: {message}"]
        if customer_data.get("name"):
            lines.append(f"Customer name: {customer_data['name']}")
        if customer_data.get("address"):
            lines.append(f"Address: {customer_data['address']}")
        return "\n".join(lines)
