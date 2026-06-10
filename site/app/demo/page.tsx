import Link from "next/link";

const SERVICES = [
  { ico: "🚿", name: "Plumbing repairs" },
  { ico: "💡", name: "Electrical fixes" },
  { ico: "🚪", name: "Doors & drywall" },
  { ico: "🪜", name: "Gutter cleaning" },
  { ico: "🪑", name: "Furniture assembly" },
  { ico: "🛠️", name: "Honey-do lists" },
];

export default function DemoHome() {
  return (
    <main className="wrap">
      <section className="demo-hero">
        <h1>Your local handyman, one text away.</h1>
        <p className="tagline">
          Fast, tidy, and on time. Most jobs done within the week.
        </p>
        <div className="cta-row">
          <Link className="btn btn-primary" href="/demo/book">Book a job</Link>
        </div>
      </section>

      <section className="section">
        <h2 className="section-title">What we do</h2>
        <div className="services">
          {SERVICES.map((s) => (
            <div className="service-card" key={s.name}>
              <span className="ico">{s.ico}</span>
              {s.name}
            </div>
          ))}
        </div>
      </section>

      <section className="section" style={{ textAlign: "center" }}>
        <h2 className="section-title">Serving the Santa Clarita Valley</h2>
        <p className="tagline">
          Newhall, Valencia, Saugus, Canyon Country, and Castaic.
          Text or call anytime — if we miss you, we text right back.
        </p>
        <div className="cta-row">
          <Link className="btn btn-ghost" href="/demo/book">Check our availability</Link>
        </div>
      </section>
    </main>
  );
}
