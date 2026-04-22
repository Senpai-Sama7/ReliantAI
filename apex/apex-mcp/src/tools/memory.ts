// apex-mcp/src/tools/memory.ts
// pgvector semantic memory search via apex-agents REST API.
// Allows any agent to retrieve past decisions, corrections, and knowledge
// using embedding similarity rather than keyword matching.
import { ToolDefinition } from '../types';

const AGENTS_URL = process.env['APEX_AGENTS_URL'] ?? 'http://apex-agents:8001';

export const memorySearchTool: ToolDefinition = {
  name:        'memory_search',
  description: 'Search APEX episodic and semantic memory using vector similarity. Returns past decisions, human corrections, and domain knowledge relevant to the current task.',
  integration: 'memory',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type:        'string',
        description: 'Natural language description of what to search for in memory',
      },
      memory_type: {
        type:        'string',
        description: 'Type of memory to search',
        enum:        ['episodic', 'semantic', 'procedural', 'all'],
      },
      limit: {
        type:        'string',
        description: 'Max results (default 5)',
      },
    },
    required: ['query'],
  },
  async execute(args) {
    const res = await fetch(`${AGENTS_URL}/memory/search`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query:       String(args['query']),
        memory_type: String(args['memory_type'] ?? 'all'),
        limit:       parseInt(String(args['limit'] ?? '5'), 10),
      }),
    });

    if (!res.ok) {
      throw new Error(`Memory search failed: ${res.status} ${res.statusText}`);
    }
    return res.json();
  },
};

export const memorySaveTool: ToolDefinition = {
  name:        'memory_save',
  description: 'Save a decision, correction, or learned fact to APEX memory for future retrieval.',
  integration: 'memory',
  inputSchema: {
    type: 'object',
    properties: {
      agent_name:   { type: 'string', description: 'Name of the agent saving this memory' },
      task_summary: { type: 'string', description: 'Brief summary of the task this memory is from' },
      content:      { type: 'string', description: 'The content to save' },
      memory_type:  {
        type:        'string',
        description: 'Memory category',
        enum:        ['episodic', 'semantic', 'procedural'],
      },
      confidence:   { type: 'string', description: 'Confidence in this memory (0.0–1.0)' },
    },
    required: ['agent_name', 'task_summary', 'content', 'memory_type'],
  },
  async execute(args) {
    const res = await fetch(`${AGENTS_URL}/memory/save`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_name:   String(args['agent_name']),
        task_summary: String(args['task_summary']),
        content:      String(args['content']),
        memory_type:  String(args['memory_type']),
        confidence:   parseFloat(String(args['confidence'] ?? '0.8')),
      }),
    });

    if (!res.ok) throw new Error(`Memory save failed: ${res.status}`);
    return res.json();
  },
};
