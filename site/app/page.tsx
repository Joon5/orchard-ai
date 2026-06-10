import Link from "next/link";
import SmsDemo from "@/components/SmsDemo";
import Reveal from "@/components/Reveal";

const TEL = "tel:+14244018308";
const SMS = "sms:+14244018308";

const FEATURES = [
  {
    ico: "🌐",
    title: "A professional website",
    desc: "Three pages with online booking — built and maintained for you.",
  },
  {
    ico: "📞",
    title: "A business number",
    desc: "A dedicated line for your business. Keep your personal number personal.",
  },
  {
    ico: "💬",
    title: "Automatic texting",
    desc: "Missed calls get an instant text back. Customers book by reply.",
  },
  {
    ico: "📅",
    title: "A booking calendar",
    desc: "Jobs land on your Google Calendar. Reminders go out automatically.",
  },
  {
    ico: "✅",
    title: "An owner dashboard",
    desc: "See every job in one place and approve with one tap. Nothing books without you.",
  },
];

function Wordmark() {
  return (
    <span className="wordmark">
      orchard<span className="dot">.</span><span className="ai">ai</span>
    </span>
  );
}

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <div className="bar">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="logo-mark" src="/logo.svg" alt="" aria-hidden="true" />
          <Wordmark />
          <a className="header-cta" href={SMS}>Text me</a>
        </div>
      </header>

      <div className="wrap">
        <section className="hero">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="hero-logo" src="/logo.svg" alt="Orchard logo" />
          <h1>Never miss another job.</h1>
          <p className="tagline">
            When you can&apos;t answer, Orchard texts the customer back, offers
            your open times, and books the job — you just tap confirm.
          </p>
          <div className="cta-row">
            <a className="btn btn-primary" href={SMS}>Text me about it</a>
            <a className="btn btn-ghost" href={TEL}>Call Jonathan</a>
          </div>
        </section>

        <section className="section">
          <Reveal>
            <h2 className="section-title">Watch a missed call become a booked job</h2>
            <p className="demo-caption">
              This is what your customers experience — in real time, automatically.
            </p>
            <SmsDemo />
          </Reveal>
        </section>

        <section className="section">
          <Reveal>
            <h2 className="section-title">What you get</h2>
            <div className="features">
              {FEATURES.map((f) => (
                <div className="feature" key={f.title}>
                  <div className="ico" aria-hidden="true">{f.ico}</div>
                  <div>
                    <h3>{f.title}</h3>
                    <p>{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Reveal>
        </section>

        <section className="section">
          <Reveal>
            <h2 className="section-title">Founding customer offer</h2>
            <div className="pricing-card">
              <div className="badge">First 10 businesses only</div>
              <div className="price-big">
                $199<small>/month — locked for life</small>
              </div>
              <p className="price-line">$249 one-time setup · your first month is free</p>
              <ul className="pricing-list">
                <li>Everything set up for you, in person — no tech skills needed</li>
                <li>Your price never increases, ever</li>
                <li>One recovered job a month pays for it</li>
                <li>Cancel anytime — no contract</li>
              </ul>
              <div className="cta-row">
                <a className="btn btn-primary" href={SMS}>Claim a founding spot</a>
              </div>
            </div>
          </Reveal>
        </section>

        <section className="section" aria-label="About Jonathan Oh">
          <Reveal>
            <div className="trust">
              <div className="avatar">JO</div>
              <div>
                <div className="trust-name">Jonathan Oh</div>
                <p>
                  Local — Santa Clarita &amp; Torrance, CA. I set up every business
                  personally and you have my cell.
                </p>
              </div>
            </div>
            <p className="privacy-line">
              Your customers&apos; info lives in an encrypted database with a locked
              compartment per business. Payments are handled by Stripe — card numbers
              never touch our systems. The AI reads, replies, and keeps nothing.
            </p>
          </Reveal>
        </section>
      </div>

      <footer className="footer">
        <div className="wrap">
          Orchard · getorchard.app ·{" "}
          <Link href="/demo">See a sample customer website →</Link>
        </div>
      </footer>
    </main>
  );
}
