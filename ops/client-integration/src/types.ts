export interface ValidationResult {
  service: string;
  isValid: boolean;
  message: string;
  latencyMs: number | null;
}

export type EnvironmentName = "production" | "staging" | "development";

export type Severity = "CRITICAL" | "WARNING" | "INFO";

export interface ExceptionPayload {
  environment: EnvironmentName;
  serviceName: string;
  errorMessage: string;
  stackTrace?: string;
  severity: Severity;
  timestamp: string;
}

export interface CredentialEnv {
  hubspotToken: string;
  schedulingKey: string;
  slackWebhookUrl: string;
  /** When true, Slack URL shape is checked without posting a handshake. */
  slackDryRun: boolean;
}
