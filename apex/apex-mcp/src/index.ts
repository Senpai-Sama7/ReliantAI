// apex-mcp/src/index.ts
// APEX MCP Tool Bus — HTTP server exposing tools to all APEX agents.
//
// Endpoints:
//   GET  /health              — liveness probe
//   GET  /tools               — list all tools with schemas
//   POST /tools/call          — execute a tool (REST, used by apex-agents Python)
//   GET  /circuit-breakers    — status of all integration circuit breakers
//   POST /mcp                 — MCP JSON-RPC 2.0 protocol (for MCP-native clients)

import 'dotenv/config';
import express, { Request, Response, NextFunction } from 'express';
import { isToolAllowed, requireApiKey } from './auth';
import { listTools, callTool, getAllBreakerStatuses } from './registry';

const app  = express();
const PORT = parseInt(process.env['PORT'] ?? '4000', 10);

// Security: Disable X-Powered-By header to prevent technology stack disclosure
app.disable('x-powered-by');

// Security headers middleware (applied to all routes)
app.use((_req: Request, res: Response, next: NextFunction) => {
  res.set({
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Frame-Options':           'DENY',
    'X-Content-Type-Options':     'nosniff',
    'Content-Security-Policy':   "default-src 'none'",
  });
  next();
});

app.use(express.json({ limit: '2mb' }));

// ── Logging middleware ───────────────────────────────────────────────────────────
app.use((req: Request, _res: Response, next: NextFunction) => {
  console.log(`[apex-mcp] ${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});

// ── GET /health ───────────────────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({
    ok:          true,
    service:     'apex-mcp',
    tools_count: listTools().length,
    timestamp:   new Date().toISOString(),
  });
});

// ── GET /tools ───────────────────────────────────────────────────────────────
app.get('/tools', requireApiKey, (_req, res) => {
  res.json({ tools: listTools() });
});

// ── POST /tools/call ──────────────────────────────────────────────────────────
app.post('/tools/call', requireApiKey, async (req: Request, res: Response) => {
  const { name, arguments: args } = req.body as {
    name:       string;
    arguments?: Record<string, unknown>;
  };

  if (!name || typeof name !== 'string') {
    res.status(400).json({ success: false, error: '`name` is required' });
    return;
  }
  if (!isToolAllowed(name)) {
    res.status(403).json({ success: false, error: `Tool '${name}' is not allowed` });
    return;
  }

  const result = await callTool(name, args ?? {});
  const status = result.success ? 200 : (result.circuit_breaker ? 503 : 422);
  res.status(status).json(result);
});

// ── GET /circuit-breakers ───────────────────────────────────────────────────────
app.get('/circuit-breakers', requireApiKey, (_req, res) => {
  const statuses = getAllBreakerStatuses();
  const open     = statuses.filter(s => s.state === 'OPEN').length;
  res.json({
    summary:  { total: statuses.length, open, closed: statuses.length - open },
    breakers: statuses,
  });
});

// ── POST /mcp — MCP JSON-RPC 2.0 protocol ──────────────────────────────────────
interface JsonRpcRequest {
  jsonrpc: '2.0';
  id:      string | number;
  method:  string;
  params?: Record<string, unknown>;
}

app.post('/mcp', requireApiKey, async (req: Request, res: Response) => {
  const rpc = req.body as JsonRpcRequest;

  if (rpc.jsonrpc !== '2.0' || !rpc.method) {
    res.status(400).json({
      jsonrpc: '2.0', id: rpc.id ?? null,
      error: { code: -32600, message: 'Invalid JSON-RPC request' },
    });
    return;
  }

  // ─ tools/list ─
  if (rpc.method === 'tools/list') {
    res.json({
      jsonrpc: '2.0', id: rpc.id,
      result: { tools: listTools() },
    });
    return;
  }

  // ─ tools/call ─
  if (rpc.method === 'tools/call') {
    const { name, arguments: args } = (rpc.params ?? {}) as {
      name?:      string;
      arguments?: Record<string, unknown>;
    };

    if (!name) {
      res.json({
        jsonrpc: '2.0', id: rpc.id,
        error: { code: -32602, message: 'Missing required param: name' },
      });
      return;
    }
    if (!isToolAllowed(name)) {
      res.json({
        jsonrpc: '2.0', id: rpc.id,
        error: { code: -32003, message: `Tool '${name}' is not allowed` },
      });
      return;
    }

    const result = await callTool(name, args ?? {});
    res.json({
      jsonrpc: '2.0', id: rpc.id,
      result: {
        content: [{
          type: 'text',
          text: result.success
            ? JSON.stringify(result.data, null, 2)
            : `ERROR: ${result.error}`,
        }],
        isError: !result.success,
      },
    });
    return;
  }

  // ─ initialize (MCP handshake) ─
  if (rpc.method === 'initialize') {
    res.json({
      jsonrpc: '2.0', id: rpc.id,
      result: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        serverInfo: { name: 'apex-mcp', version: '0.1.0' },
      },
    });
    return;
  }

  res.json({
    jsonrpc: '2.0', id: rpc.id,
    error: { code: -32601, message: `Method '${rpc.method}' not found` },
  });
});

// ── Global error handler ─────────────────────────────────────────────────────────
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('[apex-mcp] Unhandled error:', err.message);
  res.status(500).json({ success: false, error: 'Internal server error' });
});

// ── Start ─────────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  const tools = listTools();
  console.log(`[apex-mcp] Running on port ${PORT}`);
  console.log(`[apex-mcp] ${tools.length} tools registered:`);
  tools.forEach(t => console.log(`  • ${t.name} (${t.integration})`));
});
