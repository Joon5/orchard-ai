"""
Unit tests for the Orchard.ai Orchestrator.
Uses mocking to isolate agent behavior from live LLM calls.
"""
import unittest
from unittest.mock import MagicMock, patch

from pipelines.orchestrator import Orchestrator


class TestOrchestrator(unittest.TestCase):

    def _make_orchestrator(self, intent: str, agent_response: str) -> Orchestrator:
        """Helper: build an Orchestrator with mocked agents."""
        orch = Orchestrator.__new__(Orchestrator)
        orch.intake = MagicMock()
        orch.booking = MagicMock()
        orch.sms = MagicMock()

        orch.intake.classify.return_value = intent
        orch.intake.respond.return_value = {"response": agent_response, "intent": "general_inquiry"}
        orch.booking.handle.return_value = {"response": agent_response, "intent": "booking_request"}
        orch.sms.send.return_value = {"status": "stubbed"}
        return orch

    def test_booking_request_routes_to_booking_agent(self):
        orch = self._make_orchestrator("booking_request", "We'll see you Thursday at 9am!")
        result = orch.handle_inbound("I need my AC looked at this week")
        orch.booking.handle.assert_called_once()
        orch.intake.respond.assert_not_called()
        self.assertEqual(result["intent"], "booking_request")

    def test_general_inquiry_routes_to_intake_agent(self):
        orch = self._make_orchestrator("general_inquiry", "Tune-ups start at $89.")
        result = orch.handle_inbound("How much do you charge?")
        orch.intake.respond.assert_called_once()
        orch.booking.handle.assert_not_called()
        self.assertEqual(result["intent"], "general_inquiry")

    def test_unknown_intent_returns_fallback(self):
        orch = self._make_orchestrator("unknown", "")
        result = orch.handle_inbound("qwertyuiop")
        self.assertIn("follow up", result["response"])

    def test_sms_send_called_on_sms_channel(self):
        orch = self._make_orchestrator("booking_request", "See you Thursday!")
        orch.handle_inbound("Book me in", channel="sms")
        orch.sms.send.assert_called_once()

    def test_sms_not_sent_on_non_sms_channel(self):
        orch = self._make_orchestrator("booking_request", "See you Thursday!")
        orch.handle_inbound("Book me in", channel="web")
        orch.sms.send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
