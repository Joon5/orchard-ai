"use client";

import { useState } from "react";

interface Booking {
  name: string;
  service: string;
  day: string;
  window: string;
}

export default function DemoBookingForm() {
  const [booking, setBooking] = useState<Booking | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBooking({
      name: String(data.get("name") || "there"),
      service: String(data.get("service")),
      day: String(data.get("day")),
      window: String(data.get("window")),
    });
  }

  if (booking) {
    return (
      <div className="confirm-panel">
        <h2>Request received, {booking.name}!</h2>
        <p>
          <strong>{booking.service}</strong>, {booking.day}, {booking.window}
        </p>
        <p>
          Mike just got a text with your request. You&apos;ll get a confirmation
          text the moment he taps approve.
        </p>
        <p style={{ fontSize: "13.5px", color: "var(--ink-soft)" }}>
          This is a simulation, so no real booking was made. Your business gets
          this exact flow, live.
        </p>
      </div>
    );
  }

  return (
    <form className="book-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label htmlFor="name">Your name</label>
        <input id="name" name="name" required placeholder="Jane Smith" />
      </div>
      <div className="form-row">
        <label htmlFor="phone">Mobile number</label>
        <input
          id="phone"
          name="phone"
          type="tel"
          required
          placeholder="(310) 555-0123"
        />
      </div>
      <div className="form-row">
        <label htmlFor="service">What do you need?</label>
        <select id="service" name="service" required defaultValue="">
          <option value="" disabled>Choose a service…</option>
          <option>Plumbing repair</option>
          <option>Electrical fix</option>
          <option>Doors & drywall</option>
          <option>Gutter cleaning</option>
          <option>Furniture assembly</option>
          <option>Something else</option>
        </select>
      </div>
      <div className="form-row">
        <label htmlFor="day">Preferred day</label>
        <select id="day" name="day" required defaultValue="">
          <option value="" disabled>Choose a day…</option>
          <option>Thursday</option>
          <option>Friday</option>
          <option>Saturday</option>
        </select>
      </div>
      <div className="form-row">
        <label htmlFor="window">Time window</label>
        <select id="window" name="window" required defaultValue="">
          <option value="" disabled>Choose a window…</option>
          <option>9–11 AM</option>
          <option>11 AM–1 PM</option>
          <option>2–4 PM</option>
        </select>
      </div>
      <div className="form-row">
        <label htmlFor="notes">Anything we should know? (optional)</label>
        <textarea id="notes" name="notes" placeholder="Leaking under the kitchen sink…" />
      </div>
      <button className="btn btn-primary" type="submit">
        Request this time
      </button>
    </form>
  );
}
