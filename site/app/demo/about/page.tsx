import Link from "next/link";

export default function DemoAbout() {
  return (
    <main className="wrap">
      <section className="demo-hero">
        <h1>About Oakwood</h1>
      </section>
      <section style={{ paddingBottom: 20 }}>
        <div className="trust" style={{ marginBottom: 18 }}>
          <div className="avatar">M</div>
          <div>
            <div className="trust-name">Mike Oakwood — Owner</div>
            <p>15 years fixing homes in the Santa Clarita Valley.</p>
          </div>
        </div>
        <p>
          Oakwood Handyman is a one-man shop, and that&apos;s on purpose: the
          person you text is the person who shows up. Licensed and insured,
          background-checked, and serious about leaving every workspace cleaner
          than we found it.
        </p>
        <p>
          We price by the job, not the hour, so you know the number before any
          work starts. If something isn&apos;t right, we come back and fix it —
          no charge, no argument.
        </p>
        <div className="cta-row" style={{ padding: "16px 0 32px" }}>
          <Link className="btn btn-primary" href="/demo/book">Book a job</Link>
        </div>
      </section>
    </main>
  );
}
