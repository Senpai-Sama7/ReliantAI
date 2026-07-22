import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  loadCredentialEnv,
  runCredentialAudit,
} from "../src/validate-credentials";
import { validateHubSpot } from "../src/validators/hubspot";
import { validateScheduling } from "../src/validators/calcom";
import { validateSlackWebhook } from "../src/validators/slack";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("loadCredentialEnv", () => {
  it("defaults Slack dry-run to true", () => {
    const env = loadCredentialEnv({
      HUBSPOT_APP_ACCESS_TOKEN: "hs",
      SCHEDULING_API_KEY: "cal",
      NOTIFICATION_ROUTING_WEBHOOK: "https://hooks.slack.com/services/T/B/x",
    });
    expect(env.slackDryRun).toBe(true);
  });

  it("allows disabling Slack dry-run", () => {
    const env = loadCredentialEnv({ VALIDATE_SLACK_DRY_RUN: "false" });
    expect(env.slackDryRun).toBe(false);
  });
});

describe("validateHubSpot", () => {
  it("fails when token missing", async () => {
    const result = await validateHubSpot("");
    expect(result.isValid).toBe(false);
    expect(result.message).toMatch(/missing/i);
  });

  it("passes on 200", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200, { results: [] }));
    const result = await validateHubSpot("token", fetchImpl as unknown as typeof fetch);
    expect(result.isValid).toBe(true);
    expect(fetchImpl).toHaveBeenCalledWith(
      expect.stringContaining("api.hubapi.com/crm/v3/objects/contacts"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer token",
        }),
      }),
    );
  });

  it("fails on 401", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(401, { message: "unauthorized" }));
    const result = await validateHubSpot("bad", fetchImpl as unknown as typeof fetch);
    expect(result.isValid).toBe(false);
    expect(result.message).toMatch(/401/);
  });
});

describe("validateScheduling", () => {
  it("calls Cal.com /v1/me with apiKey", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200, { user: { id: 1 } }));
    const result = await validateScheduling("cal_key", fetchImpl as unknown as typeof fetch);
    expect(result.isValid).toBe(true);
    expect(fetchImpl).toHaveBeenCalledWith(
      expect.stringContaining("https://api.cal.com/v1/me?apiKey=cal_key"),
      expect.any(Object),
    );
  });

  it("fails when key missing", async () => {
    const result = await validateScheduling("  ");
    expect(result.isValid).toBe(false);
  });
});

describe("validateSlackWebhook", () => {
  it("rejects malformed URLs", async () => {
    const result = await validateSlackWebhook("https://example.com/hook");
    expect(result.isValid).toBe(false);
  });

  it("dry-run accepts valid shape without posting", async () => {
    const fetchImpl = vi.fn();
    const result = await validateSlackWebhook(
      "https://hooks.slack.com/services/T000/B000/XXXX",
      { dryRun: true, fetchImpl: fetchImpl as unknown as typeof fetch },
    );
    expect(result.isValid).toBe(true);
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("posts handshake when dry-run disabled", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response("ok", { status: 200 }));
    const result = await validateSlackWebhook(
      "https://hooks.slack.com/services/T000/B000/XXXX",
      { dryRun: false, fetchImpl: fetchImpl as unknown as typeof fetch },
    );
    expect(result.isValid).toBe(true);
    expect(fetchImpl).toHaveBeenCalledOnce();
  });
});

describe("runCredentialAudit", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("aggregates all three validators", async () => {
    const fetchImpl = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes("hubapi.com")) return jsonResponse(200, { results: [] });
      if (url.includes("cal.com")) return jsonResponse(200, { user: {} });
      return new Response("ok", { status: 200 });
    });

    const report = await runCredentialAudit(
      {
        hubspotToken: "hs",
        schedulingKey: "cal",
        slackWebhookUrl: "https://hooks.slack.com/services/T000/B000/XXXX",
        slackDryRun: true,
      },
      fetchImpl as unknown as typeof fetch,
    );

    expect(report).toHaveLength(3);
    expect(report.every((r) => r.isValid)).toBe(true);
  });
});
