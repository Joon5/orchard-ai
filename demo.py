#!/usr/bin/env python3
"""
Orchard.ai — End-to-End Demo Runner

Runs a set of test messages through the full pipeline and prints results.
Works in mock mode (no API keys needed) or live mode (set ANTHROPIC_API_KEY in .env).

Usage:
    python demo.py                    # run built-in test suite
    python demo.py "Your message here"  # test a single custom message
"""
import sys
import os
import json

# Add src/ to path so imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from pipelines.orchestrator import Orchestrator
from utils.llm_client import is_mock_mode

# ── Demo configuration ─────────────────────────────────────────────────────────

# Simulated open calendar slots (replace with real calendar integration in prod)
DEMO_AVAILABILITY = [
    "Thursday May 22 at 9am",
    "Friday May 23 at 2pm",
    "Saturday May 24 at 10am",
]

# Test messages covering all five intent categories
TEST_SUITE = [
    # (label, message)
    ("Booking request",      "Hi, I need my AC looked at this week — it's blowing warm air"),
    ("General inquiry",      "How much does an AC tune-up cost?"),
    ("Emergency",            "My furnace stopped working completely and it's freezing in here"),
    ("Complaint + booking",  "Nobody showed up last Tuesday. I still need the repair done."),
    ("Unknown / spam",       "WINNER! Claim your $500 gift card now"),
]

# ── Formatting helpers ─────────────────────────────────────────────────────────

INTENT_COLORS = {
    "booking_request":  "\033[32m",   # green
    "general_inquiry":  "\033[34m",   # blue
    "emergency":        "\033[31m",   # red
    "complaint":        "\033[33m",   # yellow
    "unknown":          "\033[90m",   # grey
    "booking_confirmed":"\033[32m",
}
RESET = "\033[0m"
BOLD  = "\033[1m"

def color(text: str, intent: str) -> str:
    return f"{INTENT_COLORS.get(intent, '')}{text}{RESET}"

def print_header():
    mode = f"{BOLD}MOCK MODE{RESET} (no API key)" if is_mock_mode() else f"{BOLD}LIVE MODE{RESET} (Anthropic API)"
    print(f"\n{'═'*60}")
    print(f"  {BOLD}Orchard.ai — End-to-End Pipeline Demo{RESET}")
    print(f"  Running in: {mode}")
    print(f"  Availability injected: {', '.join(DEMO_AVAILABILITY)}")
    print(f"{'═'*60}\n")

def print_result(label: str, message: str, result: dict, idx: int):
    intent = result.get("intent", "unknown")
    print(f"  {BOLD}[{idx}] {label}{RESET}")
    print(f"  Customer : {message}")
    print(f"  Intent   : {color(intent, intent)}")
    print(f"  Reply    : {result.get('response', '')}")
    if result.get("needs_followup"):
        print(f"  ⚑ Flagged for manual follow-up")
    sms = result.get("sms_result", {})
    if sms:
        status = sms.get("status", "")
        sid    = sms.get("sid") or ""
        suffix = f" | SID: {sid}" if sid else ""
        print(f"  SMS      : [{status.upper()}]{suffix}")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def run_suite():
    """Run the built-in test suite."""
    print_header()
    orch = Orchestrator(availability=DEMO_AVAILABILITY)

    for i, (label, message) in enumerate(TEST_SUITE, 1):
        result = orch.handle_inbound(message, channel="sms")
        print_result(label, message, result, i)

    print(f"{'─'*60}")
    print(f"  {BOLD}All {len(TEST_SUITE)} test messages processed.{RESET}")
    print(f"  Check agent_run.log for full structured event log.\n")


def run_single(message: str):
    """Run a single custom message through the pipeline."""
    print_header()
    orch = Orchestrator(availability=DEMO_AVAILABILITY)
    result = orch.handle_inbound(message, channel="sms")
    print_result("Custom message", message, result, 1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_single(" ".join(sys.argv[1:]))
    else:
        run_suite()
