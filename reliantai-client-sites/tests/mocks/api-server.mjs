// Zero-dependency stand-in for the FastAPI endpoint
// GET /api/v2/generated-sites/{slug} (reliantai/api/v2/generated_sites.py).
// Started by playwright.config.ts so e2e tests exercise the real ISR fetch
// path with real HTTP 200/404 semantics instead of ECONNREFUSED.
import { createServer } from "node:http";
import baseSiteContent from "../fixtures/site-content.mjs";

const PORT = Number(process.env.MOCK_API_PORT || 8765);

const sites = new Map([
  [
    "test-hvac-austin",
    { ...baseSiteContent, slug: "test-hvac-austin", status: "live" },
  ],
  [
    "preview-hvac-austin",
    { ...baseSiteContent, slug: "preview-hvac-austin", status: "preview_live" },
  ],
  [
    "bad-template-austin",
    {
      ...baseSiteContent,
      slug: "bad-template-austin",
      status: "live",
      site_config: {
        ...baseSiteContent.site_config,
        template_id: "nonexistent-template",
      },
    },
  ],
]);

function sendJson(res, status, body) {
  res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
}

const server = createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://127.0.0.1:${PORT}`);

  if (req.method === "GET" && url.pathname === "/health") {
    sendJson(res, 200, { status: "ok" });
    return;
  }

  const match = url.pathname.match(/^\/api\/v2\/generated-sites\/([^/]+)$/);
  if (req.method === "GET" && match) {
    const slug = decodeURIComponent(match[1]);
    const site = sites.get(slug);
    if (site) {
      sendJson(res, 200, site);
      return;
    }
    sendJson(res, 404, { detail: "Site not found" });
    return;
  }

  sendJson(res, 404, { detail: "Not found" });
});

server.listen(PORT, () => {
  console.log(`[mock-api] listening on http://127.0.0.1:${PORT}`);
});
