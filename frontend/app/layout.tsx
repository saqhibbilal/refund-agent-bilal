import type { Metadata } from "next";
import { Oswald, Roboto_Condensed } from "next/font/google";

import "./globals.css";

const robotoCondensed = Roboto_Condensed({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-roboto-condensed",
});

const oswald = Oswald({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-oswald",
});

export const metadata: Metadata = {
  title: "Worknoon Refund Agent",
  description: "AI refund support with policy-backed decisions",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${robotoCondensed.variable} ${oswald.variable}`}>
      <body className="min-h-screen bg-worknoon-dark font-sans text-worknoon-ice antialiased">
        {children}
      </body>
    </html>
  );
}
