import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Shield, Key, ArrowRight } from 'lucide-react';
import { ENV } from '../../config/env';

export default function AdminLogin() {
  const [username, setUsername] = useState(ENV.ADMIN_USER);
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, error, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setIsSubmitting(true);
    await login(username.trim(), password);
    setIsSubmitting(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-genh-black flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-genh-gold border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-genh-black flex items-center justify-center px-4">
      {/* Background gradient */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(215, 160, 77, 0.05) 0%, transparent 60%)'
        }}
      />

      <div className="relative w-full max-w-md">
        {/* Logo / Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 border border-genh-gold/30 mb-6">
            <Shield className="w-8 h-8 text-genh-gold" />
          </div>
          <h1 className="font-display text-2xl md:text-3xl text-genh-white uppercase tracking-tight">
            Admin Portal
          </h1>
          <p className="font-body text-sm text-genh-gray mt-2">
            Sign in with your admin username and password
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="text-label mb-2 block">
              Username
            </label>
            <div className="relative">
              <Key className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-genh-gray/50" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your admin username"
                className="w-full bg-genh-charcoal border border-genh-white/10 pl-12 pr-4 py-4 text-genh-white placeholder:text-genh-gray/40 font-body focus:outline-none focus:border-genh-gold transition-colors"
                disabled={isSubmitting}
                autoComplete="username"
              />
            </div>
          </div>

          <div>
            <label className="text-label mb-2 block">
              Password
            </label>
            <div className="relative">
              <Key className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-genh-gray/50" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your admin password"
                className="w-full bg-genh-charcoal border border-genh-white/10 pl-12 pr-4 py-4 text-genh-white placeholder:text-genh-gray/40 font-body focus:outline-none focus:border-genh-gold transition-colors"
                disabled={isSubmitting}
                autoComplete="current-password"
              />
            </div>
            {error && (
              <p className="text-red-400 text-sm mt-2 font-body">
                {error}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !username.trim() || !password.trim()}
            className="group w-full flex items-center justify-center gap-2 px-8 py-4 bg-genh-gold text-genh-black font-body font-semibold text-sm uppercase tracking-wider transition-all duration-300 hover:bg-genh-cream disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%)' }}
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-genh-black border-t-transparent rounded-full animate-spin" />
                Authenticating...
              </>
            ) : (
              <>
                Access Dashboard
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </>
            )}
          </button>
        </form>

        {/* Help text */}
        <p className="text-center text-genh-gray/50 text-xs mt-8 font-body">
          Authentication uses the backend session cookie only. <br />
          Contact your administrator if you need access.
        </p>

        {/* Back to site link */}
        <div className="text-center mt-6">
          <a 
            href="/"
            className="text-genh-gold text-sm font-body hover:underline"
          >
            ← Back to website
          </a>
        </div>
      </div>
    </div>
  );
}
