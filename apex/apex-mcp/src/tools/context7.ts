// apex-mcp/src/tools/context7.ts
// Context7: pre-flight documentation lookup for code-generating agents.
// Eliminates hallucinated API calls by fetching real docs at runtime.
import { ToolDefinition } from '../types';

const BASE = 'https://context7.com/api/v1';

async function resolveLibraryId(query: string): Promise<string | null> {
  const url = `${BASE}/search?q=${encodeURIComponent(query)}&limit=1`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error(`Context7 search failed: ${res.status}`);
  const data = await res.json() as { results?: Array<{ id: string }> };
  return data.results?.[0]?.id ?? null;
}

async function fetchDocs(
  libraryId: string,
  topic: string,
  tokens: number,
): Promise<unknown> {
  const url = `${BASE}/${encodeURIComponent(libraryId)}?topic=${encodeURIComponent(topic)}&tokens=${tokens}`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error(`Context7 docs failed: ${res.status}`);
  return res.json();
}

export const context7Tool: ToolDefinition = {
  name:        'context7_lookup',
  description: 'Fetches up-to-date library documentation from Context7. Use this BEFORE writing any code that calls an external library. Prevents hallucinated API signatures.',
  integration: 'context7',
  inputSchema: {
    type: 'object',
    properties: {
      library: {
        type:        'string',
        description: 'Library name to look up (e.g. \'langgraph\', \'stripe\', \'react-query\')',
      },
      topic: {
        type:        'string',
        description: 'Specific topic within the library (e.g. \'checkpointing\', \'webhooks\', \'useQuery\')',
      },
      max_tokens: {
        type:        'string',
        description: 'Max tokens of documentation to return (default 4000)',
      },
    },
    required: ['library', 'topic'],
  },
  async execute(args) {
    const library   = String(args['library']);
    const topic     = String(args['topic']);
    const maxTokens = parseInt(String(args['max_tokens'] ?? '4000'), 10);

    const libraryId = await resolveLibraryId(library);
    if (!libraryId) {
      return { found: false, message: `No Context7 documentation found for '${library}'.` };
    }

    const docs = await fetchDocs(libraryId, topic, maxTokens);
    return { found: true, library_id: libraryId, docs };
  },
};
