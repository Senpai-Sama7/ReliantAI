// UI.jsx — shared ReliantAI primitives (dark Revenue Engine v6)
// All screens in the console import these. Kept deliberately compact.

const cx = (...a) => a.filter(Boolean).join(' ');

// ── Count-up number ──────────────────────────────────────────────
const CountUp = ({ to, duration=800, prefix='', suffix='', decimals=0, className, style }) => {
  const [v, setV] = React.useState(0);
  React.useEffect(() => {
    // Immediate fallback so value shows even if rAF is throttled
    const fallback = setTimeout(() => setV(to), duration + 100);
    let raf, start;
    const step = (t) => {
      if (!start) start = t;
      const p = Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setV(to * eased);
      if (p < 1) raf = requestAnimationFrame(step);
      else clearTimeout(fallback);
    };
    raf = requestAnimationFrame(step);
    return () => { cancelAnimationFrame(raf); clearTimeout(fallback); };
  }, [to, duration]);
  return <span className={className} style={style}>{prefix}{v.toLocaleString(undefined,{maximumFractionDigits:decimals,minimumFractionDigits:decimals})}{suffix}</span>;
};

// ── Badge ────────────────────────────────────────────────────────
const Badge = ({ label, tone='neutral', pulse=false, size='sm' }) => {
  const tones = {
    neutral: { c:'#a8c4de', bg:'rgba(168,196,222,0.06)', bd:'#152637' },
    cyan:    { c:'#00e5ff', bg:'rgba(0,229,255,0.08)',   bd:'rgba(0,229,255,0.3)' },
    green:   { c:'#00ff7a', bg:'rgba(0,255,122,0.08)',   bd:'rgba(0,255,122,0.25)' },
    gold:    { c:'#ffc400', bg:'rgba(255,196,0,0.08)',   bd:'rgba(255,196,0,0.3)' },
    red:     { c:'#ff3b5c', bg:'rgba(255,59,92,0.1)',    bd:'rgba(255,59,92,0.35)' },
    purple:  { c:'#7c5cfc', bg:'rgba(124,92,252,0.1)',   bd:'rgba(124,92,252,0.3)' },
    teal:    { c:'#00d4aa', bg:'rgba(0,212,170,0.08)',   bd:'rgba(0,212,170,0.25)' },
    orange:  { c:'#ff8c00', bg:'rgba(255,140,0,0.08)',   bd:'rgba(255,140,0,0.3)' },
    life:    { c:'#ff3b5c', bg:'rgba(255,59,92,0.18)',   bd:'#ff3b5c' },
  };
  const t = tones[tone] || tones.neutral;
  const sizes = { xs:{fs:9,pad:'1px 5px'}, sm:{fs:10,pad:'2px 7px'}, md:{fs:11,pad:'3px 10px'} };
  const s = sizes[size];
  return <span style={{
    display:'inline-block', fontFamily:'IBM Plex Sans,sans-serif', fontSize:s.fs, fontWeight:600,
    padding:s.pad, borderRadius:2, background:t.bg, color:t.c, border:`1px solid ${t.bd}`,
    letterSpacing:'0.04em', whiteSpace:'nowrap',
    animation: pulse ? 'pulse 1.6s ease infinite' : undefined,
  }}>{label}</span>;
};

