import Link from 'next/link';
import type { ReactNode } from 'react';

interface DashboardLayoutProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
}

export default function DashboardLayout({ title, subtitle, children, actions }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <Link href="/" className="mb-3 inline-block text-xs text-slate-500 hover:text-slate-300">
              ← Dashboard
            </Link>
            <h1 className="text-2xl font-bold sm:text-4xl">{title}</h1>
            {subtitle && <p className="mt-1 text-sm text-slate-300 sm:text-base">{subtitle}</p>}
          </div>
          {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
        </div>
        {children}
      </div>
    </div>
  );
}
