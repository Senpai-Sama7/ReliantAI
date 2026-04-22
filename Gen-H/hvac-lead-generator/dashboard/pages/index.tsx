import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

interface Campaign {
  id: string;
  name: string;
  target_locations: string[];
  min_rating: number;
  min_review_count: number;
  results_per_location: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
}

interface Lead {
  id: string;
  company_name: string;
  phone: string;
  email: string;
  address: string;
  rating: number;
  review_count: number;
  outreach_status: 'new' | 'contacted' | 'interested' | 'not_interested';
  google_maps_url?: string;
}

interface GeneratorDefaults {
  target_locations: string[];
  min_rating: number;
  min_review_count: number;
  results_per_location: number;
  google_sheet_id: string;
  google_sheet_url: string;
  has_composio_api_key: boolean;
  composio_entity_id: string;
}

interface ArtifactSummary {
  file: string;
  path: string;
  mode: string;
  generated_at: string | null;
  total_leads_found: number | null;
  sheet_name: string | null;
  spreadsheet_url: string | null;
  dry_run: boolean;
  sample_leads: Lead[];
  is_promoted?: boolean;
  promoted_campaign?: {
    id: string;
    name: string;
    status: Campaign['status'];
  } | null;
}

interface GeneratorRunResult {
  command: string[];
  exitCode: number | null;
  stdout: string;
  stderr: string;
  artifactPath: string;
  artifact: Record<string, any> | null;
}

type ReadinessLevel = 'healthy' | 'warning' | 'error';

interface ReadinessCheck {
  key: string;
  label: string;
  status: ReadinessLevel;
  detail: string;
  meta?: Record<string, any>;
}

interface ReadinessSnapshot {
  checked_at: string;
  ready_for_profile: boolean;
  ready_for_preview: boolean;
  ready_for_export: boolean;
  ready_for_crm: boolean;
  dependencies: ReadinessCheck[];
  preflight?: {
    token: string;
    expires_at: string;
  };
}

interface ConfigFormState {
  apiKey: string;
  entityId: string;
  targetLocations: string;
  minRating: number;
  minReviewCount: number;
  resultsPerLocation: number;
  googleSheetId: string;
  googleSheetUrl: string;
}

type HistoryFilter = 'all' | 'ready' | 'promoted';
type HistorySort = 'newest' | 'most-leads' | 'ready-first' | 'oldest';

const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/api';

const statusTone: Record<Campaign['status'], string> = {
  pending: 'bg-amber-500/15 text-amber-200 border-amber-400/30',
  running: 'bg-sky-500/15 text-sky-200 border-sky-400/30',
  completed: 'bg-emerald-500/15 text-emerald-200 border-emerald-400/30',
  failed: 'bg-rose-500/15 text-rose-200 border-rose-400/30',
};

const emptyForm: ConfigFormState = {
  apiKey: '',
  entityId: '',
  targetLocations: '',
  minRating: 3.5,
  minReviewCount: 5,
  resultsPerLocation: 20,
  googleSheetId: '',
  googleSheetUrl: '',
};

