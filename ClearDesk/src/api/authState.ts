export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

let currentTokens: AuthTokens | null = null;

export function getAuthTokens(): AuthTokens | null {
  return currentTokens;
}

export function getAccessToken(): string | null {
  return currentTokens?.access_token || null;
}

export function setAuthTokens(tokens: AuthTokens | null): void {
  currentTokens = tokens;
}

export function clearAuthTokens(): void {
  currentTokens = null;
}
