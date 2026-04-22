// apex-mcp/src/tools/slack.ts
// Slack message posting via Web API.
import { ToolDefinition } from '../types';

const SLACK_API = 'https://slack.com/api';
const TOKEN     = () => process.env['SLACK_BOT_TOKEN'] ?? '';

export const slackPostTool: ToolDefinition = {
  name:        'slack_post',
  description: 'Post a message to a Slack channel. Use for human notifications, alerts, or status updates after approved APEX decisions.',
  integration: 'slack',
  inputSchema: {
    type: 'object',
    properties: {
      channel: {
        type:        'string',
        description: 'Slack channel ID or name (e.g. #apex-alerts)',
      },
      text: {
        type:        'string',
        description: 'Message text. Supports Slack mrkdwn formatting.',
      },
      thread_ts: {
        type:        'string',
        description: 'Optional: reply to a specific message thread',
      },
    },
    required: ['channel', 'text'],
  },
  async execute(args) {
    const token = TOKEN();
    if (!token) throw new Error('SLACK_BOT_TOKEN not configured.');

    const body: Record<string, unknown> = {
      channel: String(args['channel']),
      text:    String(args['text']),
    };
    if (args['thread_ts']) body['thread_ts'] = String(args['thread_ts']);

    const res = await fetch(`${SLACK_API}/chat.postMessage`, {
      method:  'POST',
      headers: {
        Authorization:  `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await res.json() as { ok: boolean; error?: string; ts?: string };
    if (!data.ok) throw new Error(`Slack API error: ${data.error}`);
    return { posted: true, ts: data.ts, channel: args['channel'] };
  },
};
