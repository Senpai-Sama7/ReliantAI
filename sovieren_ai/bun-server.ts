const port = parseInt(process.env.PORT || "8106");

const server = Bun.serve({
  port,
  fetch(req: Request) {
    const url = new URL(req.url);

    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "healthy", service: "sovieren-ai" }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(
      `<!DOCTYPE html>
<html>
<head><title>sovieren.ai</title></head>
<body>
  <h1>sovieren.ai</h1>
  <p>ReliantAI Platform — Service placeholder</p>
</body>
</html>`,
      { headers: { "Content-Type": "text/html" } }
    );
  },
});

console.log(`sovieren-ai listening on http://localhost:${port}`);
