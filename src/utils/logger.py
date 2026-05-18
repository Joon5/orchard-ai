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
