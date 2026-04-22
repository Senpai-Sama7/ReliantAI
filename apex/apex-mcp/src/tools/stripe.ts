// apex-mcp/src/tools/stripe.ts
// Stripe read-only operations. No write access — least-privilege for agents.
// Write operations (charges, refunds) require explicit human approval via HITL.
import { ToolDefinition } from '../types';

const STRIPE_API = 'https://api.stripe.com/v1';
const KEY        = () => process.env['STRIPE_SECRET_KEY'] ?? '';

async function stripe(path: string, params?: Record<string, string>): Promise<unknown> {
  const key = KEY();
  if (!key) throw new Error('STRIPE_SECRET_KEY not configured.');

  const url = new URL(`${STRIPE_API}${path}`);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));

  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${key}` },
  });

  if (!res.ok) {
    const err = await res.json() as { error?: { message: string } };
    throw new Error(`Stripe error: ${err.error?.message ?? res.statusText}`);
  }
  return res.json();
}

export const stripeCustomerLookupTool: ToolDefinition = {
  name:        'stripe_customer_lookup',
  description: 'Look up a Stripe customer by email or ID. Read-only — no charges or mutations.',
  integration: 'stripe',
  inputSchema: {
    type: 'object',
    properties: {
      email: { type: 'string', description: 'Customer email address' },
      limit: { type: 'string', description: 'Max results (default 5)' },
    },
    required: ['email'],
  },
  async execute(args) {
    return stripe('/customers', {
      email: String(args['email']),
      limit: String(args['limit'] ?? '5'),
    });
  },
};

export const stripeInvoiceLookupTool: ToolDefinition = {
  name:        'stripe_invoice_lookup',
  description: 'List recent invoices for a Stripe customer. Read-only.',
  integration: 'stripe',
  inputSchema: {
    type: 'object',
    properties: {
      customer_id: { type: 'string', description: 'Stripe customer ID (starts with cus_)' },
      status:      {
        type:        'string',
        description: 'Filter by invoice status',
        enum:        ['draft', 'open', 'paid', 'uncollectible', 'void'],
      },
      limit: { type: 'string', description: 'Max results (default 10)' },
    },
    required: ['customer_id'],
  },
  async execute(args) {
    const params: Record<string, string> = {
      customer: String(args['customer_id']),
      limit:    String(args['limit'] ?? '10'),
    };
    if (args['status']) params['status'] = String(args['status']);
    return stripe('/invoices', params);
  },
};
