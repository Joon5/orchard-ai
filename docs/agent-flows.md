# Orchard.ai — Agent Flow Diagrams

Detailed flow descriptions for each agent in the pipeline.

---

## Flow 1: New Booking Request (Happy Path)

```
Customer: "Hi, I need my AC looked at this week"
    │
    ▼
Orchestrator.handle_inbound(message, channel="sms")
    │
    ├─► IntakeAgent.classify(message)
    │       └─► LLM call: "booking_request"
    │
    ├─► BookingAgent.handle(message)
    │       └─► LLM call (with availability context if injected)
    │           └─► "We have openings Thursday 9am or Friday 2pm. Which works?"
    │
    └─► SMSAgent.send("We have openings Thursday...") ──► Customer receives SMS
```

**Logged events**: `inbound`, `intent_classified`, `handled`

---

## Flow 2: General Inquiry

```
Customer: "How much do you charge for a tune-up?"
    │
    ▼
Orchestrator.handle_inbound(message)
    │
    ├─► IntakeAgent.classify → "general_inquiry"
    │
    ├─► IntakeAgent.respond(message)
    │       └─► LLM call → "Tune-ups start at $89. Want to book one?"
    │
    └─► SMSAgent.send(...) ──► Customer
```

---

## Flow 3: Complaint (Edge Case)

```
Customer: "I called last week and nobody showed up"
    │
    ▼
IntakeAgent.classify → "complaint"  (risk: misclassified as "general_inquiry")
    │
    ▼
Orchestrator fallback: "I'll have someone follow up with you shortly."
    │
    ▼
SMSAgent.send(...) ──► Customer
```

**Failure risk**: FC-001 — multi-intent complaint with booking signal gets routed to fallback.
**Mitigation (planned)**: Secondary intent check if primary is `complaint`.

---

## Flow 4: Handoff with Context Preservation

Used when a conversation spans multiple turns (e.g., intake → booking with prior context).

```
HandoffManager.create_packet(
    source="intake", target="booking",
    intent="booking_request",
    message=original_message,
    history=[...prior turns...]
)
    │
    ▼
HandoffManager.summarize_for_prompt(packet)
    │   → "[Handoff from intake → booking]\nIntent: booking_request\n..."
    ▼
BookingAgent.handle(summarized_context)
```

**Failure risk**: FC — handoff state loss when conversation_history grows beyond context window.
**Mitigation**: Capped at last 4 turns in `summarize_for_prompt`.

---

## Event Log Schema

Every `log_event()` call produces:

```json
{
  "timestamp": "2025-01-15T10:23:45.123456",
  "event": "intent_classified",
  "data": {
    "intent": "booking_request"
  }
}
```

Events: `inbound`, `intent_classified`, `handled`, `sms_sent`, `error`
