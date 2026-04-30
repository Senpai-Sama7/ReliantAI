/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  LayoutGrid, 
  Compass, 
  Zap, 
  BarChart3, 
  Settings, 
  Bell,
  Search,
  Plus,
  Play
} from 'lucide-react';
import { ViewType } from './types';
import { cn } from './lib/utils';
import CommandView from './components/CommandView';
import DiscoveryView from './components/DiscoveryView';
import CampaignsView from './components/CampaignsView';
import MetricsView from './components/MetricsView';
import SettingsView from './components/SettingsView';

export default function App() {
  const [currentView, setCurrentView] = useState<ViewType>('command');

  const renderView = () => {
    switch (currentView) {
      case 'command': return <CommandView />;
      case 'discovery': return <DiscoveryView />;
      case 'campaigns': return <CampaignsView />;
      case 'metrics': return <MetricsView />;
      case 'settings': return <SettingsView />;
      default: return <CommandView />;
    }
  };

  const navItems = [
    { id: 'command', label: 'Command', icon: LayoutGrid },
    { id: 'discovery', label: 'Discovery', icon: Compass },
    { id: 'campaigns', label: 'Campaigns', icon: Zap },
    { id: 'metrics', label: 'Metrics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-transparent text-on-background selection:bg-white/20 selection:text-white relative">
      <div className="atmosphere" />
      {/* Top App Bar */}
      <nav className="fixed top-0 w-full z-50 bg-black/20 backdrop-blur-md border-b border-white/5 flex justify-between items-center px-10 h-20 shadow-none">
        <div className="flex items-center gap-12">
          <span className="font-serif italic text-2xl tracking-tight text-white">ReliantAI.</span>
          
          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8 font-medium text-[11px] uppercase tracking-[0.2em] text-white/50 h-full">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id as ViewType)}
                className={cn(
                  "hover:text-white transition-colors h-full relative px-2 flex items-center gap-2",
                  currentView === item.id ? "text-white" : ""
                )}
              >
                {item.label}
                {currentView === item.id && (
                  <motion.span 
                    layoutId="activeTab"
                    className="absolute bottom-[28px] left-0 right-0 h-[1px] bg-white/40"
                  />
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-6">
          <button className="relative p-2 text-white/50 hover:text-white transition-colors active:scale-95 duration-150">
            <Bell size={20} className="stroke-[1.5]" />
            <span className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-orange-500 rounded-full shadow-[0_0_8px_rgba(249,115,22,0.4)] animate-pulse" />
          </button>
          <div className="w-10 h-10 rounded-full overflow-hidden border border-white/10 bg-[url('https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=100&q=80')] bg-cover" />
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 pt-28 pb-32 px-10 max-w-7xl mx-auto w-full">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            {renderView()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Bottom Navigation (Mobile Only) */}
      <nav className="md:hidden fixed bottom-0 w-full z-50 bg-black/40 backdrop-blur-xl border-t border-white/5 flex justify-around items-center h-20 px-4 pb-safe shadow-2xl">
        {navItems.slice(0, 4).map((item) => (
          <button
            key={item.id}
            onClick={() => setCurrentView(item.id as ViewType)}
            className={cn(
              "flex flex-col items-center justify-center transition-all active:scale-90 duration-200 w-16 h-full gap-1.5",
              currentView === item.id ? "text-white" : "text-white/40"
            )}
          >
            <item.icon size={20} className="stroke-[1.5]" />
            <span className="font-medium text-[8px] uppercase tracking-[0.2em]">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
