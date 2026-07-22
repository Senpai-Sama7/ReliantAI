import type { ValidationResult } from "../types";

const SLACK_HOOK_PATTERN =
  /^https:\/\/hooks\.slack\.com\/services\/[A-Z0-9]+\/[A-Z0-9]+\/[A-Za-z0-9]+$/;

/**
 * Validates an incoming Slack webhook URL.
 * Dry-run mode only checks URL shape (safe for CI without posting).
 */
export async function validateSlackWebhook(
  webhookUrl: string,
  options: { dryRun?: boolean; fetchImpl?: typeof fetch } = {},
): Promise<ValidationResult> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const dryRun = options.dryRun ?? false;
  const started = Date.now();

  if (!webhookUrl.trim()) {
    return {
      service: "Emergency Slack Dispatch Route",
      isValid: false,
      message: "NOTIFICATION_ROUTING_WEBHOOK is missing.",
      latencyMs: null,
    };
  }

  if (!SLACK_HOOK_PATTERN.test(webhookUrl)) {
    return {
      service: "Emergency Slack Dispatch Route",
      isValid: false,
      message: "Webhook URL does not match hooks.slack.com/services/... shape.",
      latencyMs: null,
    };
  }

  if (dryRun) {
    return {
      service: "Emergency Slack Dispatch Route",
      isValid: true,
      message: "Dry-run: webhook URL shape verified (no handshake posted).",
      latencyMs: Date.now() - started,
    };
  }

  try {
    const response = await fetchImpl(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: "Reliant AI System Pipeline Diagnostics: secure connection verified.",
      }),
    });

    const latencyMs = Date.now() - started;
    const bodyText = await response.text();

    if (response.ok || bodyText.trim() === "ok") {
      return {
        service: "Emergency Slack Dispatch Route",
        isValid: true,
        message: "Webhook handshake complete. High-urgency notifications active.",
        latencyMs,
      };
    }

    return {
      service: "Emergency Slack Dispatch Route",
      isValid: false,
      message: `Routing rejection (${response.status}): ${bodyText.slice(0, 200)}`,
      latencyMs,
    };
  } catch (error) {
    return {
      service: "Emergency Slack Dispatch Route",
      isValid: false,
      message: `Payload transmission failure: ${error instanceof Error ? error.message : String(error)}`,
      latencyMs: null,
    };
  }
}
