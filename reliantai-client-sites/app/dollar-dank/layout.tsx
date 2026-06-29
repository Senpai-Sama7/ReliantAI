import type { Metadata } from "next";
import { DM_Sans, Bebas_Neue } from "next/font/google";
import "./meta.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm",
  display: "swap",
});

const bebas = Bebas_Neue({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-bebas",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Dollar Dank Dispensary | Houston, TX",
  description:
    "Can you hit 10.00? Dollar Dank Dispensary — 6590 SW Freeway, Houston. Open daily 8AM–2AM.",
  openGraph: {
    title: "Dollar Dank Dispensary",
    description: "Can you hit 10.00? 6590 SW Freeway, Houston TX.",
    type: "website",
  },
};

export default function DollarDankLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className={`${dmSans.variable} ${bebas.variable} dd-root min-h-screen`}>
      {children}
    </div>
  );
}
