// UXPolish.jsx — toast system + keyboard shortcut overlay + scroll-to-top

// ── Toast system ─────────────────────────────────────────────────
const ToastContext = React.createContext(null);

const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = React.useState([]);

  const addToast = React.useCallback(({ message, tone='neutral', duration=3200, icon }) => {
    const id = Math.random().toString(36).slice(2,10);
    setToasts(t => [...t, { id, message, tone, icon }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), duration);
    return id;
  }, []);

  const dismiss = React.useCallback((id) => setToasts(t => t.filter(x => x.id !== id)), []);

  const tones = {
    neutral: { bg:'#091424', bd:'#152637', c:'#a8c4de' },
    success: { bg:'rgba(0,255,122,0.08)', bd:'rgba(0,255,122,0.3)', c:'#00ff7a' },
    error:   { bg:'rgba(255,59,92,0.08)', bd:'rgba(255,59,92,0.3)', c:'#ff3b5c' },
    warn:    { bg:'rgba(255,196,0,0.08)', bd:'rgba(255,196,0,0.3)', c:'#ffc400' },
    info:    { bg:'rgba(0,229,255,0.06)', bd:'rgba(0,229,255,0.25)', c:'#00e5ff' },
  };

  return <ToastContext.Provider value={addToast}>
    {children}
    <div style={{position:'fixed', bottom:24, right:24, zIndex:500, display:'flex', flexDirection:'column', gap:8, pointerEvents:'none'}}>
      {toasts.map(t => {
        const s = tones[t.tone] || tones.neutral;
        return <div key={t.id} style={{
          display:'flex', alignItems:'center', gap:10,
          padding:'10px 14px', background:s.bg, border:`1px solid ${s.bd}`,
          borderRadius:2, minWidth:260, maxWidth:380,
          fontFamily:'IBM Plex Sans,sans-serif', fontSize:12, color:s.c,
          animation:'slide-up 220ms ease-out',
          boxShadow:'0 8px 24px rgba(0,0,0,0.4)',
          pointerEvents:'all',
        }}>
          {t.icon && <i data-lucide={t.icon} style={{width:14, height:14, flexShrink:0}}/>}
          <span style={{flex:1}}>{t.message}</span>
          <i data-lucide="x" style={{width:12, height:12, cursor:'pointer', opacity:0.5}} onClick={()=>dismiss(t.id)}/>
        </div>;
      })}
    </div>
  </ToastContext.Provider>;
};

const useToast = () => React.useContext(ToastContext);

// ── Keyboard shortcut overlay ────────────────────────────────────
const ShortcutOverlay = ({ onClose }) => {
  React.useEffect(() => {
    const h = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  const groups = [
    { label:'Navigation', shortcuts:[
      ['⌘K', 'Open command palette'],
      ['⌘B', 'Toggle sidebar'],
      ['Shift+?', 'Show this overlay'],
      ['Esc', 'Close modal / overlay'],
    ]},
    { label:'ClearDesk', shortcuts:[
      ['↑↓ + Enter', 'Select document row'],
      ['⌘U', 'Upload documents'],
      ['⌘E', 'Export filtered view'],
      ['⌘/', 'Open AI chat'],
    ]},
    { label:'APEX HITL', shortcuts:[
      ['A', 'Approve focused decision'],
      ['R', 'Reject focused decision'],
      ['Tab', 'Next decision in queue'],
      ['⌘Enter', 'Submit with reasoning'],
    ]},
    { label:'Global', shortcuts:[
      ['⌘.', 'Toggle event feed'],
      ['G then C', 'Go to ClearDesk'],
      ['G then M', 'Go to Money'],
      ['G then A', 'Go to APEX'],
    ]},
  ];

  return <div onClick={onClose} style={{position:'fixed', inset:0, background:'rgba(2,5,16,0.8)', zIndex:400, backdropFilter:'blur(6px)', display:'flex', alignItems:'center', justifyContent:'center'}}>
    <div onClick={e=>e.stopPropagation()} style={{background:'#060c1a', border:'1px solid #152637', width:600, maxHeight:'80vh', overflow:'auto', borderRadius:2, boxShadow:'0 20px 60px rgba(0,0,0,0.6)'}}>
      <div style={{padding:'18px 24px', borderBottom:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <div style={{fontSize:14, fontWeight:600, color:'#ffffff'}}>Keyboard shortcuts</div>
        <div style={{display:'flex', gap:8, alignItems:'center'}}>
          <Kbd>Shift+?</Kbd>
          <Kbd>Esc</Kbd>
          <i data-lucide="x" onClick={onClose} style={{width:15, height:15, color:'#4a6880', cursor:'pointer', marginLeft:4}}/>
        </div>
      </div>
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:0}}>
        {groups.map((g, gi) => (
          <div key={g.label} style={{padding:'20px 24px', borderRight:gi%2===0?'1px solid #0c1a2c':'none', borderBottom:gi<2?'1px solid #0c1a2c':'none'}}>
            <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.12em', marginBottom:12, fontFamily:'IBM Plex Mono,monospace'}}>{g.label}</div>
            <div style={{display:'flex', flexDirection:'column', gap:8}}>
              {g.shortcuts.map(([k,l])=>(
                <div key={k} style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                  <span style={{fontSize:12, color:'#a8c4de'}}>{l}</span>
                  <Kbd>{k}</Kbd>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div style={{padding:'12px 24px', borderTop:'1px solid #0c1a2c', fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
        Press Shift+? anytime to toggle this overlay
      </div>
    </div>
  </div>;
};

// ── Scroll-to-top wrapper ────────────────────────────────────────
const ScrollTop = ({ trigger, children }) => {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (ref.current) ref.current.scrollTop = 0;
  }, [trigger]);
  return <div ref={ref} style={{flex:1, overflowY:'auto', background:'#020510'}}>{children}</div>;
};

Object.assign(window, { ToastProvider, useToast, ShortcutOverlay, ScrollTop });
