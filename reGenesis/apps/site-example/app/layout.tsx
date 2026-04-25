
import "./globals.css";
import "@cyberarchitect/motion-tokens/dist/motion.css";
import type { ReactNode } from "react";

export const metadata = { title: "CyberArchitect Example", description: "Demo app generated from brief" };

export default function RootLayout({ children }: { children: ReactNode }){
  return (<html lang="en"><body>{children}</body></html>);
}
