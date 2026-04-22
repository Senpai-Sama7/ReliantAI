import { LayoutDashboard, FileText, Upload, HelpCircle, Settings, Search, Menu, X, Info } from 'lucide-react';
import { useState } from 'react';
import { classNames } from '../../utils/formatters';
import { useDocuments } from '../../contexts/DocumentContext';

interface LayoutProps {
  children: React.ReactNode;
  onNavigate?: (view: string) => void;
  activeView?: string;
}

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'about', label: 'About', icon: Info },
  { id: 'help', label: 'Help', icon: HelpCircle },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function Layout({ children, onNavigate, activeView = 'dashboard' }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { setFilters } = useDocuments();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (val: string) => {
    setSearchQuery(val);
    setFilters({ searchQuery: val });
  };

  return (
    <div className="min-h-screen bg-bg flex">
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={classNames(
        'fixed lg:static inset-y-0 left-0 z-50 w-60 bg-bg border-r border-border flex flex-col transition-transform duration-200',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
        <div className="flex items-center justify-between px-5 h-14 border-b border-border">
          <span className="font-heading text-lg font-bold text-text-primary tracking-tight">ClearDesk</span>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-text-secondary hover:text-text-primary" aria-label="Close sidebar">
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => { onNavigate?.(item.id); setSidebarOpen(false); }}
                className={classNames(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer',
                  active ? 'bg-surface text-text-primary' : 'text-text-secondary hover:text-text-primary hover:bg-surface/50'
                )}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 bg-bg border-b border-border sticky top-0 z-30 flex items-center justify-between px-4 lg:px-8">
          <div className="flex items-center gap-4">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-text-secondary hover:text-text-primary" aria-label="Open sidebar">
              <Menu className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>

          <div className="flex items-center bg-surface border border-border rounded-lg px-3 py-1.5 w-64 lg:w-80">
            <Search className="w-4 h-4 text-text-secondary mr-2 flex-shrink-0" aria-hidden="true" />
            <input
              type="text"
              aria-label="Search documents"
              placeholder="Search documents…"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="bg-transparent border-none outline-none text-sm text-text-primary placeholder:text-text-secondary w-full"
            />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 lg:p-10">
          {children}
        </main>
      </div>
    </div>
  );
}
