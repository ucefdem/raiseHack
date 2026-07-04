import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meeting Agent",
  description: "An AI teammate with its own computer.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen text-slate-100 antialiased">{children}</body>
    </html>
  );
}
