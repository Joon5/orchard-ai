"""
Orchard.ai — Intake Agent Eval Harness
Tests intent classification accuracy across edge cases.

Works in both mock mode (no API key) and live mode (with ANTHROPIC_API_KEY).
Run from project root: python evals/intake_evals.py

In mock mode, classification is keyword-based — results indicate structural
correctness but not LLM accuracy. Run with a real key for meaningful evals.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.intake_agent import IntakeAgent
from utils.llm_client import is_mock_mode

# ── Test cases ─────────────────────────────────────────────────────────────────
# Each case: input, expected_intent, failure_mode (None if happy path)

TEST_CASES = [
    # ── Happy path ─────────────────────────────────────────────────────────────
    {
        "input": "Hi I need someone to come look at my AC",
        "expected_intent": "booking_request",
        "failure_mode": None,
        "description": "Standard booking request",
    },
    {
        "input": "I want to schedule a furnace tune-up",
        "expected_intent": "booking_request",
        "failure_mode": None,
        "description": "Explicit scheduling request",
    },
    {
        "input": "How much do you charge for a tune-up?",
        "expected_intent": "general_inquiry",
        "failure_mode": None,
        "description": "Price inquiry",
    },
    {
        "input": "What are your hours?",
        "expected_intent": "general_inquiry",
        "failure_mode": None,
        "description": "Hours inquiry",
    },

    # ── Emergency ──────────────────────────────────────────────────────────────
    {
        "input": "My furnace stopped working and it's freezing in here",
        "expected_intent": "emergency",
        "failure_mode": None,
        "description": "Clear emergency — furnace failure + freezing",
    },
    {
        "input": "There's no heat in my house, it's an emergency",
        "expected_intent": "emergency",
        "failure_mode": None,
        "description": "Explicit emergency keyword",
    },

    # ── Complaint ──────────────────────────────────────────────────────────────
    {
        "input": "I called last week and nobody showed up",
        "expected_intent": "complaint",
        "failure_mode": "intent_misclassification",
        "description": "Pure complaint — no rebooking signal",
    },

    # ── Edge cases (failure mode territory) ───────────────────────────────────
    {
        "input": "Can you come tomorrow and also what's the price",
        "expected_intent": "booking_request",
        "failure_mode": "multi_intent_ambiguity",
        "description": "Multi-intent: booking takes priority over inquiry",
    },
    {
        "input": "I called last week and nobody showed up, I need to reschedule",
        "expected_intent": "booking_request",
        "failure_mode": "multi_intent_complaint_booking",
        "description": "Complaint + booking signal → booking_request per spec",
    },
    {
        "input": "WINNER! Claim your $500 gift card now",
        "expected_intent": "unknown",
        "failure_mode": None,
        "description": "Spam / irrelevant message",
    },
]

# ── Runner ─────────────────────────────────────────────────────────────────────

PASS = "\033[32m✓ PASS\033[0m"
FAIL = "\033[31m✗ FAIL\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_evals(verbose: bool = True) -> dict:
    agent = IntakeAgent()
    mode_label = "MOCK" if is_mock_mode() else "LIVE (Anthropic API)"

    if verbose:
        print(f"\n{BOLD}Orchard.ai — Intake Agent Evals{RESET}")
        print(f"Mode: {mode_label}")
        print(f"Cases: {len(TEST_CASES)}\n")

    passed = 0
    failed = []

    for i, case in enumerate(TEST_CASES, 1):
        result = agent.classify(case["input"])
        ok = result == case["expected_intent"]

        if ok:
            passed += 1
            if verbose:
                label = f"[edge: {case['failure_mode']}]" if case["failure_mode"] else ""
                print(f"  {PASS} [{i:02d}] {case['description']} {label}")
        else:
            failed.append({**case, "got": result})
            if verbose:
                print(
                    f"  {FAIL} [{i:02d}] {case['description']}\n"
                    f"         input:    {case['input'][:60]}\n"
                    f"         expected: {case['expected_intent']}\n"
                    f"         got:      {result}"
                )

    total = len(TEST_CASES)
    pct   = int(passed / total * 100)

    if verbose:
        print(f"\n{BOLD}Results: {passed}/{total} passed ({pct}%){RESET}")
        if failed:
            edge = [c for c in failed if c.get("failure_mode")]
            if edge:
                print(f"Note: {len(edge)} failure(s) in known edge-case categories")
        if is_mock_mode():
            print(
                "\n⚠  Running in mock mode — set ANTHROPIC_API_KEY in .env "
                "for real LLM accuracy scores."
            )
        print()

    return {"passed": passed, "failed": len(failed), "total": total, "pct": pct}


if __name__ == "__main__":
    results = run_evals(verbose=True)
    sys.exit(0 if results["failed"] == 0 else 1)
