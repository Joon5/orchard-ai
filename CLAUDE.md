# CLAUDE.md — Orchard.ai GitHub Repository Setup

## Your Goal
Create, scaffold, and push a new GitHub repository called `orchard-ai` for the Orchard.ai project — an AI-powered agentic platform for solo tradespeople (HVAC, plumbing, electrical). Handle every step autonomously. Do not ask for confirmation between steps unless a hard error occurs.

---

## Step 1: Verify Prerequisites

```bash
gh --version
git --version
gh auth status
```

- If `gh` is not installed: `brew install gh` (Mac) or `sudo apt install gh` (Linux)
- If not authenticated: run `gh auth login` and complete the browser OAuth flow before continuing
- Do not proceed past Step 1 until `gh auth status` confirms you are logged in

---

## Step 2: Create and Enter Project Directory

```bash
mkdir -p ~/projects/orchard-ai
cd ~/projects/orchard-ai
git init
```

---

## Step 3: Scaffold the Project Structure

Create the following files and directories exactly as specified:

```
orchard-ai/
├── README.md
├── .gitignore
├── .env.example
├── CLAUDE.md              ← this file, copy it in
├── docs/
│   ├── architecture.md
│   ├── agent-flows.md
│   └── failure-modes.md
├── src/
│   ├── agents/
│   │   ├── intake_agent.py        ← AI customer intake handler
│   │   ├── booking_agent.py       ← scheduling + confirmation logic
│   │   └── sms_agent.py           ← SMS pipeline (inbound + outbound)
│   ├── pipelines/
│   │   ├── orchestrator.py        ← multi-agent coordinator
│   │   └── handoff.py             ← agent-to-agent task passing
│   ├── web/
│   │   ├── landing.html           ← tradesperson web presence template
│   │   └── booking_form.html      ← embeddable booking widget
│   └── utils/
│       ├── llm_client.py          ← shared Anthropic API wrapper
│       └── logger.py              ← structured logging for agent runs
├── evals/
│   ├── README.md                  ← evaluation methodology
│   ├── intake_evals.py            ← test cases for intake agent
│   └── failure_cases/
│       └── edge_cases.json        ← documented failure modes + inputs
├── tests/
│   └── test_orchestrator.py
└── requirements.txt
```

### File Contents to Create

**README.md**
```markdown
# Orchard.ai

AI-powered agentic platform for solo tradespeople. Handles customer intake,
booking, and SMS communication through orchestrated LLM pipelines.

## Architecture
Multi-agent system with a central orchestrator routing tasks between:
- Intake Agent: classifies and handles inbound customer inquiries
- Booking Agent: manages scheduling, confirmations, and calendar logic
- SMS Agent: handles bidirectional SMS communication

## Setup
1. Copy `.env.example` to `.env` and add your API keys
2. `pip install -r requirements.txt`
3. `python src/agents/orchestrator.py`

## Research Notes
See `docs/failure-modes.md` for documented agent failure cases and
`evals/` for evaluation harnesses.

## Status
Active development — v0.1 (agentic pipeline scaffolding)
```

**.gitignore**
```
.env
__pycache__/
*.pyc
.DS_Store
*.log
.venv/
node_modules/
```

**.env.example**
```
ANTHROPIC_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
```

**requirements.txt**
```
anthropic>=0.25.0
twilio>=8.0.0
python-dotenv>=1.0.0
fastapi>=0.110.0
uvicorn>=0.29.0
pydantic>=2.0.0
```

**src/utils/llm_client.py**
```python
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def call_claude(system_prompt: str, user_message: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Shared wrapper for all agent LLM calls."""
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text
```

**src/pipelines/orchestrator.py**
```python
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
```

**src/utils/logger.py**
```python
import json
import datetime

def log_event(event_type: str, data: dict):
    """Structured logger for agent pipeline events. Used for failure analysis."""
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event": event_type,
        "data": data
    }
    print(json.dumps(entry))
    # TODO: write to log file for failure mode analysis
    with open("agent_run.log", "a") as f:
        f.write(json.dumps(entry) + "\n")
```

