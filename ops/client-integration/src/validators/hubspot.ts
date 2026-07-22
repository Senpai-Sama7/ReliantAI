import type { ValidationResult } from "../types";

const HUBSPOT_CONTACTS_URL =
  "https://api.hubapi.com/crm/v3/objects/contacts?limit=1";

/**
 * Validates a HubSpot private app access token with a lightweight contacts read.
 */
export async function validateHubSpot(
  token: string,
  fetchImpl: typeof fetch = fetch,
): Promise<ValidationResult> {
  const started = Date.now();

  if (!token.trim()) {
    return {
      service: "HubSpot CRM",
      isValid: false,
      message: "HUBSPOT_APP_ACCESS_TOKEN is missing.",
      latencyMs: null,
    };
  }

  try {
    const response = await fetchImpl(HUBSPOT_CONTACTS_URL, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
    });

    const latencyMs = Date.now() - started;

    if (response.ok) {
      return {
        service: "HubSpot CRM",
        isValid: true,
        message: "Authenticated. Contacts read access verified.",
        latencyMs,
      };
    }

    const body = await response.text();
    return {
      service: "HubSpot CRM",
      isValid: false,
      message: `Authentication failed (${response.status}): ${body.slice(0, 200) || response.statusText}`,
      latencyMs,
    };
  } catch (error) {
    return {
      service: "HubSpot CRM",
      isValid: false,
      message: `Connection error: ${error instanceof Error ? error.message : String(error)}`,
      latencyMs: null,
    };
  }
}
