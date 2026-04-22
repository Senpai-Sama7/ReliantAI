import type { ClaudeAnalysisResponse } from '../types/document';
import { getThresholds, getEscalationRules } from '../utils/settings';

export class ClaudeService {
  async analyzeDocument(content: string, filename: string): Promise<ClaudeAnalysisResponse> {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content, filename,
        settings: {
          thresholds: getThresholds(),
          escalationRules: getEscalationRules(),
        },
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      throw new Error(err.error || `API error ${response.status}`);
    }

    return response.json();
  }
}

export const claudeService = new ClaudeService();