// ── Button ───────────────────────────────────────────────────────
const Btn = ({ children, variant='secondary', size='md', tone, onClick, disabled, icon, style={} }) => {
  const variants = {
    primary:   { bg:'#00e5ff', c:'#020510', bd:'#00e5ff', hover:'#22eeff' },
    secondary: { bg:'#091424', c:'#a8c4de', bd:'#152637', hover:'#0d1e35' },
    ghost:     { bg:'transparent', c:'#a8c4de', bd:'transparent', hover:'rgba(255,255,255,0.04)' },
    danger:    { bg:'rgba(255,59,92,0.08)', c:'#ff3b5c', bd:'rgba(255,59,92,0.3)', hover:'rgba(255,59,92,0.12)' },
    success:   { bg:'rgba(0,255,122,0.08)', c:'#00ff7a', bd:'rgba(0,255,122,0.3)', hover:'rgba(0,255,122,0.12)' },
  };
  // service-tinted primary
  if (tone) {
    const toneMap = { cleardesk:'#00FF94', money:'#ffc400', apex:'#7c5cfc', bap:'#00e5ff' };
    const color = toneMap[tone] || '#00e5ff';
    variants.primary = { bg:color, c:'#020510', bd:color, hover:color };
  }
  const v = variants[variant] || variants.secondary;
  const sizes = { xs:{fs:10,pad:'3px 8px'}, sm:{fs:11,pad:'5px 11px'}, md:{fs:12,pad:'7px 14px'}, lg:{fs:13,pad:'10px 20px'} };
  const s = sizes[size];
  const [h, setH] = React.useState(false);
  return <button disabled={disabled} onClick={onClick}
    onMouseEnter={()=>setH(true)} onMouseLeave={()=>setH(false)}
    style={{
      display:'inline-flex', alignItems:'center', gap:6, fontWeight:600, letterSpacing:'0.01em',
      fontSize:s.fs, padding:s.pad, borderRadius:2, cursor: disabled?'not-allowed':'pointer',
      background: disabled ? '#091424' : (h ? v.hover : v.bg),
      color: disabled ? '#4a6880' : v.c,
      border: `1px solid ${disabled?'#152637':v.bd}`,
      opacity: disabled ? 0.5 : 1,
      transition:'all 150ms', fontFamily:'IBM Plex Sans,sans-serif',
      ...style,
    }}>
    {icon && <i data-lucide={icon} style={{width:s.fs+2, height:s.fs+2}}/>}
    {children}
  </button>;
};

// ── Panel + Section header ───────────────────────────────────────
const Panel = ({ children, style={}, elevated=false }) => (
  <div style={{
    background: elevated ? '#091424' : '#060c1a',
    border: '1px solid #0c1a2c',
    borderRadius: 2,
    ...style,
  }}>{children}</div>
);

const PanelHeader = ({ title, sub, right }) => (
  <div style={{padding:'12px 16px', borderBottom:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'center', gap:12}}>
    <div>
      <div style={{fontSize:12, fontWeight:600, color:'#ffffff', letterSpacing:'0.01em'}}>{title}</div>
      {sub && <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', marginTop:2}}>{sub}</div>}
    </div>
    {right}
  </div>
);

// ── Metric tile ──────────────────────────────────────────────────
const MetricTile = ({ label, value, unit='', delta, color='#ffffff', icon }) => (
  <div style={{padding:'14px 16px', borderRight:'1px solid #0c1a2c', flex:1, minWidth:120}}>
    <div style={{display:'flex', alignItems:'center', gap:6, marginBottom:6}}>
      {icon && <i data-lucide={icon} style={{width:11, height:11, color:'#4a6880'}}/>}
      <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em'}}>{label}</div>
    </div>
    <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:22, fontWeight:600, color, lineHeight:1}}>
      {typeof value === 'number' ? <CountUp to={value}/> : value}
      {unit && <span style={{fontSize:11, color:'#4a6880', marginLeft:4}}>{unit}</span>}
    </div>
    {delta != null && (
      <div style={{fontSize:10, color: delta>0?'#00ff7a':delta<0?'#ff3b5c':'#4a6880', marginTop:4, fontFamily:'IBM Plex Mono,monospace'}}>
        {delta>0?'↑':delta<0?'↓':'—'} {Math.abs(delta)}%
      </div>
    )}
  </div>
);

// ── Confidence bar ───────────────────────────────────────────────
const ConfBar = ({ val, width=60, showLabel=true }) => {
  const color = val >= 0.9 ? '#00ff7a' : val >= 0.7 ? '#ffc400' : '#ff3b5c';
  const [w, setW] = React.useState(0);
  React.useEffect(() => { const t = setTimeout(()=>setW(val*100), 50); return ()=>clearTimeout(t); }, [val]);
  return <div style={{display:'flex', alignItems:'center', gap:8}}>
    <div style={{width, height:4, background:'#0c1a2c', borderRadius:1, overflow:'hidden'}}>
      <div style={{width:`${w}%`, height:'100%', background:color, transition:'width 600ms cubic-bezier(.4,0,.2,1)'}}/>
    </div>
    {showLabel && <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color}}>{val.toFixed(2)}</span>}
  </div>;
};

