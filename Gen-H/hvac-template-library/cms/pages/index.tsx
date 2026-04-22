import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';

interface Template {
  id: string;
  name: string;
  slug: string;
  framework: string;
  status: string;
  preview_image_url?: string;
}

interface Deployment {
  id: string;
  domain: string;
  status: 'pending' | 'deploying' | 'live' | 'failed';
  company_id: string;
  template_id: string;
  created_at: string;
}

export default function Dashboard() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [templatesRes, deploymentsRes] = await Promise.all([
        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/templates`),
        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/deployments`),
      ]);

      setTemplates(templatesRes.data.data || []);
      setDeployments(deploymentsRes.data.data || []);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-2">HVAC Template Library</h1>
          <p className="text-slate-300">Manage templates and deployments</p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-8">
          <Link href="/templates/create">
            <button className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold">
              + New Template
            </button>
          </Link>
          <Link href="/companies/create">
            <button className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold">
              + New Company
            </button>
          </Link>
          <Link href="/deployments/create">
            <button className="px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold">
              + New Deployment
            </button>
          </Link>
        </div>

        {/* Templates Grid */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6">Templates ({templates.length})</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {templates.map((template) => (
              <Link key={template.id} href={`/templates/${template.id}`}>
                <div className="bg-slate-700 rounded-lg p-4 cursor-pointer hover:bg-slate-600 transition">
                  {template.preview_image_url && (
                    <img
                      src={template.preview_image_url}
                      alt={template.name}
                      className="w-full h-32 object-cover rounded mb-2"
                    />
                  )}
                  <h3 className="font-semibold">{template.name}</h3>
                  <p className="text-sm text-slate-400 capitalize">{template.framework}</p>
                  <span className={`inline-block mt-2 px-2 py-1 rounded text-xs font-semibold 
                    ${template.status === 'active' ? 'bg-green-600' : 'bg-yellow-600'}`}>
                    {template.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Deployments */}
        <div>
          <h2 className="text-2xl font-bold mb-6">Recent Deployments</h2>
          <div className="bg-slate-700 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left">Domain</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {deployments.slice(0, 10).map((deployment) => (
                  <tr key={deployment.id} className="border-t border-slate-600 hover:bg-slate-600">
                    <td className="px-4 py-3 font-mono text-sm">{deployment.domain}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold
                        ${deployment.status === 'live' ? 'bg-green-600' : 
                          deployment.status === 'deploying' ? 'bg-blue-600' : 
                          deployment.status === 'failed' ? 'bg-red-600' : 'bg-yellow-600'}`}>
                        {deployment.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {new Date(deployment.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/deployments/${deployment.id}`}>
                        <button className="text-blue-400 hover:text-blue-300 text-sm">View</button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
