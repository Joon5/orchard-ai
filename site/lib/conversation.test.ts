import { describe, it, expect } from "vitest";
import { SCRIPT, buildSchedule } from "./conversation";

describe("SCRIPT", () => {
  it("starts with a missed-call system note and ends with an owner-confirm note", () => {
    expect(SCRIPT[0].from).toBe("system");
    expect(SCRIPT[0].text.toLowerCase()).toContain("missed call");
    expect(SCRIPT[SCRIPT.length - 1].from).toBe("system");
  });

  it("system entries never have a typing duration", () => {
    for (const entry of SCRIPT.filter((e) => e.from === "system")) {
      expect(entry.typingMs).toBe(0);
    }
  });
});

describe("buildSchedule", () => {
  it("produces strictly increasing message times", () => {
    const cues = buildSchedule(SCRIPT);
    for (let i = 1; i < cues.length; i++) {
      expect(cues[i].showMessageAt).toBeGreaterThan(cues[i - 1].showMessageAt);
    }
  });

  it("shows typing exactly typingMs before the message, or not at all", () => {
    const cues = buildSchedule(SCRIPT);
    cues.forEach((cue, i) => {
      if (SCRIPT[i].typingMs > 0) {
        expect(cue.showTypingAt).toBe(cue.showMessageAt - SCRIPT[i].typingMs);
      } else {
        expect(cue.showTypingAt).toBeNull();
      }
    });
  });

  it("first message appears after its delayBefore + typingMs", () => {
    const cues = buildSchedule(SCRIPT);
    expect(cues[0].showMessageAt).toBe(SCRIPT[0].delayBefore + SCRIPT[0].typingMs);
  });

  it("total runtime is between 15 and 35 seconds (spec: ~30s)", () => {
    const cues = buildSchedule(SCRIPT);
    const total = cues[cues.length - 1].showMessageAt;
    expect(total).toBeGreaterThan(15_000);
    expect(total).toBeLessThan(35_000);
  });
});