// ── Sparkline ────────────────────────────────────────────────────
const Sparkline = ({ data, width=80, height=24, color='#00e5ff', fill=true }) => {
  const max = Math.max(...data), min = Math.min(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const points = data.map((v, i) => `${i*step},${height - ((v-min)/range) * (height-2) - 1}`);
  const path = 'M ' + points.join(' L ');
  const area = path + ` L ${width},${height} L 0,${height} Z`;
  return <svg width={width} height={height} style={{display:'block'}}>
    {fill && <path d={area} fill={color} opacity="0.12"/>}
    <path d={path} fill="none" stroke={color} strokeWidth="1.2"/>
  </svg>;
};

// ── Kbd ──────────────────────────────────────────────────────────
const Kbd = ({ children }) => <span style={{
  fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880',
  background:'#060c1a', border:'1px solid #0c1a2c', borderRadius:2, padding:'1px 5px',
}}>{children}</span>;

// ── Empty state ──────────────────────────────────────────────────
const EmptyState = ({ icon='inbox', title, body, cta }) => (
  <div style={{display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'56px 24px', gap:12}}>
    <div style={{width:40, height:40, border:'1px solid #152637', borderRadius:2, display:'flex', alignItems:'center', justifyContent:'center'}}>
      <i data-lucide={icon} style={{width:18, height:18, color:'#4a6880'}}/>
    </div>
    <div style={{fontSize:14, fontWeight:500, color:'#ffffff'}}>{title}</div>
    {body && <div style={{fontSize:12, color:'#4a6880', maxWidth:320, textAlign:'center', lineHeight:1.6}}>{body}</div>}
    {cta}
  </div>
);

// ── Skeleton ─────────────────────────────────────────────────────
const Skel = ({ w='100%', h=12, style={} }) => (
  <div className="skel" style={{width:w, height:h, borderRadius:1, ...style}}/>
);

// ── Tabs ─────────────────────────────────────────────────────────
const Tabs = ({ tabs, active, onChange, tone='#00e5ff' }) => (
  <div style={{display:'flex', gap:0, borderBottom:'1px solid #0c1a2c'}}>
    {tabs.map(t => (
      <div key={t.id||t} onClick={()=>onChange(t.id||t)} style={{
        padding:'9px 16px', fontSize:12, cursor:'pointer',
        color: active===(t.id||t) ? '#ffffff' : '#4a6880',
        borderBottom: active===(t.id||t) ? `2px solid ${tone}` : '2px solid transparent',
        marginBottom:-1, transition:'all 150ms', textTransform:'capitalize',
        fontWeight: active===(t.id||t) ? 500 : 400,
      }}>{t.label||t}{t.count!=null && <span style={{marginLeft:6,fontSize:10,color:'#4a6880',fontFamily:'IBM Plex Mono,monospace'}}>{t.count}</span>}</div>
    ))}
  </div>
);

// ── Input ────────────────────────────────────────────────────────
const Input = ({ icon, type='text', error, size='md', style={}, ...rest }) => {
  const sizes = { sm:{fs:11,pad:'5px 10px',h:26}, md:{fs:12,pad:'7px 12px',h:30} };
  const s = sizes[size];
  return <div style={{position:'relative', ...style}}>
    {icon && <i data-lucide={icon} style={{position:'absolute', left:10, top:'50%', transform:'translateY(-50%)', width:13, height:13, color:'#4a6880'}}/>}
    <input type={type} {...rest} style={{
      background:'#091424', border:`1px solid ${error?'#ff3b5c':'#152637'}`, color:'#ffffff',
      fontSize:s.fs, padding: icon ? `${s.pad.split(' ')[0]} ${s.pad.split(' ')[1]} ${s.pad.split(' ')[0]} 30px` : s.pad,
      borderRadius:2, outline:'none', width:'100%',
      fontFamily:'IBM Plex Sans,sans-serif', transition:'all 150ms',
    }}/>
    {error && <div style={{fontSize:10, color:'#ff3b5c', marginTop:3, fontFamily:'IBM Plex Sans,sans-serif'}}>{error}</div>}
  </div>;
};

// ── Divider ──────────────────────────────────────────────────────
const Divider = ({ label, style={} }) => (
  <div style={{display:'flex', alignItems:'center', gap:10, margin:'12px 0', ...style}}>
    <div style={{flex:1, height:1, background:'#0c1a2c'}}/>
    {label && <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', fontFamily:'IBM Plex Mono,monospace'}}>{label}</div>}
    <div style={{flex:1, height:1, background:'#0c1a2c'}}/>
  </div>
);

// ── Logo ─────────────────────────────────────────────────────────
// Custom monogram: concentric chevrons suggesting "layered reliability"
const ToastContext = React.createContext(null);

const useToast = () => {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be inside ToastProvider');
  return ctx;
};

const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = React.useState([]);
  const idRef = React.useRef(0);
  const show = React.useCallback((message, opts={}) => {
    const id = ++idRef.current;
    const toast = { id, message, tone: opts.tone || 'info', duration: opts.duration || 4000 };
    setToasts(prev => [...prev, toast]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, toast.duration);
    return id;
  }, []);
  const dismiss = React.useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);
  return <ToastContext.Provider value={{ show, dismiss }}>
    {children}
    <div style={{position:'fixed', bottom:20, right:20, zIndex:90, display:'flex', flexDirection:'column', gap:8, maxWidth:340, width:'calc(100vw - 40px)'}}>
      {toasts.map(t => {
        const tones = {
          info:    { c:'#00e5ff', bg:'rgba(0,229,255,0.08)', bd:'rgba(0,229,255,0.25)' },
          success: { c:'#00ff7a', bg:'rgba(0,255,122,0.08)', bd:'rgba(0,255,122,0.25)' },
          warning: { c:'#ffc400', bg:'rgba(255,196,0,0.08)', bd:'rgba(255,196,0,0.25)' },
          error:   { c:'#ff3b5c', bg:'rgba(255,59,92,0.1)',  bd:'rgba(255,59,92,0.35)' },
        };
        const tone = tones[t.tone] || tones.info;
        return <div
          key={t.id}
          style={{
            background:'#060c1a', border:`1px solid ${tone.bd}`, borderLeft:`3px solid ${tone.c}`,
            borderRadius:2, padding:'10px 14px', boxShadow:'0 8px 24px rgba(0,0,0,0.4)',
            display:'flex', alignItems:'flex-start', gap:10,
            animation:'slide-up 240ms ease-out',
          }}
        >
          <div style={{flex:1, fontSize:12, color:'#ffffff', lineHeight:1.5}}>{t.message}</div>
          <i data-lucide="x" onClick={()=>dismiss(t.id)} style={{width:14, height:14, color:'#4a6880', cursor:'pointer', flexShrink:0, marginTop:1}}/>
        </div>;
      })}
    </div>
  </ToastContext.Provider>;
};

