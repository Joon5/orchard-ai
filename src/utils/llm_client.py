"""
Orchard.ai — LLM Client
Shared wrapper for all Anthropic API calls.
Auto-detects missing API key and falls back to mock mode for local testing.
"""
import os
import random
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MOCK_MODE = not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your_key_here"

if not MOCK_MODE:
    import anthropic
    _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    _client = None

# ── Mock response banks ────────────────────────────────────────────────────────

_MOCK_BOOKING_RESPONSES = [
    "Thanks! We have openings Thursday 9am or Friday 2pm. Which works for you?",
    "Got it — we can come out Wednesday morning or Saturday afternoon. Any preference?",
    "We're available Tuesday 10am or Thursday 3pm. Want me to lock one in?",
]

_MOCK_INQUIRY_RESPONSES = [
    "HVAC tune-ups start at $89. Repairs are quoted on-site. Want to schedule a visit?",
    "We serve the area Mon-Sat, 8am-6pm. Emergency calls available 24/7. How can I help?",
    "Most AC repairs run $150-$350 depending on the issue. Free diagnosis with any repair. Book now?",
]


def _mock_classify(message: str) -> str:
    """
    Priority-ordered intent classifier for mock mode.

    Strategy:
      1. Spam / emergency / complaint checked first (high-signal phrases)
      2. ACTION verbs → booking_request
      3. QUESTION phrases → general_inquiry
      4. Multi-intent (action + question) → booking_request (per spec)
    """
    msg = message.lower()

    SPAM_KW = [
        "winner", "gift card", "prize", "click here", "free money",
        "congratulations", "claim your",
    ]
    EMERGENCY_KW = [
        "no heat", "no ac", "it's freezing", "its freezing", "freezing in here",
        "stopped working completely", "not working at all", "gas smell",
        "carbon monoxide", "flooding", "emergency", "urgent",
    ]
    COMPLAINT_KW = [
        "nobody showed", "didn't show", "never came", "no one came",
        "still broken", "never arrived", "missed my appointment",
    ]
    # Clear action verbs — unambiguously "I want service" (service NAMES removed)
    BOOKING_KW = [
        "book", "schedule an", "make an appointment", "set up an appointment",
        "come out", "come by", "come fix", "come tomorrow", "come today",
        "come this week", "come next week", "need you to come",
        "need someone to come", "fix my", "repair my", "install a", "install my",
        "replace my", "look at my", "looked at my", "reschedule",
        "want to schedule", "want to book", "need a repair", "need an inspection",
        "send someone", "send a tech",
    ]
    # Clear question phrases — unambiguously "I want information"
    INQUIRY_KW = [
        "how much", "how long does", "what do you charge", "what's the cost",
        "what is the cost", "what is the price", "what's your rate",
        "do you charge", "what are your hours", "what time do you",
        "when do you open", "are you open", "do you offer", "do you cover",
        "are you licensed", "do you have warranty", "what services do you",
        "how soon can", "how fast",
    ]

    for kw in SPAM_KW:
        if kw in msg:
            return "unknown"
    for kw in EMERGENCY_KW:
        if kw in msg:
            return "emergency"

    has_complaint = any(kw in msg for kw in COMPLAINT_KW)
    has_booking   = any(kw in msg for kw in BOOKING_KW)
    has_inquiry   = any(kw in msg for kw in INQUIRY_KW)

    if has_complaint:
        return "booking_request" if has_booking else "complaint"

    # Multi-intent: action + question → booking wins (per spec)
    if has_booking:
        return "booking_request"
    if has_inquiry:
        return "general_inquiry"

    # Softer action fallback: "I need my X looked at", "I need help with"
    SOFT_ACTION = [
        "i need my", "we need our", "need my", "need help with my",
        "need someone", "need a technician", "need a tech",
    ]
    if any(kw in msg for kw in SOFT_ACTION):
        return "booking_request"

    # Softer question fallback: standalone price/cost/hours words
    SOFT_INQUIRY = ["price", "cost", "rates", "hours", "available"]
    if any(kw in msg for kw in SOFT_INQUIRY):
        return "general_inquiry"

    return "unknown"


def _mock_response(system_prompt: str, user_message: str) -> str:
    """Return a realistic fake response based on keyword matching."""
    sys_lower = system_prompt.lower()

    # Classification requests
    if any(kw in sys_lower for kw in ["classify", "intent", "label"]):
        return _mock_classify(user_message)

    # Booking / scheduling responses
    if any(kw in sys_lower for kw in ["schedul", "booking", "appointment", "slot"]):
        return random.choice(_MOCK_BOOKING_RESPONSES)

    # General inquiry responses
    return random.choice(_MOCK_INQUIRY_RESPONSES)


# ── Public API ─────────────────────────────────────────────────────────────────

def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 256,
) -> str:
    """
    Call Claude or return a mock response if no API key is set.

    Args:
        system_prompt: The system instruction for Claude.
        user_message:  The user/customer message.
        model:         Claude model string.
        max_tokens:    Max tokens for the response.

    Returns:
        Response text (str).
    """
    if MOCK_MODE:
        return _mock_response(system_prompt, user_message)

    response = _client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()


def is_mock_mode() -> bool:
    """Returns True if running without a real API key."""
    return MOCK_MODE
