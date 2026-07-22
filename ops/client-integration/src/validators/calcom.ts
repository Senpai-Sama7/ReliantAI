import type { ValidationResult } from "../types";

const CAL_COM_ME_URL = "https://api.cal.com/v1/me";

/**
 * Validates a Cal.com API key against the /v1/me endpoint.
 */
export async function validateScheduling(
  apiKey: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ValidationResult> {
  const started = Date.now();

  if (!apiKey.trim()) {
    return {
      service: "Scheduling Engine (Cal.com)",
      isValid: false,
      message: "SCHEDULING_API_KEY is missing.",
      latencyMs: null,
    };
  }

  try {
    const url = new URL(CAL_COM_ME_URL);
    url.searchParams.set("apiKey", apiKey);

    const response = await fetchImpl(url.toString(), {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    const latencyMs = Date.now() - started;

    if (response.ok) {
      return {
        service: "Scheduling Engine (Cal.com)",
        isValid: true,
        message: "Calendar sync active. Availability endpoint responsive.",
        latencyMs,
      };
    }

    const body = await response.text();
    return {
      service: "Scheduling Engine (Cal.com)",
      isValid: false,
      message: `Connection rejected (${response.status}): ${body.slice(0, 200) || response.statusText}`,
      latencyMs,
    };
  } catch (error) {
    return {
      service: "Scheduling Engine (Cal.com)",
      isValid: false,
      message: `Connection dropped: ${error instanceof Error ? error.message : String(error)}`,
      latencyMs: null,
    };
  }
}
