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
