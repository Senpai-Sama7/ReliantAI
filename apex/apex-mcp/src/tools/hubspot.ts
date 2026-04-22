// apex-mcp/src/tools/hubspot.ts
// HubSpot CRM operations. Read-only by default; write ops require explicit args.
import { ToolDefinition } from '../types';

const HUBSPOT_API = 'https://api.hubapi.com';
const TOKEN      = () => process.env['HUBSPOT_ACCESS_TOKEN'] ?? '';

async function hs(path: string, method = 'GET', body?: unknown): Promise<unknown> {
  const token = TOKEN();
  if (!token) throw new Error('HUBSPOT_ACCESS_TOKEN not configured.');

  const res = await fetch(`${HUBSPOT_API}${path}`, {
    method,
    headers: {
      Authorization:  `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HubSpot API error ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

export const hubspotSearchTool: ToolDefinition = {
  name:        'hubspot_search',
  description: 'Search HubSpot CRM for contacts, companies, or deals by keyword.',
  integration: 'hubspot',
  inputSchema: {
    type: 'object',
    properties: {
      object_type: {
        type:        'string',
        description: 'CRM object type',
        enum:        ['contacts', 'companies', 'deals'],
      },
      query: {
        type:        'string',
        description: 'Search query string',
      },
      limit: {
        type:        'string',
        description: 'Max results (default 10)',
      },
    },
    required: ['object_type', 'query'],
  },
  async execute(args) {
    const objectType = String(args['object_type']);
    const query      = String(args['query']);
    const limit      = parseInt(String(args['limit'] ?? '10'), 10);

    return hs(`/crm/v3/objects/${objectType}/search`, 'POST', {
      query,
      limit,
      properties: ['firstname', 'lastname', 'email', 'company', 'dealname', 'amount'],
    });
  },
};

export const hubspotCreateDealTool: ToolDefinition = {
  name:        'hubspot_create_deal',
  description: 'Create a new deal in HubSpot CRM. Use only after APEX decision is approved.',
  integration: 'hubspot',
  inputSchema: {
    type: 'object',
    properties: {
      dealname:  { type: 'string', description: 'Deal name' },
      amount:    { type: 'string', description: 'Deal value in USD' },
      stage:     { type: 'string', description: 'Pipeline stage (e.g. appointmentscheduled)' },
      owner_id:  { type: 'string', description: 'HubSpot owner ID' },
    },
    required: ['dealname', 'amount', 'stage'],
  },
  async execute(args) {
    return hs('/crm/v3/objects/deals', 'POST', {
      properties: {
        dealname: String(args['dealname']),
        amount:   String(args['amount']),
        dealstage: String(args['stage']),
        ...(args['owner_id'] ? { hubspot_owner_id: String(args['owner_id']) } : {}),
      },
    });
  },
};
