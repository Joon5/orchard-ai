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
3. `python src/pipelines/orchestrator.py`

## Research Notes
See `docs/failure-modes.md` for documented agent failure cases and
`evals/` for evaluation harnesses.

## Status
Active development — v0.1 (agentic pipeline scaffolding)
