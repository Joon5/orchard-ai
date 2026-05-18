"""
Orchard.ai — Agent Handoff
Packages context from one agent and passes it cleanly to another.
Addresses failure mode: Handoff State Loss (see docs/failure-modes.md #4).
"""
from dataclasses import dataclass, field
from typing import Any, Optional
import datetime


@dataclass
class HandoffPacket:
    """Structured context bundle passed between agents."""
    source_agent: str
    target_agent: str
    intent: str
    original_message: str
    extracted_data: dict = field(default_factory=dict)
    conversation_history: list = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class HandoffManager:
    """Manages context-preserving handoffs between agents."""

    def create_packet(
        self,
        source: str,
        target: str,
        intent: str,
        message: str,
        history: list = None,
        data: dict = None,
    ) -> HandoffPacket:
        """Build a handoff packet with all context needed by the target agent."""
        return HandoffPacket(
            source_agent=source,
            target_agent=target,
            intent=intent,
            original_message=message,
            conversation_history=history or [],
            extracted_data=data or {},
        )

    def summarize_for_prompt(self, packet: HandoffPacket) -> str:
        """Convert a handoff packet into a context string for LLM injection."""
        lines = [
            f"[Handoff from {packet.source_agent} → {packet.target_agent}]",
            f"Intent: {packet.intent}",
            f"Original message: {packet.original_message}",
        ]
        if packet.extracted_data:
            lines.append(f"Extracted data: {packet.extracted_data}")
        if packet.conversation_history:
            lines.append("Prior conversation:")
            for turn in packet.conversation_history[-4:]:  # last 4 turns max
                lines.append(f"  {turn['role']}: {turn['content']}")
        return "\n".join(lines)
