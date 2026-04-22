import { useState } from 'react';
import { useDocuments } from '../../contexts/DocumentContext';
import { Button } from '../ui/Button';
import { Trash2, X, Sun, Moon, Monitor, Copy, Download } from 'lucide-react';
import { classNames } from '../../utils/formatters';
import { getThresholds, getEscalationRules, getTeamMembers, saveThresholds, saveEscalationRules, saveTeamMembers } from '../../utils/settings';
import type { Thresholds, EscalationRules } from '../../utils/settings';
import { useTheme } from '../../hooks/useTheme';
import { createShareCode, importFromShareCode } from '../../services/syncService';
import type { Document } from '../../types/document';

// no props needed

const themeOptions = [
  { value: 'system' as const, icon: Monitor, label: 'System' },
  { value: 'light' as const, icon: Sun, label: 'Light' },
  { value: 'dark' as const, icon: Moon, label: 'Dark' },
];

export function SettingsPanel() {
  const { state, dispatch } = useDocuments();
  const { theme, setTheme } = useTheme();
  const [thresholds, setThresholds] = useState(getThresholds);
  const [rules, setRules] = useState(getEscalationRules);
  const [team, setTeam] = useState(getTeamMembers);
  const [newMember, setNewMember] = useState('');
  const [shareCode, setShareCode] = useState('');
  const [syncCode, setSyncCode] = useState('');
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  const copySyncCode = async () => {
    try {
      const nextShareCode = await createShareCode();
      await navigator.clipboard.writeText(nextShareCode.shareToken);
      setShareCode(nextShareCode.shareToken);
      setSyncStatus(`Copied secure share code. Expires ${new Date(nextShareCode.expiresAt).toLocaleTimeString()}`);
    } catch (error) {
      setSyncStatus(error instanceof Error ? error.message : 'Unable to create share code');
    }
    setTimeout(() => setSyncStatus(null), 3000);
  };

  const importSyncCode = async () => {
    const code = syncCode.trim();
    if (!code) { setSyncStatus('Enter a share code'); return; }
    setSyncStatus('Pulling…');
    const docs = await importFromShareCode(code);
    if (docs && docs.length > 0) {
      dispatch({ type: 'SET_DOCUMENTS', payload: docs as Document[] });
      setSyncCode('');
      setSyncStatus(`Imported ${docs.length} document${docs.length !== 1 ? 's' : ''}`);
    } else if (docs && docs.length === 0) {
      setSyncStatus('Share code is valid, but no documents were available');
    } else {
      setSyncStatus('Invalid or expired share code');
    }
    setTimeout(() => setSyncStatus(null), 3000);
  };

  const saveT = (t: Thresholds) => { setThresholds(t); saveThresholds(t); };
  const saveR = (r: EscalationRules) => { setRules(r); saveEscalationRules(r); };

  const addMember = () => {
    const name = newMember.trim();
    if (!name || team.includes(name)) return;
    const next = [...team, name];
    setTeam(next); saveTeamMembers(next); setNewMember('');
  };
  const removeMember = (i: number) => {
    const next = team.filter((_, idx) => idx !== i);
    setTeam(next); saveTeamMembers(next);
  };

  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
      <h2 className="text-sm font-medium text-text-primary">{title}</h2>
      {children}
    </div>
  );

  const Toggle = ({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) => (
    <label className="flex items-center justify-between gap-3 cursor-pointer">
      <span className="text-xs text-text-secondary">{label}</span>
      <button type="button" onClick={() => onChange(!checked)}
        className={classNames('relative w-9 h-5 rounded-full transition-colors', checked ? 'bg-accent' : 'bg-border')}>
        <span className={classNames('absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform', checked ? 'left-[18px]' : 'left-0.5')} />
      </button>
    </label>
  );

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="font-heading text-2xl font-bold text-text-primary">Settings</h1>
        <p className="text-sm text-text-secondary mt-1">Manage data, preferences, and processing rules</p>
      </div>

      <Section title="Appearance">
        <div className="flex gap-2">
          {themeOptions.map(({ value, icon: Icon, label }) => (
            <button key={value} onClick={() => setTheme(value)}
              className={classNames(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-colors',
                theme === value ? 'bg-accent/10 text-accent border border-accent/30' : 'bg-bg border border-border text-text-secondary hover:border-border-hover'
              )}>
              <Icon className="w-3.5 h-3.5" />{label}
            </button>
          ))}
        </div>
      </Section>

      <Section title="Cross-Device Sync">
        <div className="flex items-center gap-2">
          <code className="flex-1 bg-bg border border-border rounded px-3 py-1.5 text-xs font-mono text-text-secondary truncate">
            {shareCode || 'Generate a short-lived share code to pair another browser'}
          </code>
          <Button variant="secondary" size="sm" onClick={copySyncCode} leftIcon={<Copy className="w-3.5 h-3.5" />}>Generate</Button>
        </div>
        <div className="flex gap-2">
          <input value={syncCode} onChange={e => setSyncCode(e.target.value)} placeholder="Enter secure share code from another device…"
            className="flex-1 bg-bg border border-border rounded px-3 py-1.5 text-sm text-text-primary placeholder:text-text-secondary/50 focus:border-border-hover focus:outline-none font-mono" />
          <Button variant="secondary" size="sm" onClick={importSyncCode} disabled={!syncCode.trim()} leftIcon={<Download className="w-3.5 h-3.5" />}>Import</Button>
        </div>
        {syncStatus && <p className="text-xs text-accent">{syncStatus}</p>}
        <p className="text-[11px] text-text-secondary">Share codes are signed and short-lived. Importing a valid code creates a local sync session for this browser.</p>
      </Section>

      <Section title="Priority Thresholds">
        {(['critical', 'high', 'medium'] as const).map(k => (
          <div key={k} className="flex items-center justify-between gap-4">
            <label className="text-xs text-text-secondary capitalize w-20">{k}</label>
            <div className="flex items-center gap-1">
              <span className="text-xs text-text-secondary">$</span>
              <input type="number" value={thresholds[k]}
                onChange={e => saveT({ ...thresholds, [k]: Math.max(0, Number(e.target.value)) })}
                className="w-28 bg-bg border border-border rounded px-2 py-1 text-sm font-mono text-text-primary focus:border-border-hover focus:outline-none" />
            </div>
          </div>
        ))}
        <p className="text-[11px] text-text-secondary">Documents below ${thresholds.medium.toLocaleString()} are classified as Low priority</p>
      </Section>

      <Section title="Escalation Rules">
        <Toggle label="Escalate all dispute documents" checked={rules.disputes} onChange={v => saveR({ ...rules, disputes: v })} />
        <Toggle label="Escalate if AI confidence below 80%" checked={rules.lowConfidence} onChange={v => saveR({ ...rules, lowConfidence: v })} />
        <Toggle label="Escalate if amount exceeds critical threshold" checked={rules.exceedsCritical} onChange={v => saveR({ ...rules, exceedsCritical: v })} />
        <Toggle label="Escalate if due date within 7 days" checked={rules.dueSoon} onChange={v => saveR({ ...rules, dueSoon: v })} />
      </Section>

      <Section title="Team Members">
        <div className="flex gap-2">
          <input value={newMember} onChange={e => setNewMember(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addMember()}
            placeholder="Add team member..."
            className="flex-1 bg-bg border border-border rounded px-3 py-1.5 text-sm text-text-primary placeholder:text-text-secondary/50 focus:border-border-hover focus:outline-none" />
          <Button variant="secondary" size="sm" onClick={addMember} disabled={!newMember.trim()}>Add</Button>
        </div>
        {team.length > 0 && (
          <div className="space-y-1">
            {team.map((name, i) => (
              <div key={i} className="flex items-center justify-between bg-bg border border-border rounded px-3 py-1.5">
                <span className="text-xs text-text-primary">{name}</span>
                <button onClick={() => removeMember(i)} className="text-text-secondary hover:text-danger"><X className="w-3.5 h-3.5" /></button>
              </div>
            ))}
          </div>
        )}
        <p className="text-[11px] text-text-secondary">Team members populate the assignee dropdown on document cards</p>
      </Section>


      <Section title="Data Management">
        <p className="text-xs text-text-secondary">{state.documents.length} document{state.documents.length !== 1 ? 's' : ''} stored in this browser</p>
        <Button variant="danger" size="sm" onClick={() => { if (confirm('Delete all documents? This cannot be undone.')) dispatch({ type: 'SET_DOCUMENTS', payload: [] }); }}
          leftIcon={<Trash2 className="w-3.5 h-3.5" />} disabled={state.documents.length === 0}>Clear All Documents</Button>
      </Section>
    </div>
  );
}
