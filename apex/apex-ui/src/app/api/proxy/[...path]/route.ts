// Catch-all server-side proxy to apex-agents.
// Browser hits /api/proxy/<anything> — Next.js server forwards to apex-agents.
// Works identically in local dev and in Docker Compose (container name resolution).
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const AGENT_API = process.env.AGENT_API_URL || "http://localhost:8001";

function upstream(path: string[], search: string): string {
  return `${AGENT_API}/${path.join("/")}${search}`;
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const url = upstream(path, req.nextUrl.search);
  try {
    const res = await fetch(url);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "apex-agents unreachable" }, { status: 502 });
  }
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const url = upstream(path, "");
  const body = await req.text();
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "apex-agents unreachable" }, { status: 502 });
  }
}
