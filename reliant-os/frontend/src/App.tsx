import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Settings, MessageSquare, Code, Zap, Key, Shield, Clock, History, Bot, User, DollarSign } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type AIMode = 'auto' | 'chat' | 'code' | 'sales';

interface Message {
  role: 'user' | 'system';
  content: string;
  execution?: string[];
  executionTime?: number;
  mode?: AIMode;
}

export default function App() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/os/status')
      .then(res => res.json())
      .then(data => {
        setStatus(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <LoadingScreen />;
  if (status && !status.configured) return <SetupScreen onComplete={() => window.location.reload()} />;
  return <Desktop />;
}

function LoadingScreen() {
  return (
    <div style={{
      display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center',
      background: '#000', color: '#fff', flexDirection: 'column', gap: '20px'
    }}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      >
        <Zap size={48} color="#00d4ff" />
      </motion.div>
      <div style={{ fontSize: '1.2rem', letterSpacing: '2px' }}>BOOTING RELIANT OS...</div>
      <div style={{ color: '#666', fontSize: '0.9rem' }}>Initializing secure vault • Loading AI cores • Mounting filesystems</div>
    </div>
  );
}

function SetupScreen({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    gemini_key: '', stripe_key: '', twilio_sid: '', twilio_token: '', places_key: ''
  });
  const [saving, setSaving] = useState(false);

  const steps = [
    { title: 'AI Core', key: 'gemini_key', icon: <Bot size={24} />, desc: 'Google Gemini API Key for autonomous operations' },
    { title: 'Payments', key: 'stripe_key', icon: <DollarSign size={24} />, desc: 'Stripe Secret Key for billing and subscriptions' },
    { title: 'Communications', key: 'twilio_sid', icon: <MessageSquare size={24} />, desc: 'Twilio Account SID for SMS outreach' },
    { title: 'Communications', key: 'twilio_token', icon: <Shield size={24} />, desc: 'Twilio Auth Token for secure messaging' },
    { title: 'Lead Generation', key: 'places_key', icon: <Zap size={24} />, desc: 'Google Places API Key for finding prospects' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await fetch('/api/os/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      onComplete();
    } catch (err) {
      alert('Failed to save configuration');
      setSaving(false);
    }
  };

  const inputStyle = {
    width: '100%', padding: '14px', background: '#111', border: '1px solid #333',
    color: 'white', borderRadius: '8px', marginBottom: '8px', fontSize: '1rem'
  };

  return (
    <div style={{
      display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #000 0%, #0a0a1a 100%)'
    }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: 'rgba(10,10,10,0.95)', padding: '40px', borderRadius: '20px',
          border: '1px solid #222', width: '500px', backdropFilter: 'blur(10px)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <Key color="#00ff88" size={32} />
          <h2 style={{ margin: 0, fontSize: '1.5rem' }}>Reliant OS Initialization</h2>
        </div>
        <p style={{ color: '#888', marginBottom: '24px', lineHeight: '1.5' }}>
          Welcome to your autonomous platform. Securely configure your API keys to activate the system.
          No files are written to disk - all secrets are encrypted in the vault.
        </p>

        <form onSubmit={handleSubmit}>
          <AnimatePresence mode="wait">
            {steps.map((s, i) => (
              i === step && (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                    <span style={{ color: '#00d4ff' }}>{s.icon}</span>
                    <span style={{ fontWeight: 'bold' }}>{s.title}</span>
                    <span style={{ color: '#666', marginLeft: 'auto' }}>{i + 1}/{steps.length}</span>
                  </div>
                  <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '12px' }}>{s.desc}</p>
                  <input
                    required
                    type="password"
                    style={inputStyle}
                    placeholder={`Enter ${s.title} API Key`}
                    value={formData[s.key as keyof typeof formData]}
                    onChange={e => setFormData({ ...formData, [s.key]: e.target.value })}
                  />
                </motion.div>
              )
            ))}
          </AnimatePresence>

          <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
            {step > 0 && (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                style={{
                  flex: 1, padding: '14px', background: '#1a1a1a', border: '1px solid #333',
                  borderRadius: '8px', color: 'white', cursor: 'pointer'
                }}
              >
                Back
              </button>
            )}
            {step < steps.length - 1 ? (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                style={{
                  flex: 1, padding: '14px', background: 'linear-gradient(90deg, #00d4ff, #7b2cbf)',
                  border: 'none', borderRadius: '8px', color: 'white', fontWeight: 'bold', cursor: 'pointer'
                }}
              >
                Continue
              </button>
            ) : (
              <button
                type="submit"
                disabled={saving}
                style={{
                  flex: 1, padding: '14px', background: 'linear-gradient(90deg, #00d4ff, #7b2cbf)',
                  border: 'none', borderRadius: '8px', color: 'white', fontWeight: 'bold', cursor: 'pointer'
                }}
              >
                {saving ? 'Encrypting & Booting...' : 'Initialize Platform'}
              </button>
            )}
          </div>
        </form>
      </motion.div>
    </div>
  );
}

function Desktop() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'system',
      content: 'Welcome to Reliant JIT OS v2.0. I am your autonomous operations core.\n\nI can:\n• Modify source code and deploy changes\n• Answer questions about the system\n• Generate leads and pitch prospects\n• Monitor and heal the platform\n• Write production-grade code\n\nSelect a mode below or just start typing. How can I assist you today?'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<AIMode>('auto');
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const msg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg, mode }]);
    setLoading(true);

    try {
      const res = await fetch('/api/os/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, history: messages, mode })
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: 'system',
        content: data.reply,
        execution: data.execution_results,
        executionTime: data.execution_time_ms,
        mode: data.mode
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: 'Connection to Core AI failed. Please check system status.' }]);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await fetch('/api/os/execution-history');
      const data = await res.json();
      setHistory(data.history);
      setShowHistory(true);
    } catch (err) {
      console.error('Failed to load history');
    }
  };

  const modes: { id: AIMode; label: string; icon: any; color: string }[] = [
    { id: 'auto', label: 'Auto', icon: Zap, color: '#00d4ff' },
    { id: 'chat', label: 'Support', icon: MessageSquare, color: '#00ff88' },
    { id: 'code', label: 'Engineer', icon: Code, color: '#ff6b35' },
    { id: 'sales', label: 'Sales', icon: DollarSign, color: '#ffd700' },
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#000' }}>
      {/* Sidebar */}
      <div style={{
        width: '280px', background: '#0a0a0a', borderRight: '1px solid #1a1a1a',
        padding: '24px', display: 'flex', flexDirection: 'column', gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #00d4ff, #7b2cbf)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Zap color="white" size={24} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.1rem' }}>Reliant OS</h2>
            <div style={{ color: '#00ff88', fontSize: '0.75rem' }}>● System Online</div>
          </div>
        </div>

        {modes.map(m => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px',
              borderRadius: '10px', border: 'none', background: mode === m.id ? 'rgba(0,212,255,0.1)' : 'transparent',
              color: mode === m.id ? m.color : '#888', cursor: 'pointer', width: '100%',
              transition: 'all 0.2s', borderLeft: mode === m.id ? `3px solid ${m.color}` : '3px solid transparent'
            }}
          >
            <m.icon size={18} />
            <span style={{ fontWeight: mode === m.id ? 'bold' : 'normal' }}>{m.label}</span>
            {mode === m.id && <motion.div layoutId="active" style={{ marginLeft: 'auto', width: '8px', height: '8px', borderRadius: '50%', background: m.color }} />}
          </button>
        ))}

        <div style={{ marginTop: 'auto', borderTop: '1px solid #1a1a1a', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button onClick={loadHistory} style={{
            display: 'flex', alignItems: 'center', gap: '10px', padding: '10px',
            borderRadius: '8px', border: 'none', background: 'transparent', color: '#888', cursor: 'pointer'
          }}>
            <History size={16} /> Execution History
          </button>
          <button style={{
            display: 'flex', alignItems: 'center', gap: '10px', padding: '10px',
            borderRadius: '8px', border: 'none', background: 'transparent', color: '#888', cursor: 'pointer'
          }}>
            <Settings size={16} /> Vault Settings
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#000' }}>
        {/* Header */}
        <div style={{
          padding: '16px 24px', borderBottom: '1px solid #1a1a1a',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: modes.find(m => m.id === mode)?.color, fontWeight: 'bold' }}>
              {modes.find(m => m.id === mode)?.label} Mode
            </span>
            <span style={{ color: '#666', fontSize: '0.85rem' }}>
              {mode === 'auto' && 'Automatically detects code vs chat'}
              {mode === 'chat' && 'Support and questions'}
              {mode === 'code' && 'Production code generation'}
              {mode === 'sales' && 'Lead generation and pitching'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#666', fontSize: '0.85rem' }}>
            <Shield size={14} color="#00ff88" />
            Secure Execution
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                marginBottom: '20px', display: 'flex', flexDirection: 'column',
                alignItems: m.role === 'user' ? 'flex-end' : 'flex-start'
              }}
            >
              <div style={{
                background: m.role === 'user' ? '#1a1a2e' : '#0f0f1a',
                border: `1px solid ${m.role === 'user' ? '#2a2a4a' : '#1a1a2e'}`,
                padding: '16px', borderRadius: '12px', maxWidth: '85%', lineHeight: '1.6',
                boxShadow: m.role === 'system' ? '0 4px 20px rgba(0,212,255,0.05)' : 'none'
              }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px',
                  color: m.role === 'user' ? '#00d4ff' : '#00ff88', fontSize: '0.8rem', fontWeight: 'bold'
                }}>
                  {m.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                  {m.role === 'user' ? 'You' : 'Reliant AI'}
                  {m.executionTime && <span style={{ color: '#666' }}>• {m.executionTime}ms</span>}
                </div>
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'inherit', color: '#e0e0e0' }}>{m.content}</pre>
              </div>
              
              {m.execution && m.execution.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  style={{
                    marginTop: '8px', background: '#050508', border: '1px solid #1a1a2e',
                    padding: '12px', borderRadius: '8px', maxWidth: '85%', width: '100%'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#00ff88', fontSize: '0.8rem' }}>
                    <Terminal size={14} /> Execution Output
                  </div>
                  {m.execution.map((exec, idx) => (
                    <pre key={idx} style={{
                      margin: '4px 0', padding: '8px', background: '#0a0a0f',
                      borderRadius: '4px', color: exec.startsWith('[BLOCKED]') ? '#ff4444' : exec.startsWith('[ERROR]') ? '#ff8844' : '#00ff88',
                      fontFamily: 'monospace', fontSize: '0.8rem', overflowX: 'auto'
                    }}>{exec}</pre>
                  ))}
                </motion.div>
              )}
            </motion.div>
          ))}
          
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#666', padding: '16px' }}>
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                <Zap size={16} color="#00d4ff" />
              </motion.div>
              Core AI is processing...
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input Area */}
        <div style={{ padding: '20px 24px', borderTop: '1px solid #1a1a1a', background: '#050508' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={`Ask a question, request code, or command the system...`}
                style={{
                  width: '100%', background: '#0f0f1a', border: '1px solid #2a2a4a',
                  color: 'white', padding: '14px', borderRadius: '12px', fontSize: '1rem',
                  resize: 'none', minHeight: '60px', maxHeight: '200px', fontFamily: 'inherit'
                }}
                rows={1}
              />
              <div style={{ position: 'absolute', bottom: '8px', right: '12px', color: '#666', fontSize: '0.75rem' }}>
                Shift+Enter for new line
              </div>
            </div>
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              style={{
                padding: '14px 24px', background: input.trim() ? 'linear-gradient(135deg, #00d4ff, #7b2cbf)' : '#1a1a2e',
                border: 'none', borderRadius: '12px', color: 'white', fontWeight: 'bold',
                cursor: input.trim() ? 'pointer' : 'not-allowed', transition: 'all 0.2s'
              }}
            >
              <Zap size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* History Panel */}
      <AnimatePresence>
        {showHistory && (
          <motion.div
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            style={{
              width: '350px', background: '#0a0a0a', borderLeft: '1px solid #1a1a1a',
              padding: '24px', overflowY: 'auto'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <History size={18} /> Execution History
              </h3>
              <button onClick={() => setShowHistory(false)} style={{ background: 'none', border: 'none', color: '#666', cursor: 'pointer' }}>✕</button>
            </div>
            
            {history.length === 0 && <div style={{ color: '#666' }}>No executions yet</div>}
            
            {history.map((h, i) => (
              <div key={i} style={{
                padding: '12px', borderRadius: '8px', background: '#0f0f1a',
                border: '1px solid #1a1a2e', marginBottom: '8px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: h.status === 'success' ? '#00ff88' : h.status === 'blocked' ? '#ff4444' : '#ff8844'
                  }} />
                  <span style={{ fontSize: '0.8rem', color: '#888' }}>{h.timestamp}</span>
                </div>
                <div style={{ fontSize: '0.85rem', marginBottom: '4px' }}>{h.prompt.substring(0, 60)}...</div>
                <div style={{ fontSize: '0.75rem', color: '#666' }}>
                  Hash: {h.code_hash} • {h.execution_time_ms}ms
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
