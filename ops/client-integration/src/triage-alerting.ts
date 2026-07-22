import type { Handler } from "aws-lambda";
import type { ExceptionPayload } from "./types";

export interface TriageResult {
  statusCode: number;
  body: string;
}

function isExceptionPayload(value: unknown): value is ExceptionPayload {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.serviceName === "string" &&
    typeof candidate.errorMessage === "string" &&
    typeof candidate.severity === "string" &&
    typeof candidate.environment === "string"
  );
}

export function parseExceptionPayload(event: unknown): ExceptionPayload | null {
  if (!event || typeof event !== "object") return null;

  const record = event as Record<string, unknown>;
  if (typeof record.body === "string") {
    try {
      const parsed = JSON.parse(record.body) as unknown;
      return isExceptionPayload(parsed) ? parsed : null;
    } catch {
      return null;
    }
  }

  return isExceptionPayload(event) ? (event as ExceptionPayload) : null;
}

export function shouldSuppressAlert(payload: ExceptionPayload): boolean {
  return payload.environment !== "production" && payload.severity !== "CRITICAL";
}

export function buildSlackPayload(payload: ExceptionPayload) {
  const isCritical = payload.severity === "CRITICAL";
  const alertColor = isCritical ? "#E11D48" : "#F59E0B";
  const urgencyStatus = isCritical
    ? "CRITICAL SYSTEM EXCEPTION"
    : "INFRASTRUCTURE WARNING";

  const blocks: Array<Record<string, unknown>> = [
    {
      type: "section",
      text: {
        type: "mrkdwn",
        text: `*${urgencyStatus}*\n*Service:* \`${payload.serviceName}\` | *Environment:* \`${payload.environment.toUpperCase()}\``,
      },
    },
    {
      type: "section",
      text: {
        type: "mrkdwn",
        text: `*Message:* ${payload.errorMessage}\n*Detected At:* \`${payload.timestamp}\``,
      },
    },
  ];

  if (payload.stackTrace) {
    blocks.push({
      type: "section",
      text: {
        type: "mrkdwn",
        text: `*Stack Trace Preview:*\n\`\`\`${payload.stackTrace.substring(0, 500)}\`\`\``,
      },
    });
  }

  return {
    attachments: [
      {
        color: alertColor,
        blocks,
      },
    ],
  };
}

export async function processExceptionPayload(
  event: unknown,
  options: {
    webhookUrl?: string;
    fetchImpl?: typeof fetch;
  } = {},
): Promise<TriageResult> {
  const payload = parseExceptionPayload(event);
  if (!payload) {
    // Distinguish malformed JSON body from missing fields
    if (
      event &&
      typeof event === "object" &&
      typeof (event as { body?: unknown }).body === "string"
    ) {
      try {
        JSON.parse((event as { body: string }).body);
      } catch {
        return {
          statusCode: 400,
          body: JSON.stringify({ error: "Malformed JSON payload" }),
        };
      }
    }
    return {
      statusCode: 422,
      body: JSON.stringify({ error: "Missing mandatory triage variables" }),
    };
  }

  if (shouldSuppressAlert(payload)) {
    return {
      statusCode: 200,
      body: JSON.stringify({
        status: "Suppressed",
        reason: "Non-production environment",
      }),
    };
  }

  const webhookUrl =
    options.webhookUrl ?? process.env.NOTIFICATION_ROUTING_WEBHOOK;
  if (!webhookUrl) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: "Infrastructure routing unconfigured" }),
    };
  }

  const fetchImpl = options.fetchImpl ?? fetch;
  const slackPayload = buildSlackPayload(payload);

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const response = await fetchImpl(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(slackPayload),
      signal: controller.signal,
    });
    clearTimeout(timeout);

    const bodyText = await response.text();
    if (response.ok || bodyText.trim() === "ok") {
      return {
        statusCode: 200,
        body: JSON.stringify({ status: "Alert Dispatched" }),
      };
    }

    return {
      statusCode: 502,
      body: JSON.stringify({ error: "Failed to notify on-call engineering" }),
    };
  } catch {
    return {
      statusCode: 502,
      body: JSON.stringify({ error: "Failed to notify on-call engineering" }),
    };
  }
}

export const handler: Handler = async (event) => {
  console.log("Processing incoming infrastructure exception payload...");
  return processExceptionPayload(event);
};
