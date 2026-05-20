"""
Orchard.ai — SMS Agent
Bidirectional SMS via Twilio. Gracefully stubs when Twilio is not configured.

Failure risks: see docs/failure-modes.md → Category 3 (SMS truncation)
"""
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE       = os.getenv("TWILIO_PHONE_NUMBER", "")

SMS_CHAR_LIMIT = 160  # Standard single SMS segment
SAFE_LIMIT     = 155  # Leave 5-char buffer to avoid mid-word splits

_twilio_client = None

def _get_twilio():
    """Lazy-load Twilio client. Returns None if not configured."""
    global _twilio_client
    if _twilio_client:
        return _twilio_client
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE]):
        return None
    if TWILIO_ACCOUNT_SID == "your_sid_here":
        return None
    try:
        from twilio.rest import Client
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        return _twilio_client
    except ImportError:
        return None


def _truncate(text: str, limit: int = SAFE_LIMIT) -> str:
    """
    Truncate at a word boundary, not mid-word.
    Appends ellipsis only if truncation actually occurred.
    """
    if len(text) <= limit:
        return text
    truncated = text[: limit - 3].rsplit(" ", 1)[0]
    return truncated + "..."


class SMSAgent:
    """
    Handles inbound and outbound SMS.

    In stub mode (no Twilio credentials), messages are logged to stdout
    with a [SMS STUB] prefix instead of being sent.
    """

    def __init__(self, default_to: str = None):
        """
        Args:
            default_to: Default destination phone number (E.164 format).
                        Can be overridden per send() call.
        """
        self.default_to = default_to
        self._client = _get_twilio()
        self.stub_mode = self._client is None

    # ── Outbound ───────────────────────────────────────────────────────────────

    def send(self, message: str, to_number: str = None) -> dict:
        """
        Send an outbound SMS. Truncates safely if over the limit.

        Args:
            message:   The text to send.
            to_number: Destination in E.164 format, e.g. "+15550001234".
                       Falls back to self.default_to if not provided.

        Returns:
            {"status": "sent"|"stubbed", "message": str, "sid": str|None}
        """
        to = to_number or self.default_to
        safe_msg = _truncate(message)

        if self.stub_mode:
            print(f"[SMS STUB] → {to or 'NO_NUMBER'}: {safe_msg}")
            return {"status": "stubbed", "message": safe_msg, "sid": None}

        if not to:
            return {"status": "error", "message": safe_msg, "error": "No destination number"}

        try:
            msg = self._client.messages.create(
                body=safe_msg,
                from_=TWILIO_PHONE,
                to=to,
            )
            return {"status": "sent", "message": safe_msg, "sid": msg.sid}
        except Exception as e:
            print(f"[SMS ERROR] Failed to send: {e}")
            return {"status": "error", "message": safe_msg, "error": str(e)}

    def send_multipart(self, message: str, to_number: str = None) -> list:
        """
        Split a long message into multiple SMS segments and send each.
        Use for messages where truncation is unacceptable (e.g. instructions).

        Returns: list of send() results, one per segment.
        """
        segments = self._split_segments(message)
        results = []
        for segment in segments:
            results.append(self.send(segment, to_number))
        return results

    # ── Inbound ────────────────────────────────────────────────────────────────

    def parse_inbound(self, webhook_data: dict) -> dict:
        """
        Parse a Twilio inbound SMS webhook payload.

        Args:
            webhook_data: The raw POST body from Twilio as a dict.

        Returns:
            {"from": str, "body": str, "message_sid": str}
        """
        body = webhook_data.get("Body", "").strip()
        return {
            "from": webhook_data.get("From", ""),
            "body": body,
            "message_sid": webhook_data.get("MessageSid", ""),
            "num_media": int(webhook_data.get("NumMedia", 0)),
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _split_segments(self, text: str, limit: int = SAFE_LIMIT) -> list:
        """Split text into SMS-sized segments at word boundaries."""
        if len(text) <= limit:
            return [text]

        segments = []
        words = text.split()
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= limit:
                current = f"{current} {word}".strip()
            else:
                if current:
                    segments.append(current)
                current = word
        if current:
            segments.append(current)
        return segments

    @property
    def is_live(self) -> bool:
        """True if Twilio is configured and SMS will actually be sent."""
        return not self.stub_mode
