import type { Metadata, Viewport } from "next";
import "./globals.css";

const DESCRIPTION =
  "AI front desk for trade businesses. Missed calls become booked appointments, automatically. Website, business number, booking, and reminders — set up for you.";

export const metadata: Metadata = {
  metadataBase: new URL("https://getorchard.app"),
  title: "Orchard — Never miss another job",
  description: DESCRIPTION,
  openGraph: {
    title: "Orchard — Never miss another job",
    description: DESCRIPTION,
    url: "https://getorchard.app",
    siteName: "Orchard",
    images: [{ url: "/og.jpg", width: 1250, height: 1281 }],
  },
  twitter: {
    card: "summary",
    title: "Orchard — Never miss another job",
    description: DESCRIPTION,
    images: ["/og.jpg"],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
