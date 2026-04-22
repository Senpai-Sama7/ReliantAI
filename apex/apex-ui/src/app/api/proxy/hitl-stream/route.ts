// Server-side SSE proxy.
// The browser connects here (/api/proxy/hitl-stream) and Next.js forwards
// the stream from apex-agents. This keeps apex-agents off the public network.
export const dynamic = "force-dynamic";

export async function GET() {
  const agentApi = process.env.AGENT_API_URL || "http://localhost:8001";

  let upstream: Response;
  try {
    upstream = await fetch(`${agentApi}/workflow/hitl/stream`, {
      headers: { Accept: "text/event-stream" },
    });
  } catch {
    return new Response("data: {\"type\":\"error\",\"message\":\"apex-agents unreachable\"}\n\n", {
      status: 502,
      headers: { "Content-Type": "text/event-stream" },
    });
  }

  if (!upstream.body) {
    return new Response("SSE body unavailable", { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