const formatTime = (value?: string | null) => {
  if (!value) {
    return 'Not run yet';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

const splitLocations = (value: string) =>
  value
    .split(';')
    .map((item) => item.trim())
    .filter(Boolean);

export default function LeadGeneratorDashboard() {
  const [form, setForm] = useState<ConfigFormState>(emptyForm);
  const [defaults, setDefaults] = useState<GeneratorDefaults | null>(null);
  const [history, setHistory] = useState<ArtifactSummary[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [execution, setExecution] = useState<GeneratorRunResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyMode, setBusyMode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<ReadinessSnapshot | null>(null);
  const [readinessError, setReadinessError] = useState<string | null>(null);
  const [readinessLoading, setReadinessLoading] = useState(false);
  const [preflightDirty, setPreflightDirty] = useState(false);
  const [campaignName, setCampaignName] = useState('');
  const [historyFilter, setHistoryFilter] = useState<HistoryFilter>('all');
  const [historySort, setHistorySort] = useState<HistorySort>('ready-first');
  const [historyQuery, setHistoryQuery] = useState('');

  useEffect(() => {
    void hydrate();
  }, []);

  const hydrate = async () => {
    setLoading(true);
    setError(null);
    try {
      const [configResult, campaignResult] = await Promise.allSettled([
        axios.get(`${apiBase}/system/config`),
        axios.get(`${apiBase}/campaigns`),
      ]);

      if (configResult.status !== 'fulfilled') {
        throw new Error('Config unavailable');
      }

      const incomingDefaults = configResult.value.data.data.defaults as GeneratorDefaults;
      setDefaults(incomingDefaults);
      setHistory(configResult.value.data.data.artifacts || []);
      const initialForm = {
        apiKey: '',
        entityId: incomingDefaults.composio_entity_id || '',
        targetLocations: incomingDefaults.target_locations.join('; '),
        minRating: incomingDefaults.min_rating,
        minReviewCount: incomingDefaults.min_review_count,
        resultsPerLocation: incomingDefaults.results_per_location,
        googleSheetId: incomingDefaults.google_sheet_id,
        googleSheetUrl: incomingDefaults.google_sheet_url,
      };
      setForm(initialForm);
      await checkReadiness(initialForm);

      if (campaignResult.status === 'fulfilled') {
        setCampaigns(campaignResult.value.data.data || []);
      } else {
        setCampaigns([]);
        setError('Generator controls are available, but campaign tracking is offline because the Postgres-backed API query failed.');
      }
    } catch (requestError) {
      setError('Unable to load dashboard data. Confirm the lead API is running.');
    } finally {
      setLoading(false);
    }
  };

  const fetchLeads = async (campaignId: string) => {
    try {
      const response = await axios.get(`${apiBase}/campaigns/${campaignId}/leads`);
      setLeads(response.data.data || []);
    } catch (requestError) {
      setError('Unable to load saved leads for the selected campaign.');
    }
  };

  const refreshHistory = async () => {
    const response = await axios.get(`${apiBase}/system/history`);
    const nextHistory = response.data.data || [];
    setHistory(nextHistory);
    return nextHistory as ArtifactSummary[];
  };

  const refreshCampaigns = async () => {
    const response = await axios.get(`${apiBase}/campaigns`);
    const nextCampaigns = response.data.data || [];
    setCampaigns(nextCampaigns);
    return nextCampaigns as Campaign[];
  };

  const selectCampaignRecord = async (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    await fetchLeads(campaign.id);
  };

  const openPromotedCampaign = async (campaignRef?: ArtifactSummary['promoted_campaign'] | Campaign | null) => {
    if (!campaignRef?.id) {
      return;
    }

    const existing = campaigns.find((campaign) => campaign.id === campaignRef.id);
    if (existing) {
      await selectCampaignRecord(existing);
      return;
    }

    const nextCampaigns = await refreshCampaigns();
    const selected = nextCampaigns.find((campaign) => campaign.id === campaignRef.id);
    if (selected) {
      await selectCampaignRecord(selected);
    }
  };

  const updateField = <K extends keyof ConfigFormState>(key: K, value: ConfigFormState[K]) => {
    setPreflightDirty(true);
    setForm((current) => ({ ...current, [key]: value }));
  };

  const buildPayloadFromState = (state: ConfigFormState) => ({
    ...(state.apiKey.trim() ? { apiKey: state.apiKey.trim() } : {}),
    ...(state.entityId.trim() ? { entityId: state.entityId.trim() } : {}),
    target_locations: splitLocations(state.targetLocations),
    min_rating: Number(state.minRating),
    min_review_count: Number(state.minReviewCount),
    results_per_location: Number(state.resultsPerLocation),
    google_sheet_id: state.googleSheetId.trim(),
    google_sheet_url: state.googleSheetUrl.trim(),
  });

  const buildPayload = () => buildPayloadFromState(form);

  const checkReadiness = async (state: ConfigFormState = form) => {
    setReadinessLoading(true);
    setReadinessError(null);

    try {
      const response = await axios.post(`${apiBase}/system/readiness`, buildPayloadFromState(state));
      const snapshot = response.data.data as ReadinessSnapshot;
      setReadiness(snapshot);
      setPreflightDirty(false);
      return snapshot;
    } catch (_requestError) {
      setReadinessError('Unable to run live readiness checks. Confirm the lead API is reachable.');
      return null;
    } finally {
      setReadinessLoading(false);
    }
  };

  const isPreflightFresh = Boolean(
    readiness?.preflight?.token &&
      readiness?.preflight?.expires_at &&
      new Date(readiness.preflight.expires_at).getTime() > Date.now()
  );

  const canRunMode = (mode: 'profile' | 'dry-run' | 'run') => {
    if (preflightDirty || readinessLoading || !readiness || !isPreflightFresh) {
      return false;
    }

    if (mode === 'profile') {
      return readiness.ready_for_profile;
    }
    if (mode === 'dry-run') {
      return readiness.ready_for_preview;
    }
    return readiness.ready_for_export;
  };

  const getRunBlockMessage = (mode: 'profile' | 'dry-run' | 'run') => {
    if (readinessLoading) {
      return 'Readiness checks are still running.';
    }
    if (preflightDirty) {
      return 'Configuration changed. Run preflight again to unlock execution.';
    }
    if (!readiness) {
      return 'Run preflight to validate the current configuration.';
    }
    if (!isPreflightFresh) {
      return 'Preflight expired. Refresh checks before executing again.';
    }
    if (mode === 'profile' && !readiness.ready_for_profile) {
      return 'Profile is blocked until the readiness panel reports the required dependencies as healthy.';
    }
    if (mode === 'dry-run' && !readiness.ready_for_preview) {
      return 'Preview is blocked until the readiness panel reports the required dependencies as healthy.';
    }
    if (mode === 'run' && !readiness.ready_for_export) {
      return 'Export is blocked until the readiness panel reports a live Google Sheets target and healthy dependencies.';
    }
    return '';
  };

  const runGenerator = async (mode: 'profile' | 'dry-run' | 'run') => {
    setBusyMode(mode);
    setError(null);
    setNotice(null);
    try {
      let readinessSnapshot = readiness;

      if (preflightDirty || !readinessSnapshot || !isPreflightFresh) {
        readinessSnapshot = await checkReadiness();
      }

      if (!readinessSnapshot) {
        setError('Run preflight before executing. The dashboard could not confirm dependency health.');
        return;
      }

      const modeAllowed =
        mode === 'profile'
          ? readinessSnapshot.ready_for_profile
          : mode === 'dry-run'
            ? readinessSnapshot.ready_for_preview
            : readinessSnapshot.ready_for_export;

      if (!modeAllowed || !readinessSnapshot.preflight?.token) {
        setError(getRunBlockMessage(mode) || 'Run preflight before executing.');
        return;
      }

      const endpoint = mode === 'profile' ? 'profile' : mode === 'dry-run' ? 'dry-run' : 'run';
      const response = await axios.post(`${apiBase}/system/${endpoint}`, {
        ...buildPayload(),
        preflight_token: readinessSnapshot.preflight.token,
      });
      const runResult = response.data.data as GeneratorRunResult;
      setExecution(runResult);
      await refreshHistory();
      if (mode === 'dry-run') {
        setNotice('Preview ready. Review the leads, then promote them into the CRM if the list is usable.');
      } else if (mode === 'run') {
        setNotice('Export complete. The audit JSON is saved and the lead set can be promoted into the CRM from this panel or run history.');
      } else {
        setNotice('Market profile complete. Use the preview step to inspect actual leads.');
      }
    } catch (requestError: any) {
      const message =
        requestError?.response?.data?.data?.stderr ||
        requestError?.response?.data?.error ||
        requestError?.response?.data?.data?.stdout ||
        'Generator request failed. Review the runtime log below.';
      setError(message);
    } finally {
      setBusyMode(null);
    }
  };

  const createCampaign = async () => {
    const payload = buildPayload();
    const name = campaignName.trim() || `Campaign ${new Date().toLocaleString()}`;

    try {
      setBusyMode('save-campaign');
      setError(null);
      setNotice(null);
      await axios.post(`${apiBase}/campaigns`, {
        name,
        target_locations: payload.target_locations,
        min_rating: payload.min_rating,
        min_review_count: payload.min_review_count,
        results_per_location: payload.results_per_location,
        google_sheet_id: payload.google_sheet_id || null,
      });
      await refreshCampaigns();
      setCampaignName('');
      setNotice('Campaign saved. You can promote a preview into this CRM pipeline at any time.');
    } catch (requestError) {
      setError('Unable to save campaign. Check that PostgreSQL is running and configured.');
    } finally {
      setBusyMode(null);
    }
  };

  const startCampaign = async (campaignId: string) => {
    try {
      await axios.post(`${apiBase}/campaigns/${campaignId}/start`);
      await refreshCampaigns();
    } catch (requestError) {
      setError('Unable to update the campaign status.');
    }
  };

  const loadArtifact = async (file: string, artifactPath: string) => {
    setError(null);
    setNotice(null);
    try {
      const loadedArtifact = await fetchArtifact(file);
      if (!loadedArtifact) {
        throw new Error('Artifact unavailable');
      }
      setExecution({
        command: [],
        exitCode: 0,
        stdout: 'Loaded from artifact history.',
        stderr: '',
        artifactPath,
        artifact: loadedArtifact,
      });
      setNotice('Artifact loaded. Use the download action for the raw JSON or promote the lead set into the CRM.');
    } catch (_requestError) {
      setError('Unable to load the selected artifact.');
    }
  };

  const promoteArtifactToCampaign = async (artifactFile: string) => {
    setBusyMode(`promote:${artifactFile}`);
    setError(null);
    setNotice(null);

    try {
      const response = await axios.post(`${apiBase}/system/promote`, {
        artifactFile,
        campaignName: campaignName.trim() || undefined,
        google_sheet_id: form.googleSheetId.trim() || undefined,
      });

      const promotedCampaign = response.data.data.campaign as Campaign;
      await refreshHistory();
      const nextCampaigns = await refreshCampaigns();
      const selected = nextCampaigns.find((campaign) => campaign.id === promotedCampaign.id) || promotedCampaign;
      await selectCampaignRecord(selected);
      setCampaignName('');
      setNotice(`Promoted ${response.data.data.insertedLeads} leads into CRM campaign “${selected.name}”.`);
    } catch (requestError: any) {
      const duplicateCampaign = requestError?.response?.data?.data?.campaign as Campaign | undefined;
      if (requestError?.response?.status === 409 && duplicateCampaign) {
        await openPromotedCampaign(duplicateCampaign);
        await refreshHistory();
        setNotice(`This artifact is already in CRM campaign “${duplicateCampaign.name}”.`);
        return;
      }

      const message =
        requestError?.response?.data?.error ||
        'Unable to promote this artifact into the CRM. Confirm PostgreSQL is available and the artifact contains leads.';
      setError(message);
    } finally {
      setBusyMode(null);
    }
  };

  const updateLeadStatus = async (leadId: string, status: Lead['outreach_status']) => {
    try {
      await axios.patch(`${apiBase}/leads/${leadId}`, { outreach_status: status, notes: null });
      if (selectedCampaign) {
        await fetchLeads(selectedCampaign.id);
      }
    } catch (requestError) {
      setError('Unable to update the lead status.');
    }
  };

  const artifact = execution?.artifact;
  const profileRows = useMemo(() => (Array.isArray(artifact?.profiles) ? artifact.profiles : []), [artifact]);
  const leadRows = useMemo(() => {
    if (Array.isArray(artifact?.leads)) {
      return artifact.leads as Lead[];
    }
    if (Array.isArray(artifact?.sample_leads)) {
      return artifact.sample_leads as Lead[];
    }
    return [];
  }, [artifact]);

  const totalQualifiedLeads = history.reduce((sum, item) => sum + (item.total_leads_found || 0), 0);
  const activeCampaigns = campaigns.filter((campaign) => campaign.status === 'running').length;
  const promotedHistoryCount = history.filter((item) => item.is_promoted).length;
  const readyHistoryCount = history.filter((item) => (item.total_leads_found || 0) > 0 && !item.is_promoted).length;
  const currentArtifactFile = execution?.artifactPath ? execution.artifactPath.split('/').slice(-1)[0] : null;
  const currentArtifactHistory = currentArtifactFile
    ? history.find((item) => item.file === currentArtifactFile) || null
    : null;
  const filteredHistory = useMemo(() => {
    const normalizedQuery = historyQuery.trim().toLowerCase();

    const filtered = history.filter((item) => {
      if (historyFilter === 'ready' && !((item.total_leads_found || 0) > 0 && !item.is_promoted)) {
        return false;
      }
      if (historyFilter === 'promoted' && !item.is_promoted) {
        return false;
      }

      if (!normalizedQuery) {
        return true;
      }

      const searchBlob = [
        item.file,
        item.mode,
        item.sheet_name,
        item.promoted_campaign?.name,
        item.generated_at,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      return searchBlob.includes(normalizedQuery);
    });

    const withTimestamp = filtered.map((item) => ({
      item,
      timestamp: item.generated_at ? new Date(item.generated_at).getTime() : 0,
    }));

    withTimestamp.sort((left, right) => {
      const leadDelta = (right.item.total_leads_found || 0) - (left.item.total_leads_found || 0);
      const timeDelta = right.timestamp - left.timestamp;

      if (historySort === 'newest') {
        return timeDelta;
      }

      if (historySort === 'oldest') {
        return -timeDelta;
      }

      if (historySort === 'most-leads') {
        return leadDelta || timeDelta;
      }

      const leftReady = (left.item.total_leads_found || 0) > 0 && !left.item.is_promoted ? 1 : 0;
      const rightReady = (right.item.total_leads_found || 0) > 0 && !right.item.is_promoted ? 1 : 0;
      if (rightReady !== leftReady) {
        return rightReady - leftReady;
      }
      if (leadDelta !== 0) {
        return leadDelta;
      }
      return timeDelta;
    });

    return withTimestamp.map(({ item }) => item);
  }, [history, historyFilter, historyQuery, historySort]);

  const readyVisibleCount = filteredHistory.filter((item) => (item.total_leads_found || 0) > 0 && !item.is_promoted).length;
  const promotedVisibleCount = filteredHistory.filter((item) => item.is_promoted).length;
  const visibleLeadCount = filteredHistory.reduce((sum, item) => sum + (item.total_leads_found || 0), 0);

  const currentHistorySortLabel =
    historySort === 'ready-first'
      ? 'Ready First'
      : historySort === 'most-leads'
        ? 'Most Leads'
        : historySort === 'oldest'
          ? 'Oldest'
          : 'Newest';

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-8">
        <div className="rounded-3xl border border-white/10 bg-white/5 px-8 py-6 text-sm tracking-[0.2em] uppercase">
          Loading operator workspace...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.12),_transparent_30%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.1),_transparent_30%),linear-gradient(180deg,#020617_0%,#0f172a_45%,#111827_100%)] text-slate-100 px-4 py-8 md:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30 backdrop-blur md:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-cyan-200">
                Lead Operations Console
              </div>
              <div>
                <h1
                  className="text-4xl font-semibold tracking-tight text-white md:text-5xl"
                  style={{ fontFamily: 'Georgia, Times New Roman, serif' }}
                >
                  Run the full HVAC lead pipeline without touching code.
                </h1>
                <p className="mt-4 max-w-2xl text-base leading-8 text-slate-300 md:text-lg">
                  This workspace exposes every operational mode of the generator: market profiling,
                  dry-run validation, live Google Sheets export, saved campaign tracking, and lead
                  follow-up management. Configure the search once, then use the action rail to test,
                  preview, and publish safely.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 xl:w-[34rem]">
              <MetricCard label="Saved Runs" value={String(history.length)} note="JSON artifacts ready for audit" />
              <MetricCard label="Leads Captured" value={String(totalQualifiedLeads)} note="Across all recorded artifacts" />
              <MetricCard label="Active Campaigns" value={String(activeCampaigns)} note="CRM pipeline records in Postgres" />
            </div>
          </div>
        </section>

        <section className="grid gap-8 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-8">
            <Panel title="1. Configure the search" subtitle="Non-technical operators can adjust every runtime input here. These values drive profile, dry-run, export, and campaign save operations.">
              <div className="grid gap-6 md:grid-cols-2">
                <LabeledField label="Composio API Key" hint={defaults?.has_composio_api_key ? 'Environment key already exists. Paste only if you need to override it for this run.' : 'Required if the API server does not already have a valid key.'}>
                  <input
                    type="password"
                    value={form.apiKey}
                    onChange={(event) => updateField('apiKey', event.target.value)}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                    placeholder={defaults?.has_composio_api_key ? 'Using server default key' : 'Paste Composio API key'}
                  />
                </LabeledField>
                <LabeledField label="Composio Entity ID" hint="This ties the session to the connected Google Maps and Google Sheets accounts.">
                  <input
                    value={form.entityId}
                    onChange={(event) => updateField('entityId', event.target.value)}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                    placeholder="External user identifier"
                  />
                </LabeledField>
                <div className="md:col-span-2">
                  <LabeledField label="Target Locations" hint="Separate each market with a semicolon. These defaults are already tuned to produce live leads.">
                    <textarea
                      value={form.targetLocations}
                      onChange={(event) => updateField('targetLocations', event.target.value)}
                      rows={4}
                      className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                    />
                  </LabeledField>
                </div>
                <LabeledField label="Minimum Rating">
                  <input
                    type="number"
                    min={0}
                    max={5}
                    step={0.1}
                    value={form.minRating}
                    onChange={(event) => updateField('minRating', Number(event.target.value))}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                  />
                </LabeledField>
                <LabeledField label="Minimum Review Count">
                  <input
                    type="number"
                    min={0}
                    step={1}
                    value={form.minReviewCount}
                    onChange={(event) => updateField('minReviewCount', Number(event.target.value))}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                  />
                </LabeledField>
                <LabeledField label="Results Per Location" hint="The generator caps Google Maps fetches at 20 per location.">
                  <input
                    type="number"
                    min={1}
                    max={20}
                    step={1}
                    value={form.resultsPerLocation}
                    onChange={(event) => updateField('resultsPerLocation', Number(event.target.value))}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                  />
                </LabeledField>
                <LabeledField label="Google Sheet ID" hint="Required for live export. Dry-run and profiling do not write to Sheets.">
                  <input
                    value={form.googleSheetId}
                    onChange={(event) => updateField('googleSheetId', event.target.value)}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                  />
                </LabeledField>
                <div className="md:col-span-2">
                  <LabeledField label="Google Sheet URL (optional)" hint="You can use the sheet ID alone. This field is only here if your operator prefers URLs.">
                    <input
                      value={form.googleSheetUrl}
                      onChange={(event) => updateField('googleSheetUrl', event.target.value)}
                      className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                    />
                  </LabeledField>
                </div>
              </div>
            </Panel>

            <Panel title="2. Choose an action" subtitle="Profile first, preview second, then run the live export. Each action uses the same configuration above, so there are no hidden parameters.">
              <div className="mb-5 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-300">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200">Execution guard</div>
                    <div className="mt-2 leading-7">
                      {preflightDirty
                        ? 'Configuration changed. Run preflight again to unlock execution.'
                        : isPreflightFresh
                          ? 'A fresh readiness preflight is active. Execution is unlocked only for healthy modes.'
                          : 'Run the readiness preflight before executing profile, preview, or export.'}
                    </div>
                  </div>
                  <button
                    onClick={() => void checkReadiness()}
                    disabled={readinessLoading}
                    className="rounded-full border border-cyan-300/30 bg-cyan-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {readinessLoading ? 'Checking...' : 'Run Preflight Now'}
                  </button>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <ActionButton
                  label="Profile Markets"
                  description="Counts total places, no-website candidates, and qualified leads per market without writing data."
                  busy={busyMode === 'profile'}
                  disabled={!canRunMode('profile')}
                  disabledReason={getRunBlockMessage('profile')}
                  onClick={() => runGenerator('profile')}
                />
                <ActionButton
                  label="Preview Leads"
                  description="Runs the full search and filtering logic, then returns the lead set without touching the spreadsheet."
                  busy={busyMode === 'dry-run'}
                  disabled={!canRunMode('dry-run')}
                  disabledReason={getRunBlockMessage('dry-run')}
                  onClick={() => runGenerator('dry-run')}
                />
                <ActionButton
                  label="Generate + Export"
                  description="Runs the full workflow and writes a new Google Sheets tab. A JSON artifact is saved for audit and reuse."
                  busy={busyMode === 'run'}
                  disabled={!canRunMode('run')}
                  disabledReason={getRunBlockMessage('run')}
                  onClick={() => runGenerator('run')}
                  accent="amber"
                />
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-[1fr_auto]">
                <input
                  value={campaignName}
                  onChange={(event) => setCampaignName(event.target.value)}
                  className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                  placeholder="Optional campaign name for CRM tracking"
                />
                <button
                  onClick={createCampaign}
                  disabled={busyMode === 'save-campaign'}
                  className="rounded-2xl border border-white/10 bg-white/10 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busyMode === 'save-campaign' ? 'Saving...' : 'Save Config as Campaign'}
                </button>
              </div>
            </Panel>
          </div>

          <div className="space-y-8">
            <Panel title="Production readiness" subtitle="These live checks use the exact configuration above, so operators can confirm what is safe to run before starting a campaign.">
              <div className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-sm text-slate-300">
                    Last checked: <span className="font-semibold text-white">{formatTime(readiness?.checked_at)}</span>
                  </div>
                  <button
                    onClick={() => void checkReadiness()}
                    disabled={readinessLoading}
                    className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {readinessLoading ? 'Checking...' : 'Refresh checks'}
                  </button>
                </div>

                {readinessError ? (
                  <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-100">
                    {readinessError}
                  </div>
                ) : null}

                <div className="grid gap-3 sm:grid-cols-2">
                  <ReadinessSummaryCard
                    label="Profile"
                    ready={Boolean(readiness?.ready_for_profile)}
                    note="Requires Composio, Python, and artifact storage"
                  />
                  <ReadinessSummaryCard
                    label="Preview"
                    ready={Boolean(readiness?.ready_for_preview)}
                    note="Runs the full search without writing the sheet"
                  />
                  <ReadinessSummaryCard
                    label="Export"
                    ready={Boolean(readiness?.ready_for_export)}
                    note="Requires a valid Google Sheets target"
                  />
                  <ReadinessSummaryCard
                    label="CRM"
                    ready={Boolean(readiness?.ready_for_crm)}
                    note="Requires live Postgres access"
                  />
                </div>

                {!readiness ? (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-black/10 p-5 text-sm text-slate-400">
                    No readiness report yet. Use “Refresh checks” to validate the current configuration.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {readiness.dependencies.map((dependency) => (
                      <ReadinessCard key={dependency.key} dependency={dependency} />
                    ))}
                  </div>
                )}
              </div>
            </Panel>

            <Panel title="Operator runbook" subtitle="Use this sequence to avoid bad exports and make the system understandable to non-technical staff.">
              <ol className="space-y-4 text-sm text-slate-300">
                <li className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-200">Step 1</div>
                  Profile markets to confirm your current thresholds still produce candidates.
                </li>
                <li className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-200">Step 2</div>
                  Run a dry-run to inspect the exact companies before exporting or handing them to sales.
                </li>
                <li className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-200">Step 3</div>
                  Generate and export, then review the audit artifact and saved campaign pipeline below.
                </li>
              </ol>
            </Panel>

            <Panel title="Run result" subtitle="Every run returns the exact command result plus a structured artifact. Nothing is hidden behind a terminal.">
              {error ? (
                <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-100 whitespace-pre-wrap">
                  {error}
                </div>
              ) : null}

              {notice ? (
                <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4 text-sm text-emerald-100 whitespace-pre-wrap">
                  {notice}
                </div>
              ) : null}

              {!execution ? (
                <div className="rounded-2xl border border-dashed border-white/10 bg-black/10 p-6 text-sm text-slate-400">
                  No run selected yet. Use the action buttons to profile, preview, or export with the current settings.
                </div>
              ) : (
                <div className="space-y-5">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <MetricCard label="Exit Code" value={String(execution.exitCode ?? 'n/a')} note={artifact?.mode || 'runtime'} compact />
                    <MetricCard label="Leads Found" value={String(artifact?.total_leads_found ?? profileRows.reduce((sum, row) => sum + (row.qualified || 0), 0))} note={artifact?.sheet_name || execution.artifactPath.split('/').slice(-1)[0]} compact />
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {artifact?.spreadsheet_url ? (
                      <a
                        href={String(artifact.spreadsheet_url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center rounded-full border border-emerald-300/30 bg-emerald-400/10 px-4 py-2 text-sm font-semibold text-emerald-200 transition hover:bg-emerald-400/15"
                      >
                        Open exported spreadsheet
                      </a>
                    ) : null}

                    {execution.artifactPath ? (
                      <a
                        href={`${apiBase}/system/history/${encodeURIComponent(execution.artifactPath.split('/').slice(-1)[0])}/download`}
                        className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/10"
                      >
                        Download audit JSON
                      </a>
                    ) : null}

                    {leadRows.length > 0 ? (
                      <button
                        onClick={() => void promoteArtifactToCampaign(execution.artifactPath.split('/').slice(-1)[0])}
                        disabled={
                          busyMode === `promote:${execution.artifactPath.split('/').slice(-1)[0]}` ||
                          Boolean(currentArtifactHistory?.is_promoted)
                        }
                        className="inline-flex items-center rounded-full border border-cyan-300/30 bg-cyan-400/10 px-4 py-2 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {busyMode === `promote:${execution.artifactPath.split('/').slice(-1)[0]}`
                          ? 'Promoting...'
                          : currentArtifactHistory?.is_promoted
                            ? 'Already in CRM'
                            : 'Promote lead set to CRM'}
                      </button>
                    ) : null}
                  </div>

                  {currentArtifactHistory?.is_promoted && currentArtifactHistory.promoted_campaign ? (
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-cyan-300/20 bg-cyan-400/10 p-4 text-sm text-cyan-100">
                      <span>This artifact already feeds CRM campaign “{currentArtifactHistory.promoted_campaign.name}”.</span>
                      <button
                        onClick={() => void openPromotedCampaign(currentArtifactHistory.promoted_campaign)}
                        className="rounded-full border border-cyan-200/30 bg-cyan-200/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-50 transition hover:bg-cyan-200/15"
                      >
                        Open CRM Campaign
                      </button>
                    </div>
                  ) : null}

                  {profileRows.length > 0 ? (
                    <div className="space-y-3">
                      {profileRows.map((profile) => (
                        <div key={profile.location} className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-300">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div className="font-semibold text-white">{profile.location}</div>
                            <div className="text-xs uppercase tracking-[0.28em] text-slate-400">
                              {profile.qualified} qualified / {profile.without_website} without website / {profile.places_found} total
                            </div>
                          </div>
                          {Array.isArray(profile.sample) && profile.sample.length > 0 ? (
                            <div className="mt-3 space-y-2">
                              {profile.sample.map((sample: any) => (
                                <div key={`${profile.location}-${sample.name}`} className="rounded-xl bg-white/5 px-3 py-2 text-xs text-slate-300">
                                  <span className="font-semibold text-white">{sample.name}</span> - rating {sample.rating} / {sample.review_count} reviews
                                </div>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {leadRows.length > 0 ? (
                    <div className="overflow-hidden rounded-2xl border border-white/10">
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-white/10 text-sm">
                          <thead className="bg-white/5 text-left text-xs uppercase tracking-[0.25em] text-slate-400">
                            <tr>
                              <th className="px-4 py-3">Company</th>
                              <th className="px-4 py-3">Location</th>
                              <th className="px-4 py-3">Rating</th>
                              <th className="px-4 py-3">Reviews</th>
                              <th className="px-4 py-3">Map</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/5 bg-black/10">
                            {leadRows.slice(0, 8).map((lead: any, index: number) => (
                              <tr key={`${lead.name}-${lead.address}-${index}`}>
                                <td className="px-4 py-3">
                                  <div className="font-semibold text-white">{lead.name || lead.company_name}</div>
                                  <div className="text-xs text-slate-400">{lead.address}</div>
                                </td>
                                <td className="px-4 py-3 text-slate-300">{lead.location || 'n/a'}</td>
                                <td className="px-4 py-3 text-slate-300">{lead.rating}</td>
                                <td className="px-4 py-3 text-slate-300">{lead.review_count}</td>
                                <td className="px-4 py-3">
                                  {lead.google_maps_url ? (
                                    <a
                                      href={lead.google_maps_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-cyan-200 underline decoration-cyan-300/40 underline-offset-4"
                                    >
                                      Open
                                    </a>
                                  ) : (
                                    <span className="text-slate-500">n/a</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : null}

                  <details className="rounded-2xl border border-white/10 bg-black/20 p-4 text-xs text-slate-300">
                    <summary className="cursor-pointer font-semibold text-white">Show runtime log</summary>
                    <pre className="mt-3 whitespace-pre-wrap break-words text-slate-300">{execution.stdout || execution.stderr || 'No runtime output.'}</pre>
                  </details>
                </div>
              )}
            </Panel>
          </div>
        </section>

        <section className="grid gap-8 xl:grid-cols-[0.95fr_1.05fr]">
          <Panel title="Run history" subtitle="Every profile, dry-run, and export can be revisited. This removes the need to dig through terminal logs.">
            <div className="space-y-3">
              <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="flex flex-wrap gap-2">
                  <FilterChip
                    label={`All (${history.length})`}
                    active={historyFilter === 'all'}
                    onClick={() => setHistoryFilter('all')}
                  />
                  <FilterChip
                    label={`Ready to Promote (${readyHistoryCount})`}
                    active={historyFilter === 'ready'}
                    onClick={() => setHistoryFilter('ready')}
                  />
                  <FilterChip
                    label={`Already in CRM (${promotedHistoryCount})`}
                    active={historyFilter === 'promoted'}
                    onClick={() => setHistoryFilter('promoted')}
                  />
                </div>

                <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
                  <input
                    value={historyQuery}
                    onChange={(event) => setHistoryQuery(event.target.value)}
                    className="rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                    placeholder="Search by file, mode, sheet name, or CRM campaign"
                  />
                  <div className="flex flex-wrap gap-2">
                    <FilterChip
                      label="Ready First"
                      active={historySort === 'ready-first'}
                      onClick={() => setHistorySort('ready-first')}
                    />
                    <FilterChip
                      label="Most Leads"
                      active={historySort === 'most-leads'}
                      onClick={() => setHistorySort('most-leads')}
                    />
                    <FilterChip
                      label="Newest"
                      active={historySort === 'newest'}
                      onClick={() => setHistorySort('newest')}
                    />
                    <FilterChip
                      label="Oldest"
                      active={historySort === 'oldest'}
                      onClick={() => setHistorySort('oldest')}
                    />
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <MetricCard
                    label="Visible Runs"
                    value={String(filteredHistory.length)}
                    note={`${currentHistorySortLabel} order`}
                    compact
                  />
                  <MetricCard
                    label="Ready in View"
                    value={String(readyVisibleCount)}
                    note={`${promotedVisibleCount} already in CRM`}
                    compact
                  />
                  <MetricCard
                    label="Leads in View"
                    value={String(visibleLeadCount)}
                    note="Total across current filter"
                    compact
                  />
                </div>
              </div>

              {filteredHistory.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-white/10 bg-black/10 p-5 text-sm text-slate-400">
                  {history.length === 0
                    ? 'No artifacts yet. Run a profile, dry-run, or export to create one.'
                    : 'No artifacts match the current filter or search.'}
                </div>
              ) : (
                filteredHistory.map((item) => (
                  <div
                    key={item.file}
                    className="rounded-2xl border border-white/10 bg-black/20 p-4 transition hover:border-cyan-300/30 hover:bg-white/5"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-400">{item.mode}</div>
                        <div className="mt-1 text-sm font-semibold text-white">{formatTime(item.generated_at)}</div>
                      </div>
                      <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
                        {item.total_leads_found ?? 0} leads
                      </div>
                    </div>
                    {item.sheet_name ? <div className="mt-3 text-xs text-emerald-200">Sheet: {item.sheet_name}</div> : null}
                    {item.is_promoted && item.promoted_campaign ? (
                      <div className="mt-2 text-xs text-cyan-200">Already in CRM: {item.promoted_campaign.name}</div>
                    ) : null}
                    <div className="mt-4 flex flex-wrap gap-2">
                      <button
                        onClick={() => void loadArtifact(item.file, item.path)}
                        className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-white transition hover:bg-white/10"
                      >
                        Load
                      </button>
                      <a
                        href={`${apiBase}/system/history/${encodeURIComponent(item.file)}/download`}
                        className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-white transition hover:bg-white/10"
                      >
                        Download JSON
                      </a>
                      {item.is_promoted && item.promoted_campaign ? (
                        <button
                          onClick={() => void openPromotedCampaign(item.promoted_campaign)}
                          className="rounded-full border border-cyan-200/30 bg-cyan-200/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-50 transition hover:bg-cyan-200/15"
                        >
                          Open CRM
                        </button>
                      ) : null}
                      {item.total_leads_found && item.total_leads_found > 0 ? (
                        <button
                          onClick={() => void promoteArtifactToCampaign(item.file)}
                          disabled={busyMode === `promote:${item.file}` || Boolean(item.is_promoted)}
                          className="rounded-full border border-cyan-300/30 bg-cyan-400/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-100 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {busyMode === `promote:${item.file}`
                            ? 'Promoting...'
                            : item.is_promoted
                              ? 'Already in CRM'
                              : 'Promote to CRM'}
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Panel>

          <div className="space-y-8">
            <Panel title="Campaign tracker" subtitle="This is the non-technical CRM layer. Operators can save a search configuration, mark a campaign as running, inspect saved leads, and update outreach statuses.">
              <div className="space-y-3">
                {campaigns.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-black/10 p-5 text-sm text-slate-400">
                    No campaigns saved yet. Use “Save Config as Campaign” to create one from the current search settings.
                  </div>
                ) : (
                  campaigns.map((campaign) => (
                    <div
                      key={campaign.id}
                      className={`rounded-2xl border p-4 transition ${
                        selectedCampaign?.id === campaign.id
                          ? 'border-cyan-300/40 bg-cyan-400/10'
                          : 'border-white/10 bg-black/20 hover:bg-white/5'
                      }`}
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                        <button
                          onClick={() => {
                            void selectCampaignRecord(campaign);
                          }}
                          className="text-left"
                        >
                          <div className="font-semibold text-white">{campaign.name}</div>
                          <div className="mt-1 text-xs text-slate-400">
                            {campaign.target_locations.length} markets · rating {campaign.min_rating}+ · reviews {campaign.min_review_count}+
                          </div>
                        </button>
                        <div className="flex flex-wrap items-center gap-3">
                          <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${statusTone[campaign.status]}`}>
                            {campaign.status}
                          </span>
                          {campaign.status === 'pending' ? (
                            <button
                              onClick={() => void startCampaign(campaign.id)}
                              className="rounded-full border border-white/10 bg-white/10 px-3 py-2 text-xs font-semibold text-white transition hover:bg-white/15"
                            >
                              Mark Running
                            </button>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Panel>

            <Panel title="Saved lead list" subtitle="Selecting a campaign loads stored leads from PostgreSQL so outreach staff can update statuses without leaving the dashboard.">
              {!selectedCampaign ? (
                <div className="rounded-2xl border border-dashed border-white/10 bg-black/10 p-5 text-sm text-slate-400">
                  Select a campaign above to view and update saved leads.
                </div>
              ) : leads.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-white/10 bg-black/10 p-5 text-sm text-slate-400">
                  No saved leads found for {selectedCampaign.name}. This CRM table reads from the local database, which is separate from the Google Sheets export.
                </div>
              ) : (
                <div className="overflow-hidden rounded-2xl border border-white/10">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-white/10 text-sm">
                      <thead className="bg-white/5 text-left text-xs uppercase tracking-[0.25em] text-slate-400">
                        <tr>
                          <th className="px-4 py-3">Company</th>
                          <th className="px-4 py-3">Rating</th>
                          <th className="px-4 py-3">Reviews</th>
                          <th className="px-4 py-3">Outreach</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5 bg-black/10">
                        {leads.map((lead) => (
                          <tr key={lead.id}>
                            <td className="px-4 py-3">
                              <div className="font-semibold text-white">{lead.company_name}</div>
                              <div className="text-xs text-slate-400">{lead.address}</div>
                            </td>
                            <td className="px-4 py-3 text-slate-300">{lead.rating}</td>
                            <td className="px-4 py-3 text-slate-300">{lead.review_count}</td>
                            <td className="px-4 py-3">
                              <select
                                value={lead.outreach_status}
                                onChange={(event) => void updateLeadStatus(lead.id, event.target.value as Lead['outreach_status'])}
                                className="rounded-xl border border-white/10 bg-slate-950/80 px-3 py-2 text-sm text-white outline-none focus:border-cyan-300/40"
                              >
                                <option value="new">New</option>
                                <option value="contacted">Contacted</option>
                                <option value="interested">Interested</option>
                                <option value="not_interested">Not Interested</option>
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </Panel>
          </div>
        </section>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  note,
  compact = false,
}: {
  label: string;
  value: string;
  note: string;
  compact?: boolean;
}) {
  return (
    <div
      className={`rounded-3xl border border-white/10 bg-black/20 ${
        compact ? 'p-4' : 'p-5'
      } shadow-lg shadow-black/20`}
    >
      <div className="text-[0.65rem] font-semibold uppercase tracking-[0.3em] text-slate-400">{label}</div>
      <div className="mt-3 text-3xl font-semibold text-white">{value}</div>
      <div className="mt-2 text-xs leading-6 text-slate-400">{note}</div>
    </div>
  );
}

function Panel({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur md:p-7">
      <div className="mb-6">
        <div className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-200">{title}</div>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">{subtitle}</p>
      </div>
      {children}
    </section>
  );
}

function LabeledField({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-3">
      <span className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-400">{label}</span>
      {children}
      {hint ? <span className="block text-xs leading-6 text-slate-500">{hint}</span> : null}
    </label>
  );
}

function ActionButton({
  label,
  description,
  busy,
  disabled,
  disabledReason,
  onClick,
  accent = 'cyan',
}: {
  label: string;
  description: string;
  busy: boolean;
  disabled?: boolean;
  disabledReason?: string;
  onClick: () => void;
  accent?: 'cyan' | 'amber';
}) {
  const accentClasses =
    accent === 'amber'
      ? 'border-amber-300/30 bg-amber-400/10 text-amber-100 hover:bg-amber-400/15'
      : 'border-cyan-300/30 bg-cyan-400/10 text-cyan-100 hover:bg-cyan-400/15';

  return (
    <button
      onClick={onClick}
      disabled={busy || disabled}
      className={`rounded-3xl border p-5 text-left transition disabled:cursor-not-allowed disabled:opacity-60 ${accentClasses}`}
    >
      <div className="text-sm font-semibold uppercase tracking-[0.2em]">{busy ? 'Running...' : label}</div>
      <div className="mt-3 text-sm leading-7 text-slate-200">{description}</div>
      {disabled && !busy && disabledReason ? (
        <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-xs leading-6 text-slate-300">
          {disabledReason}
        </div>
      ) : null}
    </button>
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
        active
          ? 'border-cyan-300/30 bg-cyan-400/10 text-cyan-100'
          : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
      }`}
    >
      {label}
    </button>
  );
}

function ReadinessSummaryCard({
  label,
  ready,
  note,
}: {
  label: string;
  ready: boolean;
  note: string;
}) {
  return (
    <div className={`rounded-2xl border p-4 ${ready ? 'border-emerald-300/20 bg-emerald-400/10' : 'border-amber-300/20 bg-amber-400/10'}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-200">{label}</span>
        <span
          className={`rounded-full border px-2.5 py-1 text-[0.65rem] font-semibold uppercase tracking-[0.22em] ${
            ready
              ? 'border-emerald-200/30 bg-emerald-200/10 text-emerald-50'
              : 'border-amber-200/30 bg-amber-200/10 text-amber-50'
          }`}
        >
          {ready ? 'Ready' : 'Blocked'}
        </span>
      </div>
      <div className="mt-3 text-xs leading-6 text-slate-300">{note}</div>
    </div>
  );
}

function ReadinessCard({
  dependency,
}: {
  dependency: ReadinessCheck;
}) {
  const tone =
    dependency.status === 'healthy'
      ? 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100'
      : dependency.status === 'warning'
        ? 'border-amber-300/20 bg-amber-400/10 text-amber-100'
        : 'border-rose-300/20 bg-rose-400/10 text-rose-100';

  return (
    <div className={`rounded-2xl border p-4 ${tone}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm font-semibold text-white">{dependency.label}</div>
        <span className="rounded-full border border-white/10 bg-black/20 px-2.5 py-1 text-[0.65rem] font-semibold uppercase tracking-[0.22em]">
          {dependency.status}
        </span>
      </div>
      <div className="mt-3 text-sm leading-7">{dependency.detail}</div>
      {dependency.meta?.sheet_id ? (
        <div className="mt-2 text-xs text-slate-200">Sheet ID: {String(dependency.meta.sheet_id)}</div>
      ) : null}
      {dependency.meta?.path ? (
        <div className="mt-2 text-xs text-slate-200">Path: {String(dependency.meta.path)}</div>
      ) : null}
    </div>
  );
}

async function fetchArtifact(file: string): Promise<Record<string, any> | null> {
  if (!file) {
    return null;
  }

  try {
    const response = await fetch(`${apiBase}/system/history/${encodeURIComponent(file)}`);
    const payload = await response.json();
    if (!payload.success) {
      return null;
    }
    return (payload.data?.artifact || null) as Record<string, any> | null;
  } catch (_error) {
    return null;
  }
}
