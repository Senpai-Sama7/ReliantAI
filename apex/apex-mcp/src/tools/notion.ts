// apex-mcp/src/tools/notion.ts
// Notion page creation and database search.
import { ToolDefinition } from '../types';

const NOTION_API = 'https://api.notion.com/v1';
const TOKEN      = () => process.env['NOTION_TOKEN'] ?? '';
const VERSION    = '2022-06-28';

async function notion(path: string, method = 'GET', body?: unknown): Promise<unknown> {
  const token = TOKEN();
  if (!token) throw new Error('NOTION_TOKEN not configured.');

  const res = await fetch(`${NOTION_API}${path}`, {
    method,
    headers: {
      Authorization:    `Bearer ${token}`,
      'Content-Type':   'application/json',
      'Notion-Version': VERSION,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Notion API error ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

export const notionSearchTool: ToolDefinition = {
  name:        'notion_search',
  description: 'Search Notion workspace for pages, databases, or blocks.',
  integration: 'notion',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type:        'string',
        description: 'Search query',
      },
      filter_type: {
        type:        'string',
        description: 'Object type filter',
        enum:        ['page', 'database'],
      },
    },
    required: ['query'],
  },
  async execute(args) {
    const body: Record<string, unknown> = { query: String(args['query']) };
    if (args['filter_type']) {
      body['filter'] = { value: String(args['filter_type']), property: 'object' };
    }
    return notion('/search', 'POST', body);
  },
};

export const notionCreatePageTool: ToolDefinition = {
  name:        'notion_create_page',
  description: 'Create a new page in a Notion database. Use only after APEX decision is approved.',
  integration: 'notion',
  inputSchema: {
    type: 'object',
    properties: {
      database_id: { type: 'string', description: 'Notion database ID (from database URL)' },
      title:       { type: 'string', description: 'Page title' },
      content:     { type: 'string', description: 'Page body content as plain text' },
    },
    required: ['database_id', 'title'],
  },
  async execute(args) {
    return notion('/pages', 'POST', {
      parent: { database_id: String(args['database_id']) },
      properties: {
        title: {
          title: [{ text: { content: String(args['title']) } }],
        },
      },
      children: args['content']
        ? [{
            object: 'block',
            type:   'paragraph',
            paragraph: {
              rich_text: [{ type: 'text', text: { content: String(args['content']) } }],
            },
          }]
        : [],
    });
  },
};
