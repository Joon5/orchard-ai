import type { Metadata, Viewport } from "next";
import "./globals.css";

const DESCRIPTION =
  "The AI front desk for trade businesses. When you can't pick up, Orchard texts customers back, books the job, and adds it to your calendar. You just tap confirm.";

export const metadata: Metadata = {
  metadataBase: new URL("https://getorchard.app"),
  title: "Orchard | Never miss another job",
  description: DESCRIPTION,
  openGraph: {
    title: "Orchard | Never miss another job",
    description: DESCRIPTION,
    url: "https://getorchard.app",
    siteName: "Orchard",
    images: [{ url: "/og.jpg", width: 1250, height: 1281 }],
  },
  twitter: {
    card: "summary",
    title: "Orchard | Never miss another job",
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
