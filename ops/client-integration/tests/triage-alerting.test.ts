import { describe, expect, it, vi } from "vitest";
import {
  buildSlackPayload,
  parseExceptionPayload,
  processExceptionPayload,
  shouldSuppressAlert,
} from "../src/triage-alerting";
import type { ExceptionPayload } from "../src/types";

const basePayload: ExceptionPayload = {
  environment: "production",
  serviceName: "intake-api",
  errorMessage: "webhook timeout",
  severity: "CRITICAL",
  timestamp: "2026-07-22T12:00:00Z",
};

describe("parseExceptionPayload", () => {
  it("parses API Gateway style body", () => {
    const parsed = parseExceptionPayload({ body: JSON.stringify(basePayload) });
    expect(parsed?.serviceName).toBe("intake-api");
  });

  it("returns null on malformed JSON", () => {
    expect(parseExceptionPayload({ body: "{not-json" })).toBeNull();
  });
});

describe("shouldSuppressAlert", () => {
  it("suppresses non-critical staging alerts", () => {
    expect(
      shouldSuppressAlert({
        ...basePayload,
        environment: "staging",
        severity: "WARNING",
      }),
    ).toBe(true);
  });

  it("keeps critical alerts in staging", () => {
    expect(
      shouldSuppressAlert({
        ...basePayload,
        environment: "staging",
        severity: "CRITICAL",
      }),
    ).toBe(false);
  });
});

describe("processExceptionPayload", () => {
  it("returns 422 when required fields missing", async () => {
    const result = await processExceptionPayload({ hello: "world" });
    expect(result.statusCode).toBe(422);
  });

  it("returns 400 on malformed JSON body", async () => {
    const result = await processExceptionPayload({ body: "{broken" });
    expect(result.statusCode).toBe(400);
  });

  it("dispatches Slack alert for production critical", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response("ok", { status: 200 }));
    const result = await processExceptionPayload(basePayload, {
      webhookUrl: "https://hooks.slack.com/services/T/B/x",
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });
    expect(result.statusCode).toBe(200);
    expect(JSON.parse(result.body).status).toBe("Alert Dispatched");
    expect(fetchImpl).toHaveBeenCalledOnce();
  });

  it("suppresses non-prod warnings", async () => {
    const fetchImpl = vi.fn();
    const result = await processExceptionPayload(
      { ...basePayload, environment: "development", severity: "INFO" },
      {
        webhookUrl: "https://hooks.slack.com/services/T/B/x",
        fetchImpl: fetchImpl as unknown as typeof fetch,
      },
    );
    expect(result.statusCode).toBe(200);
    expect(JSON.parse(result.body).status).toBe("Suppressed");
    expect(fetchImpl).not.toHaveBeenCalled();
  });
});

describe("buildSlackPayload", () => {
  it("includes stack trace when provided", () => {
    const payload = buildSlackPayload({
      ...basePayload,
      stackTrace: "Error: boom\n    at handler",
    });
    const blocks = payload.attachments[0].blocks as Array<{ text?: { text: string } }>;
    expect(blocks.some((b) => b.text?.text.includes("Stack Trace Preview"))).toBe(true);
  });
});
