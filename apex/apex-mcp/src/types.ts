// apex-mcp/src/types.ts

export type JsonSchemaProperty = {
  type:        string;
  description: string;
  enum?:       string[];
  items?:      { type: string };
};

export type ToolInputSchema = {
  type:        'object';
  properties:  Record<string, JsonSchemaProperty>;
  required:    string[];
};

export type ToolDefinition = {
  name:        string;
  description: string;
  integration: string;    // groups tools under one circuit breaker
  inputSchema: ToolInputSchema;
  execute:     (args: Record<string, unknown>) => Promise<unknown>;
};

export type ToolCallResult = {
  success:          boolean;
  data?:            unknown;
  error?:           string;
  circuit_breaker?: string;   // set when blocked by open circuit
};

export type CircuitBreakerStatus = {
  name:     string;
  state:    'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failures: number;
};
