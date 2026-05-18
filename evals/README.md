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
