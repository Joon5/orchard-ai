import Link from "next/link";

export const metadata = { robots: "noindex" };

export default function DemoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="demo-banner">
        This is a live demo. <Link href="/">Your business gets one of these.</Link>
      </div>
      <nav className="demo-nav">
        <Link className="logo" href="/demo">🔨 Oakwood Handyman</Link>
        <Link href="/demo/about">About</Link>
        <Link href="/demo/book">Book a Job</Link>
      </nav>
      {children}
      <footer className="demo-footer">
        Oakwood Handyman Services · Serving the Santa Clarita Valley ·
        Licensed &amp; insured · (310) 555-0144
        <br />
        <em>Sample website by Orchard · getorchard.app</em>
      </footer>
    </div>
  );
}
