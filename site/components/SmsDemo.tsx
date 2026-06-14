"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { SCRIPT, buildSchedule } from "@/lib/conversation";

export default function SmsDemo() {
  const [visible, setVisible] = useState(0);
  const [typingFor, setTypingFor] = useState<number | null>(null);
  const started = useRef(false);
  const timers = useRef<number[]>([]);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  const play = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setVisible(0);
    setTypingFor(null);

    const cues = buildSchedule(SCRIPT);
    cues.forEach((cue, i) => {
      if (cue.showTypingAt !== null) {
        timers.current.push(
          window.setTimeout(() => setTypingFor(i), cue.showTypingAt)
        );
      }
      timers.current.push(
        window.setTimeout(() => {
          setTypingFor(null);
          setVisible(i + 1);
        }, cue.showMessageAt)
      );
    });
  }, []);

  // Auto-play once when the phone scrolls into view
  useEffect(() => {
    const el = frameRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !started.current) {
          started.current = true;
          play();
          obs.disconnect();
        }
      },
      { threshold: 0.4 }
    );
    obs.observe(el);
    return () => {
      obs.disconnect();
      timers.current.forEach(clearTimeout);
    };
  }, [play]);

  // Keep newest message in view
  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [visible, typingFor]);

  return (
    <div className="phone" ref={frameRef}>
      <div className="phone-header">
        <div className="phone-name">Oakwood Handyman</div>
        <div className="phone-status">Text message · powered by Orchard</div>
      </div>
      <div className="msg-list" ref={listRef}>
        {SCRIPT.slice(0, visible).map((m, i) =>
          m.from === "system" ? (
            <div key={i} className="sysnote">{m.text}</div>
          ) : (
            <div key={i} className={`bubble ${m.from}`}>{m.text}</div>
          )
        )}
        {typingFor !== null && (
          <div
            className={`typing${SCRIPT[typingFor].from === "customer" ? " customer-side" : ""}`}
          >
            <span /><span /><span />
          </div>
        )}
      </div>
    </div>
  );
}
