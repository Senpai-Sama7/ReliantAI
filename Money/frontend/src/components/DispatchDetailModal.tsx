// Dispatch detail modal — full view with timeline and manual override
import { useState, useEffect } from 'react';
import {
  X, User, Phone, MapPin, Clock, Wrench, AlertTriangle,
  CheckCircle, ChevronRight, Edit2, Save,
} from 'lucide-react';
import api, { type Dispatch } from '../services/api';

interface TimelineEvent {
  event_id: number;
  event_type: string;
  from_state: string | null;
  to_state: string | null;
  actor: string;
  created_at: string;
}

interface Props {
  dispatch: Dispatch;
  onClose: () => void;
  onUpdated: (updated: Dispatch) => void;
  onError: (msg: string) => void;
}

const STATE_LABELS: Record<string, string> = {
  received: 'Received',
  triaged: 'Triaged',
  qualified: 'Qualified',
  scheduled: 'Scheduled',
  confirmed: 'Confirmed',
  dispatched: 'Dispatched',
  arrived: 'Arrived',
  in_progress: 'In Progress',
  completed: 'Completed',
  followed_up: 'Followed Up',
  cancelled: 'Cancelled',
  escalated: 'Escalated',
};

const ALLOWED_STATUS_OVERRIDES = ['pending', 'in_progress', 'complete', 'cancelled', 'escalated'];

