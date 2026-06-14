import Link from "next/link";
import SmsDemo from "@/components/SmsDemo";
import Reveal from "@/components/Reveal";
import Icon from "@/components/Icon";

const TEL = "tel:+14244018308";
const SMS = "sms:+14244018308";

const FEATURES = [
  { icon: "globe", title: "A professional website", desc: "A clean three-page site with online booking — built and maintained for you." },
  { icon: "phone", title: "A business number", desc: "A dedicated line for the business. Keep your personal cell personal." },
  { icon: "chat", title: "Automatic text-back", desc: "Every missed call gets an instant text. Customers book right from the reply." },
  { icon: "calendar", title: "A booking calendar", desc: "Jobs land on your Google Calendar. Reminders go out on their own." },
  { icon: "dashboard", title: "An owner dashboard", desc: "Every job in one place. Approve with one tap — nothing books without you." },
  { icon: "shield", title: "Your data, locked down", desc: "Encrypted, separated per business. Payments run through Stripe — never us." },
];

const STEPS = [
  { icon: "phone", n: "1", title: "A call comes in while you're working", desc: "You're under a sink or up a ladder. You can't stop to answer — so it goes to voicemail." },
  { icon: "chat", n: "2", title: "Orchard texts back in seconds", desc: "It greets the customer, asks what they need, and offers your real open times." },
  { icon: "check", n: "3", title: "You tap confirm — job booked", desc: "The appointment lands on your calendar and the customer gets a confirmation text." },
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
      {/* ── Header ─────────────────────────────────────────── */}
      <header className="site-header">
        <div className="bar">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="logo-mark" src="/logo.svg" alt="" aria-hidden="true" />
          <Wordmark />
          <nav className="nav-links" aria-label="Primary">
            <a href="#how">How it works</a>
            <a href="#features">What you get</a>
            <a href="#pricing">Pricing</a>
          </nav>
          <a className="header-cta" href={SMS}>Text Jonathan</a>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────── */}
      <section className="hero">
        <div className="wrap hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">AI front desk for the trades</span>
            <h1>Never miss another job.</h1>
            <p className="lead">
              When you&apos;re on a job and can&apos;t pick up, Orchard texts the
              customer back in seconds, offers your open times, and books it
              straight to your calendar. You just tap confirm.
            </p>
            <div className="cta-row">
              <a className="btn btn-primary" href={SMS}>Text me about it</a>
              <a className="btn btn-ghost" href="#how">See how it works</a>
            </div>
            <ul className="microtrust">
              <li><Icon name="check" size={18} /> Set up for you in a day</li>
              <li><Icon name="check" size={18} /> No tech skills needed</li>
              <li><Icon name="check" size={18} /> Santa Clarita &amp; South Bay</li>
            </ul>
          </div>
          <div className="hero-visual">
            <SmsDemo />
          </div>
        </div>
      </section>

      {/* ── Problem stat band ──────────────────────────────── */}
      <section className="band band-dark">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow eyebrow-light">What a missed call really costs</span>
            <div className="stats">
              <div className="stat">
                <div className="stat-num">62%</div>
                <p>of callers ring a competitor after one unanswered call</p>
              </div>
              <div className="stat">
                <div className="stat-num">$275–1,200</div>
                <p>the typical value of a single service job</p>
              </div>
              <div className="stat">
                <div className="stat-num">85%</div>
                <p>of people who reach voicemail never call back</p>
              </div>
            </div>
            <p className="stat-note">Industry estimates, U.S. home-services sector.</p>
          </Reveal>
        </div>
      </section>

      {/* ── How it works ───────────────────────────────────── */}
      <section className="band" id="how">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">How it works</span>
            <h2 className="section-title">From missed call to booked job — automatically</h2>
            <div className="steps">
              {STEPS.map((s) => (
                <div className="step" key={s.n}>
                  <div className="step-head">
                    <span className="step-num">{s.n}</span>
                    <span className="step-ico"><Icon name={s.icon} /></span>
                  </div>
                  <h3>{s.title}</h3>
                  <p>{s.desc}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── Features ───────────────────────────────────────── */}
      <section className="band band-soft" id="features">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">What you get</span>
            <h2 className="section-title">Everything a front desk does — without hiring one</h2>
            <div className="features">
              {FEATURES.map((f) => (
                <div className="feature" key={f.title}>
                  <span className="ico-box"><Icon name={f.icon} /></span>
                  <div>
                    <h3>{f.title}</h3>
                    <p>{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── See a real example ─────────────────────────────── */}
      <section className="band">
        <div className="wrap">
          <Reveal>
            <div className="example">
              <div>
                <span className="eyebrow">See it for real</span>
                <h2 className="section-title left">A working site, built for a handyman</h2>
                <p className="lead">
                  Here&apos;s a real example of the website and booking flow your
                  business gets — try the booking form yourself.
                </p>
                <Link className="btn btn-primary" href="/demo">
                  View the sample site <Icon name="arrow" size={18} />
                </Link>
              </div>
              <Link href="/demo" className="example-card" aria-label="Open the sample site">
                <div className="example-bar"><span /><span /><span /></div>
                <div className="example-body">
                  <div className="example-logo">🔨 Oakwood Handyman</div>
                  <div className="example-line wide" />
                  <div className="example-line" />
                  <div className="example-pill">Book a job</div>
                </div>
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── Pricing ────────────────────────────────────────── */}
      <section className="band band-soft" id="pricing">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">Founding customer offer</span>
            <h2 className="section-title">One price, locked in for good</h2>
            <div className="pricing-card">
              <div className="badge">First 10 businesses only</div>
              <div className="price-big">$199<small>/month — locked for life</small></div>
              <p className="price-line">$249 one-time setup · your first month is free</p>
              <ul className="pricing-list">
                <li>Everything set up for you, in person — no tech skills needed</li>
                <li>Your price never increases, ever</li>
                <li>One recovered job a month more than pays for it</li>
                <li>Cancel anytime — no contract</li>
              </ul>
              <a className="btn btn-primary btn-block" href={SMS}>Claim a founding spot</a>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── Founder ────────────────────────────────────────── */}
      <section className="band" aria-label="About Jonathan Oh">
        <div className="wrap">
          <Reveal>
            <div className="founder">
              <div className="avatar">JO</div>
              <div>
                <div className="trust-name">Jonathan Oh — Founder</div>
                <p>
                  I&apos;m local to Santa Clarita and the South Bay. I set up every
                  business myself, in person, and you get my cell number — not a
                  ticket queue. Your first month is free, so if it isn&apos;t earning
                  its keep, you walk away.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── Final CTA ──────────────────────────────────────── */}
      <section className="band band-dark final">
        <div className="wrap">
          <Reveal>
            <h2>Ready to stop missing jobs?</h2>
            <p>Text me and I&apos;ll show you exactly how it&apos;d work for your business.</p>
            <div className="cta-row center">
              <a className="btn btn-on-dark" href={SMS}>Text me about it</a>
              <a className="btn btn-ghost-light" href={TEL}>Call Jonathan</a>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────── */}
      <footer className="footer">
        <div className="wrap footer-grid">
          <div>
            <div className="footer-brand">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img className="logo-mark" src="/logo.svg" alt="" aria-hidden="true" />
              <Wordmark />
            </div>
            <p className="footer-tag">The AI front desk for trade businesses.</p>
          </div>
          <div className="footer-col">
            <h4>Product</h4>
            <a href="#how">How it works</a>
            <a href="#features">What you get</a>
            <a href="#pricing">Pricing</a>
            <Link href="/demo">Sample site</Link>
          </div>
          <div className="footer-col">
            <h4>Get in touch</h4>
            <a href={SMS}>Text (424) 401-8308</a>
            <a href={TEL}>Call Jonathan</a>
            <a href="mailto:jdoh2023@gmail.com">Email us</a>
          </div>
        </div>
        <div className="footer-base">Built in Santa Clarita, CA · getorchard.app</div>
      </footer>
    </main>
  );
}
