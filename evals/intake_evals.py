"""
Eval harness for the Intake Agent.
Tests intent classification accuracy across edge cases.
"""
import sys
sys.path.insert(0, "../src")

from agents.intake_agent import IntakeAgent

TEST_CASES = [
    {
        "input": "Hi I need someone to come look at my AC",
        "expected_intent": "booking_request",
        "failure_mode": None
    },
    {
        "input": "How much do you charge?",
        "expected_intent": "general_inquiry",
        "failure_mode": None
    },
    {
        "input": "I called last week and nobody showed up",
        "expected_intent": "complaint",
        "failure_mode": "intent_misclassification"  # watch for this
    },
    {
        "input": "Can you come tomorrow and also what's the price",
        "expected_intent": "booking_request",  # multi-intent — booking takes priority
        "failure_mode": "multi_intent_ambiguity"
    },
]

def run_evals():
    agent = IntakeAgent()
    passed = 0
    failed = []

    for case in TEST_CASES:
        result = agent.classify(case["input"])
        if result == case["expected_intent"]:
            passed += 1
            print(f"  PASS: '{case['input'][:50]}...' → {result}")
        else:
            failed.append({**case, "got": result})
            print(f"  FAIL: '{case['input'][:50]}...' → got {result}, expected {case['expected_intent']}")

    print(f"\nResults: {passed}/{len(TEST_CASES)} passed")
    if failed:
        print("Failed cases:", failed)

if __name__ == "__main__":
    run_evals()
