"use client";

import { useEffect, useRef, useState } from "react";

/** Wraps a block so it fades up the first time it scrolls into view. */
export default function Reveal({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setShown(true);
          obs.disconnect();
        }
      },
      // Fire once the block reaches the middle of the viewport, not as it enters
      { threshold: 0, rootMargin: "0px 0px -45% 0px" }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={ref} className={`reveal${shown ? " in" : ""}`}>
      {children}
    </div>
  );
}