**docs/failure-modes.md**
```markdown
# Agent Failure Modes — Research Log

This document tracks observed failure cases in the Orchard.ai agentic pipeline.
Used to identify systematic weaknesses in multi-agent LLM orchestration.

## Taxonomy

### Category 1: Intent Misclassification
- Description: Intake agent routes message to wrong downstream agent
- Trigger conditions: Ambiguous phrasing, multi-intent messages
- Observed frequency: TBD
- Mitigation: TBD

### Category 2: Booking Hallucination
- Description: Booking agent confirms unavailable time slots
- Trigger conditions: Calendar context not injected into prompt
- Observed frequency: TBD
- Mitigation: TBD

### Category 3: SMS Truncation
- Description: Agent response exceeds SMS character limit, gets cut off mid-sentence
- Trigger conditions: Complex responses, multi-step instructions
- Observed frequency: TBD
- Mitigation: TBD

### Category 4: Handoff State Loss
- Description: Context from intake agent not preserved when passed to booking agent
- Trigger conditions: Long conversation threads, context window limits
- Observed frequency: TBD
- Mitigation: TBD

## Log Format
Date | Category | Input | Agent Output | Expected Output | Root Cause
```

**evals/README.md**
```markdown
# Orchard.ai Evaluation Harness

Structured evals for each agent in the pipeline.

## Running Evals
```bash
python evals/intake_evals.py
```

## Methodology
Each eval case specifies:
- input: the raw customer message
- expected_intent: correct classification
- expected_response_contains: keywords that should appear in output
- failure_mode: which failure category this tests (see docs/failure-modes.md)
```

**evals/intake_evals.py**
```python
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
```

**evals/failure_cases/edge_cases.json**
```json
[
  {
    "id": "FC-001",
    "category": "intent_misclassification",
    "input": "I called last week and nobody showed up, I need to reschedule",
    "agent": "intake",
    "observed_output": "general_inquiry",
    "expected_output": "complaint + booking_request",
    "notes": "Multi-intent message with complaint framing causes intake agent to miss booking signal"
  },
  {
    "id": "FC-002",
    "category": "booking_hallucination",
    "input": "Can you come this Saturday at 2pm?",
    "agent": "booking",
    "observed_output": "Confirmed for Saturday at 2pm",
    "expected_output": "Check availability before confirming",
    "notes": "Booking agent confirms without calendar context — classic hallucination failure"
  }
]
```

---

## Step 4: Stage and Commit All Files

```bash
cd ~/projects/orchard-ai
git add .
git commit -m "feat: initial scaffold — Orchard.ai agentic stack v0.1

- Multi-agent orchestration pipeline (intake, booking, SMS)
- Structured logging for failure mode research
- Eval harness with edge case test suite
- Documented failure taxonomy (docs/failure-modes.md)"
```

---

## Step 5: Create GitHub Repo and Push

```bash
gh repo create orchard-ai \
  --public \
  --description "AI-powered agentic platform for solo tradespeople — intake, booking, and SMS orchestration" \
  --source=. \
  --remote=origin \
  --push
```

If the repo name is already taken on your account, use `orchard-ai-app` or `orchard-platform`.

---

## Step 6: Verify and Report

```bash
gh repo view orchard-ai --web
```

Open the repo in the browser and confirm:
- All files are present
- README renders correctly
- The commit message is visible

Report back the repo URL when complete.

---

## Error Handling

| Error | Fix |
|---|---|
| `gh: command not found` | Install GitHub CLI first |
| `auth required` | Run `gh auth login` |
| `repo already exists` | Use `--name orchard-ai-2026` flag |
| `git: not a repository` | Re-run `git init` from the project directory |
| Any Python import error | These are scaffolded stubs — imports will fail until agent files are filled in, which is expected |