function formatDate(iso: string) {
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

function ResultSection({ result }: { result: Record<string, unknown> }) {
  const fields = Object.entries(result).filter(([k]) =>
    !['event_bus_event_id', 'event_bus_channel'].includes(k),
  );

  return (
    <div className="space-y-2">
      {fields.map(([key, val]) => (
        <div key={key} className="flex gap-2 text-sm">
          <span className="text-genh-gray min-w-[120px] capitalize">{key.replace(/_/g, ' ')}:</span>
          <span className="text-genh-white/90 break-words">
            {typeof val === 'object' ? JSON.stringify(val, null, 2) : String(val ?? '—')}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function DispatchDetailModal({ dispatch, onClose, onUpdated, onError }: Props) {
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loadingTimeline, setLoadingTimeline] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [overrideStatus, setOverrideStatus] = useState(dispatch.status);
  const [overrideTech, setOverrideTech] = useState(dispatch.tech_name || '');
  const [overrideEta, setOverrideEta] = useState(dispatch.eta || '');

  useEffect(() => {
    let alive = true;
    api.getDispatchTimeline(dispatch.dispatch_id)
      .then(data => { if (alive) setTimeline(data.events as TimelineEvent[]); })
      .catch(() => { /* timeline is optional */ })
      .finally(() => { if (alive) setLoadingTimeline(false); });
    return () => { alive = false; };
  }, [dispatch.dispatch_id]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await api.updateDispatchStatus(dispatch.dispatch_id, {
        status: overrideStatus !== dispatch.status ? overrideStatus : undefined,
        tech_name: overrideTech !== dispatch.tech_name ? overrideTech : undefined,
        eta: overrideEta !== dispatch.eta ? overrideEta : undefined,
      });
      onUpdated(updated);
      setEditing(false);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  const isEmergency = dispatch.urgency?.toLowerCase() === 'emergency';
  const result = dispatch.crew_result as Record<string, unknown> | undefined;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-label="Dispatch details"
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-genh-black border border-genh-white/10 shadow-2xl">
        {/* Header */}
        <div className={`sticky top-0 z-10 px-6 py-4 border-b flex items-center justify-between ${
          isEmergency ? 'border-red-500/50 bg-red-950/30' : 'border-genh-white/10 bg-genh-black'
        }`}>
          <div className="flex items-center gap-3">
            {isEmergency && <AlertTriangle className="w-5 h-5 text-red-400 animate-pulse" />}
            <h2 className="font-display text-lg text-genh-white uppercase tracking-tight">
              Dispatch Details
            </h2>
            <span className="text-genh-gray text-xs font-mono">{dispatch.dispatch_id.slice(0, 8)}…</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-genh-gray hover:text-genh-white transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Customer Info */}
          <section>
            <h3 className="text-label mb-3 opacity-60">Customer</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {dispatch.customer_name && (
                <div className="flex items-center gap-2 text-sm">
                  <User className="w-4 h-4 text-genh-gold" />
                  <span className="text-genh-white">{dispatch.customer_name}</span>
                </div>
              )}
              {dispatch.customer_phone && (
                <div className="flex items-center gap-2 text-sm">
                  <Phone className="w-4 h-4 text-genh-gold" />
                  <a
                    href={`tel:${dispatch.customer_phone}`}
                    className="text-genh-white hover:text-genh-gold transition-colors"
                  >
                    {dispatch.customer_phone}
                  </a>
                </div>
              )}
              {dispatch.address && (
                <div className="flex items-start gap-2 text-sm sm:col-span-2">
                  <MapPin className="w-4 h-4 text-genh-gold shrink-0 mt-0.5" />
                  <span className="text-genh-white">{dispatch.address}</span>
                </div>
              )}
            </div>
          </section>

          {/* Issue */}
          <section>
            <h3 className="text-label mb-2 opacity-60">Issue Reported</h3>
            <p className="text-genh-white/90 text-sm leading-relaxed bg-genh-charcoal/30 p-3 border border-genh-white/5">
              {dispatch.issue_summary || 'No description provided'}
            </p>
          </section>

          {/* Status / Assignment (editable) */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-label opacity-60">Assignment & Status</h3>
              {!editing ? (
                <button
                  onClick={() => setEditing(true)}
                  className="flex items-center gap-1.5 text-xs text-genh-gold hover:text-genh-gold/80 transition-colors"
                >
                  <Edit2 className="w-3 h-3" /> Edit
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setEditing(false)}
                    className="text-xs text-genh-gray hover:text-genh-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1.5 text-xs bg-genh-gold text-genh-black px-2 py-1 hover:bg-genh-gold/90 transition-colors disabled:opacity-50"
                  >
                    <Save className="w-3 h-3" />
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                </div>
              )}
            </div>

            {editing ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-genh-gray mb-1 block">Status</label>
                  <select
                    value={overrideStatus}
                    onChange={e => setOverrideStatus(e.target.value)}
                    className="w-full bg-genh-charcoal border border-genh-white/20 text-genh-white text-sm px-2 py-1.5 focus:outline-none focus:border-genh-gold"
                  >
                    {ALLOWED_STATUS_OVERRIDES.map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-genh-gray mb-1 block">Technician</label>
                  <input
                    type="text"
                    value={overrideTech}
                    onChange={e => setOverrideTech(e.target.value)}
                    placeholder="Tech name"
                    className="w-full bg-genh-charcoal border border-genh-white/20 text-genh-white text-sm px-2 py-1.5 focus:outline-none focus:border-genh-gold placeholder:text-genh-gray/50"
                  />
                </div>
                <div>
                  <label className="text-xs text-genh-gray mb-1 block">ETA</label>
                  <input
                    type="text"
                    value={overrideEta}
                    onChange={e => setOverrideEta(e.target.value)}
                    placeholder="e.g. 2:30 PM"
                    className="w-full bg-genh-charcoal border border-genh-white/20 text-genh-white text-sm px-2 py-1.5 focus:outline-none focus:border-genh-gold placeholder:text-genh-gray/50"
                  />
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-genh-gold" />
                  <span className="text-genh-gray">Status:</span>
                  <span className="text-genh-white capitalize">{dispatch.status}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-genh-gold" />
                  <span className="text-genh-gray">Tech:</span>
                  <span className="text-genh-white">{dispatch.tech_name || 'Unassigned'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-genh-gold" />
                  <span className="text-genh-gray">ETA:</span>
                  <span className="text-genh-white">{dispatch.eta || 'TBD'}</span>
                </div>
              </div>
            )}
          </section>

          {/* AI Result */}
          {result && Object.keys(result).length > 0 && (
            <section>
              <h3 className="text-label mb-3 opacity-60">AI Dispatch Result</h3>
              <div className="bg-genh-charcoal/30 p-3 border border-genh-white/5 text-xs font-mono">
                <ResultSection result={result} />
              </div>
            </section>
          )}

          {/* Timeline */}
          <section>
            <h3 className="text-label mb-3 opacity-60">State Timeline</h3>
            {loadingTimeline ? (
              <p className="text-genh-gray text-sm">Loading timeline…</p>
            ) : timeline.length === 0 ? (
              <p className="text-genh-gray text-sm">No state transitions recorded yet.</p>
            ) : (
              <ol className="space-y-2">
                {timeline.map((ev, i) => (
                  <li key={i} className="flex items-start gap-3 text-xs">
                    <div className="flex flex-col items-center shrink-0">
                      <div className="w-2 h-2 rounded-full bg-genh-gold mt-1" />
                      {i < timeline.length - 1 && <div className="w-px h-4 bg-genh-white/10 my-0.5" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 text-genh-white/80">
                        {ev.from_state && (
                          <>
                            <span className="text-genh-gray">{STATE_LABELS[ev.from_state] ?? ev.from_state}</span>
                            <ChevronRight className="w-3 h-3 text-genh-gray/50" />
                          </>
                        )}
                        <span className="font-medium">{STATE_LABELS[ev.to_state ?? ''] ?? ev.to_state ?? ev.event_type}</span>
                      </div>
                      <div className="text-genh-gray/60 mt-0.5">
                        {ev.actor} · {formatDate(ev.created_at)}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>

          {/* Timestamps */}
          <section className="flex gap-4 text-xs text-genh-gray border-t border-genh-white/5 pt-4">
            <span>Created: {formatDate(dispatch.created_at)}</span>
            {dispatch.updated_at && (
              <span>Updated: {formatDate(dispatch.updated_at)}</span>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
