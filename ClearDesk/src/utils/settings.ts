export interface Thresholds {
  critical: number;
  high: number;
  medium: number;
}

export interface EscalationRules {
  disputes: boolean;
  lowConfidence: boolean;
  exceedsCritical: boolean;
  dueSoon: boolean;
}

const KEYS = {
  thresholds: 'cleardesk_thresholds',
  escalation: 'cleardesk_escalation_rules',
  team: 'cleardesk_team_members',
} as const;

const DEFAULTS = {
  thresholds: { critical: 50000, high: 10000, medium: 1000 } as Thresholds,
  escalation: { disputes: true, lowConfidence: true, exceedsCritical: true, dueSoon: false } as EscalationRules,
  team: [] as string[],
};

function load<T>(key: string, fallback: T): T {
  try { return JSON.parse(localStorage.getItem(key) || '') as T; }
  catch { return fallback; }
}

export const getThresholds = () => load(KEYS.thresholds, DEFAULTS.thresholds);
export const getEscalationRules = () => load(KEYS.escalation, DEFAULTS.escalation);
export const getTeamMembers = () => load(KEYS.team, DEFAULTS.team);

export const saveThresholds = (v: Thresholds) => localStorage.setItem(KEYS.thresholds, JSON.stringify(v));
export const saveEscalationRules = (v: EscalationRules) => localStorage.setItem(KEYS.escalation, JSON.stringify(v));
export const saveTeamMembers = (v: string[]) => localStorage.setItem(KEYS.team, JSON.stringify(v));
