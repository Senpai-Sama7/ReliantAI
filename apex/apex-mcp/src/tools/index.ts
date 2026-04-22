// apex-mcp/src/tools/index.ts
// Barrel export — every tool registered here is automatically available to all agents.
import { ToolDefinition } from '../types';

import { context7Tool }                        from './context7';
import { zapierTool }                          from './zapier';
import { hubspotSearchTool, hubspotCreateDealTool } from './hubspot';
import { notionSearchTool, notionCreatePageTool }   from './notion';
import { slackPostTool }                       from './slack';
import { stripeCustomerLookupTool, stripeInvoiceLookupTool } from './stripe';
import { braveSearchTool }                     from './brave_search';
import { memorySearchTool, memorySaveTool }    from './memory';

// ── ALL_TOOLS ─────────────────────────────────────────────────────────────────────
// Add new tools here. They are automatically:
// 1. Listed at GET /tools
// 2. Callable via POST /tools/call
// 3. Protected by circuit breakers grouped by tool.integration
// 4. Exposed via the MCP JSON-RPC protocol at POST /mcp
export const ALL_TOOLS: ToolDefinition[] = [
  // ─ Documentation (pre-flight validation for code agents) ─
  context7Tool,

  // ─ Outbound action bus ─
  zapierTool,

  // ─ CRM ─
  hubspotSearchTool,
  hubspotCreateDealTool,

  // ─ Knowledge management ─
  notionSearchTool,
  notionCreatePageTool,

  // ─ Communication ─
  slackPostTool,

  // ─ Payments (read-only) ─
  stripeCustomerLookupTool,
  stripeInvoiceLookupTool,

  // ─ Research ─
  braveSearchTool,

  // ─ Memory ─
  memorySearchTool,
  memorySaveTool,
];

export const TOOL_MAP = new Map<string, ToolDefinition>(
  ALL_TOOLS.map((t) => [t.name, t])
);
