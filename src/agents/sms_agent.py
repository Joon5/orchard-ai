"""
Orchard.ai — SMS Agent
Handles inbound and outbound SMS via Twilio.
"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from twilio.rest import Client as TwilioClient
    _twilio_available = True
except ImportError:
    _twilio_available = False


class SMSAgent:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.client = TwilioClient(self.account_sid, self.auth_token) if _twilio_available else None

    def send(self, message: str, to_number: str = None) -> dict:
        """Send an outbound SMS. Truncates to 160 chars if needed."""
        if len(message) > 160:
            message = message[:157] + "..."

        if not self.client:
            # Stub: log instead of sending (Twilio not installed)
            print(f"[SMS STUB] To: {to_number} | Message: {message}")
            return {"status": "stubbed", "message": message}

        msg = self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=to_number
        )
        return {"status": "sent", "sid": msg.sid, "message": message}

    def parse_inbound(self, webhook_data: dict) -> dict:
        """Parse an inbound Twilio SMS webhook payload."""
        return {
            "from": webhook_data.get("From"),
            "body": webhook_data.get("Body", "").strip(),
            "message_sid": webhook_data.get("MessageSid"),
        }
