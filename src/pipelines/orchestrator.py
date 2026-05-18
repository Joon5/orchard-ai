"""
Orchard.ai — Central Orchestrator
Routes inbound events to the appropriate agent and manages handoffs.
"""
from agents.intake_agent import IntakeAgent
from agents.booking_agent import BookingAgent
from agents.sms_agent import SMSAgent
from utils.logger import log_event

class Orchestrator:
    def __init__(self):
        self.intake = IntakeAgent()
        self.booking = BookingAgent()
        self.sms = SMSAgent()

    def handle_inbound(self, message: str, channel: str = "sms") -> dict:
        """Main entry point. Classify message and route to correct agent."""
        log_event("inbound", {"channel": channel, "message": message})

        # Step 1: Intake classification
        intent = self.intake.classify(message)
        log_event("intent_classified", {"intent": intent})

        # Step 2: Route by intent
        if intent == "booking_request":
            result = self.booking.handle(message)
        elif intent == "general_inquiry":
            result = self.intake.respond(message)
        else:
            result = {"response": "I'll have someone follow up with you shortly.", "intent": intent}

        # Step 3: Respond via channel
        if channel == "sms":
            self.sms.send(result["response"])

        log_event("handled", result)
        return result

if __name__ == "__main__":
    orch = Orchestrator()
    # Test run
    print(orch.handle_inbound("Hi, I need my AC unit looked at this week"))
