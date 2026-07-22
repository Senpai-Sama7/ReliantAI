import type { CredentialEnv, ValidationResult } from "./types";
import { validateHubSpot } from "./validators/hubspot";
import { validateScheduling } from "./validators/calcom";
import { validateSlackWebhook } from "./validators/slack";

export function loadCredentialEnv(
  env: NodeJS.ProcessEnv = process.env,
): CredentialEnv {
  return {
    hubspotToken: env.HUBSPOT_APP_ACCESS_TOKEN ?? "",
    schedulingKey: env.SCHEDULING_API_KEY ?? "",
    slackWebhookUrl: env.NOTIFICATION_ROUTING_WEBHOOK ?? "",
    slackDryRun:
      (env.VALIDATE_SLACK_DRY_RUN ?? "true").toLowerCase() !== "false",
  };
}

export async function runCredentialAudit(
  credentials: CredentialEnv,
  fetchImpl: typeof fetch = fetch,
): Promise<ValidationResult[]> {
  return Promise.all([
    validateHubSpot(credentials.hubspotToken, fetchImpl),
    validateScheduling(credentials.schedulingKey, fetchImpl),
    validateSlackWebhook(credentials.slackWebhookUrl, {
      dryRun: credentials.slackDryRun,
      fetchImpl,
    }),
  ]);
}

export function printAuditReport(report: ValidationResult[]): boolean {
  console.log("=== SYSTEM AUDIT REPORT ===");
  let overallSuccess = true;

  for (const result of report) {
    const statusIcon = result.isValid ? "PASS" : "FAIL";
    const latency =
      result.latencyMs === null ? "n/a" : `${result.latencyMs}ms`;
    if (!result.isValid) overallSuccess = false;
    console.log(
      `[${statusIcon}] ${result.service} (${latency}): ${result.message}`,
    );
  }

  console.log("==========================");
  if (overallSuccess) {
    console.log("STATUS: PRODUCTION READY. Credentials approved.");
  } else {
    console.log("STATUS: CRITICAL ERROR. One or more pipelines failed.");
  }

  return overallSuccess;
}

export async function runFullTechnicalAudit(
  env: NodeJS.ProcessEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<boolean> {
  console.log("Initializing credential integrity audit...\n");
  const report = await runCredentialAudit(loadCredentialEnv(env), fetchImpl);
  return printAuditReport(report);
}

const isDirectRun =
  typeof require !== "undefined" &&
  typeof module !== "undefined" &&
  require.main === module;

if (isDirectRun) {
  runFullTechnicalAudit()
    .then((ok) => process.exit(ok ? 0 : 1))
    .catch((error) => {
      console.error("Audit crashed:", error);
      process.exit(1);
    });
}
