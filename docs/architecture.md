# Orchard.ai — System Architecture

## Overview

Orchard.ai is a multi-agent LLM pipeline designed for solo tradespeople. The system handles the full customer communication lifecycle: inbound inquiry → classification → booking → confirmation → follow-up.

## Component Map

```
Customer (SMS / Web)
        │
        ▼
   [SMS Agent]  ←── inbound Twilio webhook
        │
        ▼
  [Orchestrator]  ── central router
     │       │
     ▼       ▼
[Intake]  [Booking]
 Agent     Agent
     │       │
     └───────┘
         │
         ▼
   [SMS Agent]  ──► outbound reply to customer
```

## Agents

### Intake Agent (`src/agents/intake_agent.py`)
- **Role**: First-touch classifier
- **Input**: Raw customer message string
- **Output**: Intent label (`booking_request`, `general_inquiry`, `complaint`, `emergency`, `unknown`)
- **Model call**: Single classification prompt → one-word output
- **Key risk**: Intent misclassification on ambiguous or multi-intent messages (see failure-modes.md #1)

### Booking Agent (`src/agents/booking_agent.py`)
- **Role**: Scheduling + confirmation logic
- **Input**: Customer message + optional availability context
- **Output**: Confirmation or proposal text (<160 chars)
- **Key risk**: Hallucinating unavailable time slots when calendar context is absent (see failure-modes.md #2)

### SMS Agent (`src/agents/sms_agent.py`)
- **Role**: Twilio I/O layer
- **Input**: Outbound message string + destination number
- **Output**: Sent SMS, or stubbed log if Twilio not configured
- **Key risk**: Response truncation at 160-char SMS limit (see failure-modes.md #3)

## Orchestrator (`src/pipelines/orchestrator.py`)
Single entry point (`handle_inbound`). Receives a message + channel, runs the intake → route → respond loop, logs all events via `logger.py`.

## Handoff Manager (`src/pipelines/handoff.py`)
Packages context into `HandoffPacket` structs to prevent state loss when passing between agents. See failure-modes.md #4.

## Data Flow
1. Customer texts or submits booking form
2. Twilio webhook fires → `SMSAgent.parse_inbound()` → `Orchestrator.handle_inbound()`
3. `IntakeAgent.classify()` returns intent
4. Orchestrator routes to `BookingAgent` or `IntakeAgent.respond()`
5. Response returned to `SMSAgent.send()` → customer receives confirmation

## External Integrations
| Service | Purpose | Config |
|---|---|---|
| Anthropic API | LLM inference for all agents | `ANTHROPIC_API_KEY` |
| Twilio | SMS inbound/outbound | `TWILIO_*` env vars |
| Calendar (TBD) | Availability context injection | Phase 2 |
| FastAPI (TBD) | HTTP endpoint for booking form | Phase 2 |
