import type { Metadata } from "next";
import { Syne, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./styles.css";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  display: "swap",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-plex-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "FAANG 2026 — Design System Showcase",
  description:
    "2026 web design at FAANG scale: kinetic typography, tactile brutalism, glassmorphism 2.0, bento grids, and archival index aesthetics.",
};

export default function Faang2026Layout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div
      className={`${syne.variable} ${plexSans.variable} ${plexMono.variable} faang-2026-root`}
    >
      {children}
    </div>
  );
}
