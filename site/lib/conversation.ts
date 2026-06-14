export type Sender = "system" | "orchard" | "customer";

export interface ScriptEntry {
  from: Sender;
  text: string;
  /** ms of silence before this entry's typing (or message, if no typing) begins */
  delayBefore: number;
  /** ms the typing indicator shows before the message lands; 0 = no indicator */
  typingMs: number;
}

export interface Cue {
  showTypingAt: number | null;
  showMessageAt: number;
}

export const SCRIPT: ScriptEntry[] = [
  {
    from: "system",
    text: "Missed call from (310) 555-0182 · 2:47 PM",
    delayBefore: 600,
    typingMs: 0,
  },
  {
    from: "orchard",
    text: "Hi, this is Oakwood Handyman! Sorry we missed your call — we're on a job right now. How can we help?",
    delayBefore: 1600,
    typingMs: 1100,
  },
  {
    from: "customer",
    text: "My garbage disposal is leaking under the sink",
    delayBefore: 1800,
    typingMs: 1300,
  },
  {
    from: "orchard",
    text: "We can fix that. We have Thursday 9–11 AM or Friday 2–4 PM open. Which works better?",
    delayBefore: 1400,
    typingMs: 1400,
  },
  {
    from: "customer",
    text: "Thursday morning works",
    delayBefore: 1500,
    typingMs: 1000,
  },
  {
    from: "orchard",
    text: "You're booked for Thursday 9–11 AM. We'll text you a reminder the day before. Anything else?",
    delayBefore: 1800,
    typingMs: 1400,
  },
  {
    from: "system",
    text: "Mike confirmed the job with one tap, without leaving the work he was on.",
    delayBefore: 1700,
    typingMs: 0,
  },
];

export function buildSchedule(script: ScriptEntry[]): Cue[] {
  let t = 0;
  return script.map((entry) => {
    t += entry.delayBefore;
    const showTypingAt = entry.typingMs > 0 ? t : null;
    t += entry.typingMs;
    return { showTypingAt, showMessageAt: t };
  });
}
