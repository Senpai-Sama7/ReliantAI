// apex-mcp/src/tools/zapier.ts
// Zapier outbound action bus. APEX decisions become real-world events
// (CRM updates, emails, Slack alerts) without agents needing direct system access.
import { ToolDefinition } from '../types';

const ZAPIER_WEBHOOK_BASE = process.env['ZAPIER_WEBHOOK_BASE_URL'] ?? '';

export const zapierTool: ToolDefinition = {
  name:        'zapier_trigger',
  description: 'Fires a Zapier webhook to execute a real-world action (e.g. create CRM record, send email, post Slack alert). Use for outbound actions after APEX decisions are approved.',
  integration: 'zapier',
  inputSchema: {
    type: 'object',
    properties: {
      zap_name: {
        type:        'string',
        description: 'Name of the Zap to trigger (must match a registered webhook key in env)',
      },
      payload: {
        type:        'string',
        description: 'JSON string of data to send to the Zap',
      },
    },
    required: ['zap_name', 'payload'],
  },
  async execute(args) {
    if (!ZAPIER_WEBHOOK_BASE) {
      throw new Error('ZAPIER_WEBHOOK_BASE_URL not configured. Set it in .env.');
    }

    const zapName = String(args['zap_name']);
    const webhookKey = process.env[`ZAPIER_WEBHOOK_${zapName.toUpperCase()}`];
    if (!webhookKey) {
      throw new Error(`No webhook key found for zap '${zapName}'. Add ZAPIER_WEBHOOK_${zapName.toUpperCase()} to .env.`);
    }

    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(String(args['payload']));
    } catch {
      throw new Error('payload must be valid JSON');
    }

    const res = await fetch(`${ZAPIER_WEBHOOK_BASE}/${webhookKey}`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ ...payload, _apex_source: 'apex-mcp' }),
    });

    if (!res.ok) {
      throw new Error(`Zapier webhook failed: ${res.status} ${res.statusText}`);
    }

    return { triggered: true, zap: zapName, status: res.status };
  },
};
