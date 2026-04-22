// apex-mcp/src/registry.ts
// Wraps every tool execution with circuit breaker protection.
// Agents never call tools directly — all calls go through this registry.
import { ToolCallResult, ToolDefinition } from './types';
import { getBreaker, getAllBreakerStatuses } from './circuit-breaker';
import { ALL_TOOLS, TOOL_MAP } from './tools/index';

export function listTools(): Array<{
  name: string;
  description: string;
  integration: string;
  inputSchema: ToolDefinition['inputSchema'];
}> {
  return ALL_TOOLS.map(({ name, description, integration, inputSchema }) => ({
    name,
    description,
    integration,
    inputSchema,
  }));
}

export async function callTool(
  name: string,
  args: Record<string, unknown>,
): Promise<ToolCallResult> {
  const tool = TOOL_MAP.get(name);

  if (!tool) {
    return {
      success: false,
      error: `Tool '${name}' not found. Available: ${ALL_TOOLS.map(t => t.name).join(', ')}`,
    };
  }

  const breaker = getBreaker(tool.integration);

  try {
    const data = await breaker.execute(() => tool.execute(args));
    return { success: true, data };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    const isCircuitOpen = message.startsWith('[CircuitBreaker:');
    return {
      success:          false,
      error:            message,
      circuit_breaker:  isCircuitOpen ? breaker.status.state : undefined,
    };
  }
}

export { getAllBreakerStatuses };
