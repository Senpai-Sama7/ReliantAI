import type { ReactNode } from "react";

export const metadata = {
  title: "APEX HITL Dashboard",
  description: "Human-in-the-loop control panel for APEX Layer 1 workflows",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, background: "#f9fafb" }}>
        {children}
      </body>
    </html>
  );
}
