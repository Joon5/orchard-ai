import Link from "next/link";
import SmsDemo from "@/components/SmsDemo";
import Reveal from "@/components/Reveal";
import Icon from "@/components/Icon";
import CountUp from "@/components/CountUp";

const TEL = "tel:+14242251386";
const SMS = "sms:+14242251386";
const EMAIL = "mailto:orchard.ai.app@gmail.com";

const FEATURES = [
  { icon: "globe", title: "A website that books jobs", desc: "A clean, professional site with online booking. We build it and keep it running for you." },
  { icon: "phone", title: "Your own business number", desc: "A dedicated line for the business, so your personal cell stays personal." },
  { icon: "chat", title: "Instant text-back", desc: "Every missed call gets a reply in seconds. Customers book right from the text." },
  { icon: "calendar", title: "A calendar that fills itself", desc: "Jobs land on your Google Calendar. Reminders go out on their own." },
  { icon: "dashboard", title: "One simple dashboard", desc: "Every job in one place. Approve it with a tap. Nothing books without you." },
  { icon: "shield", title: "Your customers, protected", desc: "Everything is encrypted and kept separate. Payments run through Stripe, never through us." },
];

const STEPS = [
  { icon: "phone", n: "1", title: "A call comes in while you work", desc: "You are under a sink or up a ladder. You cannot stop, so the call would normally go to voicemail." },
  { icon: "chat", n: "2", title: "Orchard texts back in seconds", desc: "It greets the customer, asks what they need, and offers the times you actually have open." },
  { icon: "check", n: "3", title: "You tap confirm and it is booked", desc: "The job lands on your calendar and the customer gets a confirmation text. Done." },
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
            <span className="eyebrow">The AI front desk for the trades</span>
            <h1>Never miss another job.</h1>
            <p className="lead">
              You are on a job and the phone rings. Orchard answers, texts the
              customer back in seconds, and offers your open times. The booking
              lands on your calendar and all you do is tap confirm.
            </p>
            <div className="cta-row">
              <a className="btn btn-primary" href={SMS}>Text me about it</a>
              <a className="btn btn-ghost" href="#how">See how it works</a>
            </div>
            <ul className="microtrust">
              <li><Icon name="check" size={18} /> Set up for you in a day</li>
              <li><Icon name="check" size={18} /> No tech skills needed</li>
              <li><Icon name="check" size={18} /> Santa Clarita &amp; the South Bay</li>
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
                <div className="stat-num"><CountUp value={62} suffix="%" /></div>
                <p>of callers ring the next company when you do not pick up</p>
              </div>
              <div className="stat">
                <div className="stat-num">$275 to $1,200</div>
                <p>is what a single service job is typically worth</p>
              </div>
              <div className="stat">
                <div className="stat-num"><CountUp value={85} suffix="%" /></div>
                <p>of people who reach voicemail never call back</p>
              </div>
            </div>
            <p className="stat-note">Industry estimates from the U.S. home services sector.</p>
          </Reveal>
        </div>
      </section>

      {/* ── How it works ───────────────────────────────────── */}
      <section className="band band-soft" id="how">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">How it works</span>
            <h2 className="section-title">Booked jobs without picking up the phone</h2>
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
      <section className="band" id="features">
        <div className="wrap">
          <Reveal>
            <span className="eyebrow">What you get</span>
            <h2 className="section-title">Everything a front desk does, without hiring one</h2>
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

      {/* ── Owner dashboard ────────────────────────────────── */}
      <section className="band band-soft">
        <div className="wrap">
          <Reveal>
            <div className="example">
              <div>
                <span className="eyebrow">Built for the owner</span>
                <h2 className="section-title left">Run your whole day from your phone</h2>
                <p className="lead">
                  Open the app and see today at a glance. New requests, jobs
                  waiting on your okay, and what is coming up next. Tap once to
                  confirm. Tap once to reschedule. You stay in control of every job.
                </p>
                <a className="btn btn-primary" href={SMS}>Text me for a walkthrough</a>
              </div>

              <div className="dash">
                <div className="dash-top">
                  <div>
                    <div className="dash-hello">Good morning, Mike</div>
                    <div className="dash-date">Thursday, today</div>
                  </div>
                  <span className="dash-bell"><Icon name="clock" size={18} /></span>
                </div>
                <div className="dash-chips">
                  <div className="dash-chip alert"><strong>2</strong><span>to confirm</span></div>
                  <div className="dash-chip"><strong>3</strong><span>today</span></div>
                  <div className="dash-chip"><strong>6</strong><span>this week</span></div>
                </div>
                <div className="dash-label">Waiting on you</div>
                <div className="dash-job pending">
                  <div>
                    <div className="dash-job-title">Garbage disposal leak</div>
                    <div className="dash-job-sub">Jane S. · Thu 9–11 AM</div>
                  </div>
                  <div className="dash-actions">
                    <span className="dash-btn confirm">Confirm</span>
                    <span className="dash-btn ghost">Move</span>
                  </div>
                </div>
                <div className="dash-job pending">
                  <div>
                    <div className="dash-job-title">Ceiling fan install</div>
                    <div className="dash-job-sub">Dave R. · Fri 2–4 PM</div>
                  </div>
                  <div className="dash-actions">
                    <span className="dash-btn confirm">Confirm</span>
                    <span className="dash-btn ghost">Move</span>
                  </div>
                </div>
                <div className="dash-label">Confirmed today</div>
                <div className="dash-job done">
                  <div>
                    <div className="dash-job-title">Faucet replacement</div>
                    <div className="dash-job-sub">Carla M. · 1–2 PM</div>
                  </div>
                  <span className="dash-tick"><Icon name="check" size={16} /></span>
                </div>
              </div>
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
                <h2 className="section-title left">A real website, built for a handyman</h2>
                <p className="lead">
                  This is the exact website and booking flow your business gets.
                  Go ahead and try the booking form yourself.
                </p>
                <Link className="btn btn-primary" href="/demo">
                  View the sample site <Icon name="arrow" size={18} />
                </Link>
              </div>
              <Link href="/demo" className="example-card" aria-label="Open the sample site">
                <div className="example-bar">
                  <span /><span /><span />
                  <span className="example-url">oakwoodhandyman.com</span>
                </div>
                <div className="example-body">
                  <div className="example-logo">🔨 Oakwood Handyman</div>
                  <div className="example-headline">Your local handyman, one text away</div>
                  <div className="example-sub">Serving the Santa Clarita Valley · Licensed &amp; insured</div>
                  <div className="example-services">
                    <span>Plumbing</span><span>Electrical</span><span>Drywall</span>
                    <span>Gutters</span><span>Assembly</span>
                  </div>
                  <div className="example-row">
                    <span className="example-rating">★★★★★ 5.0 (38)</span>
                    <span className="example-pill">Book a job</span>
                  </div>
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
              <div className="price-big">$199<small>per month, locked for life</small></div>
              <p className="price-line">$249 one-time setup. Your first month is free.</p>
              <ul className="pricing-list">
                <li>Everything set up for you, in person. No tech skills needed.</li>
                <li>Your price never goes up. Ever.</li>
                <li>One recovered job a month more than covers it.</li>
                <li>Cancel anytime. No contract.</li>
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
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img className="founder-photo" src="/jonathan.jpg" alt="Jonathan Oh, founder of Orchard" />
              <div>
                <div className="trust-name">Jonathan Oh, Founder</div>
                <p>
                  I am local to Santa Clarita and grew up in the South Bay. Many
                  of my friends work in the trades, which exposed me to the regular
                  inefficiencies they deal with. Orchard.ai is my solution to that,
                  and I set up every business dashboard and maintain it myself.
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
            <p>Send me a text and I will show you exactly how it would work for your business.</p>
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
            <a href={SMS}>Text (424) 225-1386</a>
            <a href={TEL}>Call us</a>
            <a href={EMAIL}>orchard.ai.app@gmail.com</a>
          </div>
        </div>
        <div className="footer-base">Built in Santa Clarita, CA · getorchard.app</div>
      </footer>
    </main>
  );
}
