import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import DashboardLayout from '../../components/DashboardLayout';
import { createDeployment, fetchCompanies, fetchTemplates } from '../../lib/api';
import type { Company, Template } from '../../lib/types';

export default function CreateDeploymentPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    template_id: '',
    company_id: '',
    domain: '',
    primary_color: '',
  });

  useEffect(() => {
    Promise.all([fetchTemplates(), fetchCompanies()])
      .then(([templateData, companyData]) => {
        setTemplates(templateData);
        setCompanies(companyData);
        if (templateData[0]) setForm((f) => ({ ...f, template_id: templateData[0].id }));
        if (companyData[0]) setForm((f) => ({ ...f, company_id: companyData[0].id }));
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load form data'))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const deployment = await createDeployment({
        template_id: form.template_id,
        company_id: form.company_id,
        domain: form.domain.trim(),
        customizations: form.primary_color ? { primary_color: form.primary_color } : undefined,
      });
      router.push(`/deployments/${deployment.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create deployment');
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout title="New Deployment" subtitle="Configure and queue a new site deployment">
      {loading ? (
        <div className="h-64 animate-pulse rounded-lg bg-slate-700/60" />
      ) : (
        <form onSubmit={handleSubmit} className="mx-auto max-w-xl space-y-5">
          <Field label="Template">
            <select
              required
              value={form.template_id}
              onChange={(e) => setForm((f) => ({ ...f, template_id: e.target.value }))}
              className={inputClass}
            >
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.framework})
                </option>
              ))}
            </select>
          </Field>

          <Field label="Company">
            <select
              required
              value={form.company_id}
              onChange={(e) => setForm((f) => ({ ...f, company_id: e.target.value }))}
              className={inputClass}
            >
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Domain">
            <input
              required
              type="text"
              placeholder="example-hvac.com"
              value={form.domain}
              onChange={(e) => setForm((f) => ({ ...f, domain: e.target.value }))}
              className={inputClass}
            />
          </Field>

          <Field label="Primary color (optional)">
            <div className="flex gap-2">
              <input
                type="color"
                value={form.primary_color || '#1e3a8a'}
                onChange={(e) => setForm((f) => ({ ...f, primary_color: e.target.value }))}
                className="h-10 w-14 cursor-pointer rounded border border-slate-600 bg-slate-800"
              />
              <input
                type="text"
                placeholder="#1e3a8a"
                value={form.primary_color}
                onChange={(e) => setForm((f) => ({ ...f, primary_color: e.target.value }))}
                className={`${inputClass} flex-1`}
              />
            </div>
          </Field>

          {error && (
            <div className="rounded-lg border border-red-800 bg-red-950/40 p-3 text-sm text-red-300">{error}</div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-purple-600 py-2.5 text-sm font-semibold hover:bg-purple-700 disabled:opacity-60 sm:w-auto sm:px-8"
          >
            {submitting ? 'Creating…' : 'Create Deployment'}
          </button>
        </form>
      )}
    </DashboardLayout>
  );
}

const inputClass =
  'w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500';

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-slate-300">{label}</span>
      {children}
    </label>
  );
}
