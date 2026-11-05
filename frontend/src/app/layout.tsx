import type { Metadata } from "next";
import { IBM_Plex_Mono, Schibsted_Grotesk } from "next/font/google";

import "@/app/globals.css";
import { Providers } from "@/app/providers";

const sans = Schibsted_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
  adjustFontFallback: false,
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["300", "400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Talent Lens — See Beyond the Resume",
  description: "AI-Powered Hiring Intelligence for Modern Teams.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${sans.variable} ${mono.variable} font-sans antialiased`} suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
