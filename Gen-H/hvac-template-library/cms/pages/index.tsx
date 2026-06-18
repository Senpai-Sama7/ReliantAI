import { useEffect, useState } from 'react';
import Link from 'next/link';
import DeploymentsList from '../components/DeploymentsList';
import { fetchTemplates } from '../lib/api';
import type { Template } from '../lib/types';

export default function Dashboard() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTemplates()
      .then(setTemplates)
      .catch((err) => console.error('Failed to fetch templates:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <div className="mb-8 sm:mb-12">
          <h1 className="text-2xl font-bold sm:text-4xl">HVAC Template Library</h1>
          <p className="mt-1 text-sm text-slate-300 sm:text-base">Manage templates and deployments</p>
        </div>

        <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:gap-4">
          <Link href="/templates/create">
            <button className="w-full rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold hover:bg-blue-700 sm:w-auto">
              + New Template
            </button>
          </Link>
          <Link href="/companies/create">
            <button className="w-full rounded-lg bg-green-600 px-6 py-2 text-sm font-semibold hover:bg-green-700 sm:w-auto">
              + New Company
            </button>
          </Link>
          <Link href="/deployments/create">
            <button className="w-full rounded-lg bg-purple-600 px-6 py-2 text-sm font-semibold hover:bg-purple-700 sm:w-auto">
              + New Deployment
            </button>
          </Link>
        </div>

        <div className="mb-10 sm:mb-12">
          <h2 className="mb-4 text-xl font-bold sm:mb-6 sm:text-2xl">
            Templates {!loading && `(${templates.length})`}
          </h2>
          {loading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-40 animate-pulse rounded-lg bg-slate-700/60" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {templates.map((template) => (
                <Link key={template.id} href={`/templates/${template.id}`}>
                  <div className="cursor-pointer rounded-lg bg-slate-700 p-4 transition hover:bg-slate-600">
                    {template.preview_image_url && (
                      <img
                        src={template.preview_image_url}
                        alt={template.name}
                        className="mb-2 h-32 w-full rounded object-cover"
                      />
                    )}
                    <h3 className="font-semibold">{template.name}</h3>
                    <p className="text-sm capitalize text-slate-400">{template.framework}</p>
                    <span
                      className={`mt-2 inline-block rounded px-2 py-1 text-xs font-semibold ${
                        template.status === 'active' ? 'bg-green-600' : 'bg-yellow-600'
                      }`}
                    >
                      {template.status}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        <DeploymentsList limit={10} showViewAll title="Recent Deployments" />
      </div>
    </div>
  );
}
