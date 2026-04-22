interface ShareSession {
  shareToken: string;
  expiresAt: string;
}

export async function initSyncSession(): Promise<boolean> {
  try {
    const response = await fetch('/api/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ action: 'init' }),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function createShareCode(): Promise<ShareSession> {
  const initialized = await initSyncSession();
  if (!initialized) {
    throw new Error('Secure sync is unavailable');
  }

  const response = await fetch('/api/documents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ action: 'share' }),
  });
  const data = await response.json();

  if (!response.ok || !data.shareToken) {
    throw new Error(data.error || 'Failed to create share code');
  }

  return {
    shareToken: data.shareToken,
    expiresAt: data.expiresAt,
  };
}

export async function syncToKV(documents: unknown[]): Promise<void> {
  try {
    const initialized = await initSyncSession();
    if (!initialized) {
      return;
    }

    await fetch('/api/documents', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ documents }),
    });
  } catch {
    // background sync is best-effort only
  }
}

export async function pullFromKV(): Promise<unknown[] | null> {
  try {
    const initialized = await initSyncSession();
    if (!initialized) {
      return null;
    }

    const response = await fetch('/api/documents', {
      credentials: 'include',
    });
    if (!response.ok) {
      return null;
    }

    const { documents } = await response.json();
    return Array.isArray(documents) && documents.length > 0 ? documents : null;
  } catch {
    return null;
  }
}

export async function importFromShareCode(shareToken: string): Promise<unknown[] | null> {
  try {
    const response = await fetch('/api/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ action: 'import', shareToken }),
    });
    if (!response.ok) {
      return null;
    }

    const { documents } = await response.json();
    return Array.isArray(documents) ? documents : null;
  } catch {
    return null;
  }
}