const Logo = ({ size=22, showWord=true, wordSize=15 }) => (
  <div style={{display:'flex', alignItems:'center', gap:10}}>
    <svg width={size} height={size*1.1} viewBox="0 0 24 26" fill="none" style={{flexShrink:0}}>
      <path d="M 2 4 L 12 2 L 22 4 L 22 14 L 12 24 L 2 14 Z" stroke="#00e5ff" strokeWidth="1.5" fill="none" strokeLinejoin="miter"/>
      <path d="M 7 8 L 12 7 L 17 8 L 17 14 L 12 19 L 7 14 Z" fill="#00e5ff" opacity="0.25"/>
      <circle cx="12" cy="12" r="1.5" fill="#00e5ff"/>
    </svg>
    {showWord && <span style={{fontFamily:"'Neue Haas Grotesk', 'Inter Tight', sans-serif", fontSize:wordSize, fontWeight:700, color:'#ffffff', letterSpacing:'-0.015em'}}>
      Reliant<span style={{color:'#00e5ff'}}>AI</span>
    </span>}
  </div>
);

Object.assign(window, { cx, CountUp, Badge, Btn, Panel, PanelHeader, MetricTile, ConfBar, Sparkline, Kbd, EmptyState, Skel, Tabs, Input, Divider, Logo, ToastContext, useToast, ToastProvider });
