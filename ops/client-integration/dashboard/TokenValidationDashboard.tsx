import React, { useMemo, useState } from "react";
import {
  Activity,
  CheckCircle,
  RefreshCw,
  Server,
  Shield,
  XCircle,
} from "lucide-react";

export interface ServiceStatus {
  name: string;
  category: string;
  isValid: boolean | null;
  message: string;
  latency: number | null;
}

export interface CredentialAuditResponse {
  services: ServiceStatus[];
  auditedAt: string;
}

type AuditFetcher = () => Promise<CredentialAuditResponse>;

const INITIAL_SERVICES: ServiceStatus[] = [
  {
    name: "HubSpot CRM Access API",
    category: "Data Pipeline",
    isValid: null,
    message: "Awaiting initialization...",
    latency: null,
  },
  {
    name: "Scheduling Sync (Cal.com)",
    category: "Customer Portal",
    isValid: null,
    message: "Awaiting initialization...",
    latency: null,
  },
  {
    name: "Emergency Slack Dispatch Route",
    category: "Communications",
    isValid: null,
    message: "Awaiting initialization...",
    latency: null,
  },
];

async function defaultAuditFetcher(): Promise<CredentialAuditResponse> {
  const response = await fetch("/api/credential-audit", { method: "POST" });
  if (!response.ok) {
    throw new Error(`Audit endpoint returned ${response.status}`);
  }
  return (await response.json()) as CredentialAuditResponse;
}

function overallLabel(services: ServiceStatus[]): {
  label: string;
  tone: string;
} {
  const known = services.filter((s) => s.isValid !== null);
  if (known.length === 0) return { label: "Idle", tone: "text-stone-600" };
  const failed = known.filter((s) => s.isValid === false).length;
  if (failed === 0) return { label: "Fully Connected", tone: "text-emerald-700" };
  if (failed === known.length) return { label: "Disconnected", tone: "text-rose-700" };
  return { label: "Partial Connection", tone: "text-amber-700" };
}

export interface TokenValidationDashboardProps {
  /** Optional injector for tests / local CLI bridge. Defaults to POST /api/credential-audit */
  auditFetcher?: AuditFetcher;
}

/**
 * Internal ops panel for live credential pipeline diagnostics.
 * Expects a backend route at POST /api/credential-audit that runs runCredentialAudit().
 */
export default function TokenValidationDashboard({
  auditFetcher = defaultAuditFetcher,
}: TokenValidationDashboardProps) {
  const [isAuditing, setIsAuditing] = useState(false);
  const [lastAuditTime, setLastAuditTime] = useState("Never");
  const [error, setError] = useState<string | null>(null);
  const [services, setServices] = useState<ServiceStatus[]>(INITIAL_SERVICES);

  const summary = useMemo(() => overallLabel(services), [services]);
  const verifiedCount = services.filter((s) => s.isValid === true).length;

  const triggerSystemAudit = async () => {
    setIsAuditing(true);
    setError(null);
    try {
      const result = await auditFetcher();
      setServices(result.services);
      setLastAuditTime(
        result.auditedAt
          ? new Date(result.auditedAt).toLocaleTimeString()
          : new Date().toLocaleTimeString(),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsAuditing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_#f4f7f5_0%,_#e8eee9_45%,_#dfe6e1_100%)] text-stone-900 p-8 font-[family-name:var(--font-ops,ui-sans-serif)]">
      <div className="mx-auto max-w-5xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-stone-300/80 pb-6 mb-8 gap-4">
          <div>
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-teal-800" />
              <h1 className="text-2xl font-semibold tracking-tight text-stone-900">
                Reliant AI Credential Matrix
              </h1>
            </div>
            <p className="text-sm text-stone-600 mt-1">
              Real-time endpoint diagnostics for HubSpot, Cal.com, and Slack routing.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-xs text-stone-500 uppercase tracking-wider">
                Last System Scan
              </p>
              <p className="text-sm font-mono font-medium text-stone-800">
                {lastAuditTime}
              </p>
            </div>
            <button
              type="button"
              onClick={triggerSystemAudit}
              disabled={isAuditing}
              className="flex items-center gap-2 bg-teal-800 hover:bg-teal-700 disabled:bg-stone-300 disabled:text-stone-500 text-white px-5 py-2.5 rounded-md text-sm font-medium transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isAuditing ? "animate-spin" : ""}`} />
              {isAuditing ? "Executing Live Audit..." : "Run Diagnostics"}
            </button>
          </div>
        </div>

        {error ? (
          <div className="mb-6 border border-rose-300 bg-rose-50 text-rose-800 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        ) : null}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="border border-stone-300 bg-white/70 backdrop-blur-sm rounded-lg p-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-stone-500 font-medium uppercase tracking-wider">
                System Integration Status
              </p>
              <h3 className={`text-xl font-semibold mt-1 ${summary.tone}`}>
                {summary.label}
              </h3>
            </div>
            <Activity className="w-8 h-8 text-amber-700 bg-amber-100 p-1.5 rounded-md" />
          </div>
          <div className="border border-stone-300 bg-white/70 backdrop-blur-sm rounded-lg p-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-stone-500 font-medium uppercase tracking-wider">
                Active Secure Pipelines
              </p>
              <h3 className="text-xl font-semibold mt-1 font-mono text-stone-900">
                {verifiedCount} / {services.length} Verified
              </h3>
            </div>
            <Server className="w-8 h-8 text-teal-800 bg-teal-50 p-1.5 rounded-md" />
          </div>
          <div className="border border-stone-300 bg-white/70 backdrop-blur-sm rounded-lg p-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-stone-500 font-medium uppercase tracking-wider">
                Audit Mode
              </p>
              <h3 className="text-xl font-semibold mt-1 text-stone-800">Live Endpoints</h3>
            </div>
            <CheckCircle className="w-8 h-8 text-emerald-700 bg-emerald-50 p-1.5 rounded-md" />
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-wider mb-2">
            Endpoint Performance Tracks
          </h2>
          {services.map((service) => (
            <div
              key={service.name}
              className="border border-stone-300 bg-white/80 rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="flex items-start gap-4">
                <div className="mt-1">
                  {service.isValid === null && (
                    <div className="w-5 h-5 rounded-full border-2 border-dashed border-stone-400" />
                  )}
                  {service.isValid === true && (
                    <CheckCircle className="w-5 h-5 text-emerald-600" />
                  )}
                  {service.isValid === false && (
                    <XCircle className="w-5 h-5 text-rose-600" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-base font-semibold text-stone-900">
                      {service.name}
                    </h4>
                    <span className="text-xs font-medium px-2 py-0.5 rounded bg-stone-100 text-stone-600 border border-stone-200">
                      {service.category}
                    </span>
                  </div>
                  <p className="text-sm text-stone-600 mt-1 font-mono">
                    {service.message}
                  </p>
                </div>
              </div>

              <div className="text-left sm:text-right flex sm:flex-col items-center sm:items-end justify-between sm:justify-center border-t sm:border-t-0 border-stone-200 pt-3 sm:pt-0 gap-2">
                <span className="text-xs text-stone-500 uppercase tracking-wider">
                  Latency
                </span>
                <span className="text-sm font-mono font-medium text-stone-800">
                  {service.latency != null ? `${service.latency} ms` : "--"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
