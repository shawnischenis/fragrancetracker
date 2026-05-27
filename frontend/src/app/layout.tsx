import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Scent Index",
  description: "Fragrance market intelligence and price alerts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
