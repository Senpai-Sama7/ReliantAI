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
  
  // Forward Authorization header from original request
  const headers: Record<string, string> = {};
  const authHeader = req.headers.get("authorization");
  if (authHeader) {
    headers["Authorization"] = authHeader;
  }
  
  try {
    const res = await fetch(url, { headers });
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
  
  // Forward Authorization header from original request
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const authHeader = req.headers.get("authorization");
  if (authHeader) {
    headers["Authorization"] = authHeader;
  }
  
  try {
    const res = await fetch(url, {
      method: "POST",
      headers,
      body,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "apex-agents unreachable" }, { status: 502 });
  }
}
