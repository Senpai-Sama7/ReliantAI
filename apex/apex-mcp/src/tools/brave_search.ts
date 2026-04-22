// apex-mcp/src/tools/brave_search.ts
// Brave Search API — privacy-respecting web search for Research agent.
import { ToolDefinition } from '../types';

const BRAVE_API = 'https://api.search.brave.com/res/v1/web/search';
const KEY       = () => process.env['BRAVE_SEARCH_API_KEY'] ?? '';

export const braveSearchTool: ToolDefinition = {
  name:        'brave_search',
  description: 'Search the web using Brave Search. Use for the Research agent to verify facts, find recent events, or gather evidence. Returns title, url, and description for top results.',
  integration: 'brave_search',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type:        'string',
        description: 'Search query',
      },
      count: {
        type:        'string',
        description: 'Number of results to return (default 5, max 20)',
      },
      freshness: {
        type:        'string',
        description: 'Limit results by date',
        enum:        ['pd', 'pw', 'pm', 'py'],  // past day/week/month/year
      },
    },
    required: ['query'],
  },
  async execute(args) {
    const key = KEY();
    if (!key) throw new Error('BRAVE_SEARCH_API_KEY not configured.');

    const url = new URL(BRAVE_API);
    url.searchParams.set('q',     String(args['query']));
    url.searchParams.set('count', String(args['count'] ?? '5'));
    if (args['freshness']) url.searchParams.set('freshness', String(args['freshness']));

    const res = await fetch(url.toString(), {
      headers: {
        Accept:            'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': key,
      },
    });

    if (!res.ok) throw new Error(`Brave Search error: ${res.status} ${res.statusText}`);

    const data = await res.json() as {
      web?: { results?: Array<{ title: string; url: string; description: string }> }
    };

    const results = (data.web?.results ?? []).map(r => ({
      title:       r.title,
      url:         r.url,
      description: r.description,
    }));

    return { query: args['query'], count: results.length, results };
  },
};
