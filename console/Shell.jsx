// Shell.jsx — global chrome: left rail + top bar + event feed + router
const { useState, useEffect, useRef, useCallback } = React;

// ── Command palette ─────────────────────────────────────────────
const CommandPalette = ({ open, onClose, routes, onGo }) => {
  const [q, setQ] = useState('');
  const [sel, setSel] = useState(0);
  const items = routes.filter(r => !q || (r.label+r.path+r.group).toLowerCase().includes(q.toLowerCase())).slice(0, 9);
  useEffect(() => { if (open) setQ(''); setSel(0); }, [open]);
  useEffect(() => {
    const h = (e) => {
      if (!open) return;
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => Math.min(s+1, items.length-1)); }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => Math.max(s-1, 0)); }
      if (e.key === 'Enter' && items[sel]) { onGo(items[sel].path); onClose(); }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [open, items, sel]);
  if (!open) return null;
  return <div className="re-cmd-palette" onClick={onClose} style={{position:'fixed', inset:0, background:'rgba(2,5,16,0.85)', zIndex:100, backdropFilter:'blur(6px)', display:'flex', alignItems:'flex-start', justifyContent:'center', paddingTop:'12vh'}}>
    <div onClick={e=>e.stopPropagation()} style={{width:560, background:'#060c1a', border:'1px solid #152637', borderRadius:2, boxShadow:'0 16px 48px rgba(0,0,0,0.6)'}}>
      <div style={{padding:'14px 18px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:10}}>
        <i data-lucide="search" style={{width:16, height:16, color:'#00e5ff'}}/>
        <input autoFocus value={q} onChange={e=>{setQ(e.target.value); setSel(0);}} placeholder="Jump to screen, service, or action…" style={{background:'transparent', border:'none', outline:'none', color:'#ffffff', fontSize:14, flex:1}}/>
        <Kbd>esc</Kbd>
      </div>
      <div style={{maxHeight:420, overflowY:'auto', padding:6}}>
        {items.length === 0 && <div style={{padding:'24px 16px', color:'#4a6880', fontSize:12}}>No matches for "{q}"</div>}
        {items.map((r, i) => (
          <div key={r.path} onMouseEnter={()=>setSel(i)} onClick={()=>{onGo(r.path); onClose();}} style={{
            display:'flex', alignItems:'center', gap:12, padding:'9px 12px', borderRadius:2,
            background: sel===i ? '#091424' : 'transparent', cursor:'pointer',
          }}>
            <i data-lucide={r.icon} style={{width:14, height:14, color: sel===i?'#00e5ff':'#4a6880'}}/>
            <div style={{flex:1}}>
              <div style={{fontSize:12, color:'#ffffff'}}>{r.label}</div>
              <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', marginTop:1}}>{r.group} · {r.path}</div>
            </div>
            {sel===i && <Kbd>↵</Kbd>}
          </div>
        ))}
      </div>
      <div style={{padding:'8px 12px', borderTop:'1px solid #0c1a2c', display:'flex', gap:12, fontSize:10, color:'#4a6880'}}>
        <span><Kbd>↑↓</Kbd> navigate</span>
        <span><Kbd>↵</Kbd> open</span>
        <span><Kbd>⌘K</Kbd> toggle</span>
      </div>
    </div>
  </div>;
};

// ── Event feed (right rail, live SSE sim) ───────────────────────
const useLiveEvents = () => {
  const [feed, setFeed] = useState(EVENTS.slice());
  useEffect(() => {
    const messages = [
      { src:'cleardesk.ingest', kind:'info', msg:()=>`Parsed INV-2026-${String(Math.floor(Math.random()*900)+100).padStart(4,'0')} · ${(0.7+Math.random()*0.3).toFixed(2)} conf · ${Math.floor(Math.random()*600)+200}ms` },
      { src:'apex.langfuse', kind:'info', msg:()=>`Trace TRC-${Math.floor(Math.random()*9999)} · ${Math.floor(Math.random()*10)+3} spans · $${(Math.random()*0.05).toFixed(3)}` },
      { src:'money.dispatch', kind:'info', msg:()=>`DSP-${Math.floor(Math.random()*900)+2400} assigned · ETA ${Math.floor(Math.random()*60)}m` },
      { src:'bap.pipeline', kind:'success', msg:()=>`fact.events materialized · ${(Math.random()*3+0.5).toFixed(1)}M rows` },
      { src:'integration.bus', kind:'info', msg:()=>`webhook.delivered · ${['stripe','slack','hubspot','gong'][Math.floor(Math.random()*4)]}.com · 200` },
    ];
    const tick = setInterval(() => {
      const m = messages[Math.floor(Math.random()*messages.length)];
      setFeed(f => [{ t:new Date(), src:m.src, kind:m.kind, msg:m.msg() }, ...f].slice(0, 40));
    }, 2600);
    return () => clearInterval(tick);
  }, []);
  return feed;
};

const EventFeed = ({ collapsed, onToggle }) => {
  const feed = useLiveEvents();
  if (collapsed) return <div className="re-event-feed" onClick={onToggle} style={{width:36, borderLeft:'1px solid #0c1a2c', background:'#060c1a', cursor:'pointer', display:'flex', flexDirection:'column', alignItems:'center', paddingTop:14, gap:12}}>
    <i data-lucide="activity" style={{width:14, height:14, color:'#00e5ff'}}/>
    <div style={{writingMode:'vertical-rl', transform:'rotate(180deg)', fontSize:10, color:'#4a6880', letterSpacing:'0.1em', textTransform:'uppercase'}}>Event Stream</div>
    <div style={{width:6, height:6, borderRadius:'50%', background:'#00ff7a', animation:'pulse 1.6s ease infinite', marginTop:'auto', marginBottom:14}}/>
  </div>;
  return <div className="re-event-feed" style={{width:300, borderLeft:'1px solid #0c1a2c', background:'#060c1a', display:'flex', flexDirection:'column'}}>
    <div style={{padding:'11px 14px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:8}}>
      <div style={{width:6, height:6, borderRadius:'50%', background:'#00ff7a', animation:'pulse 1.6s ease infinite'}}/>
      <div style={{fontSize:11, fontWeight:600, color:'#ffffff', letterSpacing:'0.04em'}}>EVENT STREAM</div>
      <div style={{flex:1}}/>
      <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>SSE · live</span>
      <i data-lucide="chevron-right" onClick={onToggle} style={{width:14, height:14, color:'#4a6880', cursor:'pointer'}}/>
    </div>
    <div style={{flex:1, overflowY:'auto', padding:'4px 0'}}>
      {feed.map((e,i) => {
        const colors = { info:'#00e5ff', warn:'#ffc400', critical:'#ff3b5c', success:'#00ff7a' };
        return <div key={i} style={{padding:'6px 14px', borderLeft:`2px solid ${colors[e.kind]}`, margin:'1px 0', animation: i===0 ? 'slide-left 240ms ease-out' : undefined}}>
          <div style={{display:'flex', justifyContent:'space-between', fontSize:9, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', marginBottom:2}}>
            <span>{e.src}</span><span>{fmtTime(e.t)}</span>
          </div>
          <div style={{fontSize:11, color:'#a8c4de', lineHeight:1.4}}>{e.msg}</div>
        </div>;
      })}
    </div>
    <div style={{padding:'8px 14px', borderTop:'1px solid #0c1a2c', fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', display:'flex', gap:10, justifyContent:'space-between'}}>
      <span>bus: integration.events</span>
      <span>{feed.length} recent</span>
    </div>
  </div>;
};

// ── Sidebar ─────────────────────────────────────────────────────
const Sidebar = ({ current, onGo, routes, expanded, onToggle }) => {
  const groups = [...new Set(routes.map(r => r.group))];
  const [openG, setOpenG] = useState({ Platform:true, ClearDesk:true, Money:true, APEX:true, 'B-A-P':true, Marketing:false, Admin:false });
  if (!expanded) return <div className="re-sidebar" style={{width:52, borderRight:'1px solid #0c1a2c', background:'#060c1a', display:'flex', flexDirection:'column', alignItems:'center', paddingTop:14, gap:4}}>
    <div onClick={onToggle} style={{cursor:'pointer', padding:8}}>
      <Logo size={20} showWord={false}/>
    </div>
    <div style={{height:1, width:30, background:'#0c1a2c', margin:'6px 0'}}/>
    {[
      {icon:'layout-dashboard', path:'/console/home'},
      {icon:'file-text', path:'/cleardesk/queue'},
      {icon:'radio', path:'/money/admin'},
      {icon:'cpu', path:'/apex/overview'},
      {icon:'bar-chart-3', path:'/bap/analytics'},
      {icon:'git-branch', path:'/integration/bus'},
      {icon:'settings', path:'/settings'},
    ].map(it => (
      <div key={it.path} onClick={()=>onGo(it.path)} title={it.path} style={{
        padding:9, cursor:'pointer', borderRadius:2, color: current.startsWith(it.path.split('/').slice(0,2).join('/'))?'#00e5ff':'#4a6880',
        background: current.startsWith(it.path.split('/').slice(0,2).join('/')) ? 'rgba(0,229,255,0.08)' : 'transparent',
      }}>
        <i data-lucide={it.icon} style={{width:16, height:16}}/>
      </div>
    ))}
  </div>;
  return <div className="re-sidebar" style={{width:224, borderRight:'1px solid #0c1a2c', background:'#060c1a', display:'flex', flexDirection:'column', overflow:'hidden'}}>
    <div style={{padding:'14px 16px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', justifyContent:'space-between'}}>
      <div onClick={()=>onGo('/console/home')} style={{cursor:'pointer'}}><Logo size={20} wordSize={14}/></div>
      <i data-lucide="panel-left-close" onClick={onToggle} style={{width:14, height:14, color:'#4a6880', cursor:'pointer'}}/>
    </div>
    <div style={{flex:1, overflowY:'auto', padding:'8px 0'}}>
      {groups.map(g => {
        const items = routes.filter(r => r.group === g);
        const tones = { Platform:'#00e5ff', ClearDesk:'#00FF94', Money:'#ffc400', APEX:'#7c5cfc', 'B-A-P':'#00d4aa', Marketing:'#ff8c00', Admin:'#a8c4de', Auth:'#4a6880' };
        return <div key={g} style={{marginBottom:4}}>
          <div onClick={()=>setOpenG(s=>({...s, [g]:!s[g]}))} style={{
            padding:'7px 16px', display:'flex', alignItems:'center', gap:6, cursor:'pointer',
            fontSize:9, fontWeight:600, letterSpacing:'0.12em', textTransform:'uppercase', color: tones[g]||'#4a6880',
          }}>
            <i data-lucide={openG[g]?'chevron-down':'chevron-right'} style={{width:10, height:10, opacity:0.5}}/>
            {g}
            <span style={{marginLeft:'auto', color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{items.length}</span>
          </div>
          {openG[g] && items.map(r => (
            <div key={r.path} onClick={()=>onGo(r.path)} style={{
              padding:'6px 16px 6px 30px', display:'flex', alignItems:'center', gap:8, cursor:'pointer',
              fontSize:12, color: current===r.path ? '#ffffff' : '#a8c4de',
              background: current===r.path ? 'rgba(0,229,255,0.06)' : 'transparent',
              borderLeft: current===r.path ? '2px solid #00e5ff' : '2px solid transparent',
            }}>
              <i data-lucide={r.icon} style={{width:12, height:12, color: current===r.path ? (tones[g]||'#00e5ff') : '#4a6880'}}/>
              <span style={{flex:1, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>{r.label}</span>
              {r.badge && <Badge label={r.badge} tone={r.badgeTone||'cyan'} size="xs"/>}
            </div>
          ))}
        </div>;
      })}
    </div>
    <div style={{padding:'10px 14px', borderTop:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:8}}>
      <div style={{width:24, height:24, borderRadius:'50%', background:'linear-gradient(135deg,#00e5ff,#7c5cfc)', fontSize:10, color:'#020510', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:700}}>LY</div>
      <div style={{flex:1, minWidth:0}}>
        <div style={{fontSize:11, color:'#ffffff', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis'}}>Lena Yu</div>
        <div style={{fontSize:9, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>ops@reliant.ai</div>
      </div>
      <i data-lucide="log-out" style={{width:13, height:13, color:'#4a6880', cursor:'pointer'}}/>
    </div>
  </div>;
};

// ── Top bar ────────────────────────────────────────────────────
const TopBar = ({ current, routes, onGo, onCmd, isMobile, onMenuClick }) => {
  const route = routes.find(r => r.path === current) || { label:'—', group:'' };
  return <div className="re-top-bar" style={{height:44, borderBottom:'1px solid #0c1a2c', background:'#060c1a', display:'flex', alignItems:'center', padding:'0 16px', gap:16}}>
    {isMobile && <i data-lucide="menu" onClick={onMenuClick} style={{width:18, height:18, color:'#a8c4de', cursor:'pointer'}}/>}
    <div className="re-breadcrumb" style={{display:'flex', alignItems:'center', gap:8, fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
      <span>reliant.ai</span>
      <i data-lucide="chevron-right" style={{width:10, height:10}}/>
      <span>{route.group}</span>
      <i data-lucide="chevron-right" style={{width:10, height:10}}/>
      <span style={{color:'#ffffff'}}>{route.label}</span>
    </div>
    <div style={{flex:1}}/>
    <div className="re-cmd-trigger" onClick={onCmd} style={{display:'flex', alignItems:'center', gap:10, padding:'6px 12px', background:'#091424', border:'1px solid #0c1a2c', borderRadius:2, cursor:'pointer', minWidth:260}}>
      <i data-lucide="search" style={{width:13, height:13, color:'#4a6880'}}/>
      <span style={{fontSize:11, color:'#4a6880', flex:1}}>Jump to anything…</span>
      <Kbd>⌘K</Kbd>
    </div>
    <div className="re-status-pill" style={{display:'flex', alignItems:'center', gap:4, padding:'4px 10px', background:'#091424', borderRadius:2, border:'1px solid #0c1a2c'}}>
      <div style={{width:6, height:6, borderRadius:'50%', background:'#00ff7a', animation:'pulse 1.6s ease infinite'}}/>
      <span style={{fontSize:10, color:'#a8c4de', fontFamily:'IBM Plex Mono,monospace'}}>all systems</span>
    </div>
    <i data-lucide="bell" style={{width:15, height:15, color:'#a8c4de', cursor:'pointer'}}/>
    <i data-lucide="book-open" style={{width:15, height:15, color:'#a8c4de', cursor:'pointer'}}/>
  </div>;
};

// ── Router ──────────────────────────────────────────────────────
const Router = ({ current, routes }) => {
  const route = routes.find(r => r.path === current);
  if (!route) return <div style={{padding:40, color:'#4a6880'}}>Route not found: {current}</div>;
  const Cmp = window[route.component];
  if (!Cmp) return <div style={{padding:40}}>
    <div style={{fontSize:13, color:'#ffc400', marginBottom:8}}>Screen stub: {route.label}</div>
    <div style={{fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>Component "{route.component}" not yet registered on window.</div>
  </div>;
  return <Cmp/>;
};

// ── App ────────────────────────────────────────────────────────
const useWindowWidth = () => {
  const [w, setW] = useState(window.innerWidth);
  useEffect(() => {
    const onResize = () => setW(window.innerWidth);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);
  return w;
};

const App = () => {
  const [current, setCurrent] = useState(() => localStorage.getItem('re:route') || '/console/home');
  const width = useWindowWidth();
  const isMobile = width <= 768;
  const isTablet = width <= 1024;
  const [sideEx, setSideEx] = useState(!isTablet);
  const [sideMobileOpen, setSideMobileOpen] = useState(false);
  const [feedEx, setFeedEx] = useState(width > 1400);
  const [cmdOpen, setCmdOpen] = useState(false);

  const go = useCallback((p) => { setCurrent(p); localStorage.setItem('re:route', p); if (isMobile) setSideMobileOpen(false); }, [isMobile]);

  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey||e.ctrlKey) && e.key === 'k') { e.preventDefault(); setCmdOpen(o=>!o); }
      if ((e.metaKey||e.ctrlKey) && e.key === 'b') { e.preventDefault(); setSideEx(s=>!s); }
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const routes = window.ROUTES || [];
  // Marketing + auth screens are fullscreen (no chrome)
  const route = routes.find(r => r.path === current);
  const fullscreen = route?.fullscreen;

  if (fullscreen) {
    return <div style={{height:'100vh', overflow:'auto', background:'#020510'}}>
      <Router current={current} routes={routes}/>
      <div style={{position:'fixed', top:14, left:14, zIndex:50}}>
        <Btn variant="secondary" size="sm" icon="arrow-left" onClick={()=>go('/console/home')}>Back to console</Btn>
      </div>
      <CommandPalette open={cmdOpen} onClose={()=>setCmdOpen(false)} routes={routes} onGo={go}/>
    </div>;
  }

  return <ToastProvider>
    <div style={{display:'flex', height:'100vh', overflow:'hidden'}}>
      {/* Mobile sidebar overlay */}
      {isMobile && sideMobileOpen && <div className="re-sidebar-overlay" onClick={()=>setSideMobileOpen(false)}/>}

      {isMobile ? (
        <div className={`re-sidebar-mobile ${sideMobileOpen ? 're-open' : ''}`} style={{position:'fixed', left:0, top:0, bottom:0, zIndex:40, transform:sideMobileOpen?'translateX(0)':'translateX(-100%)', transition:'transform 200ms ease'}}>
          <Sidebar current={current} onGo={go} routes={routes} expanded={true} onToggle={() => setSideMobileOpen(false)}/>
        </div>
      ) : (
        <Sidebar current={current} onGo={go} routes={routes} expanded={sideEx} onToggle={() => setSideEx(s=>!s)}/>
      )}

      <div style={{flex:1, display:'flex', flexDirection:'column', minWidth:0}}>
        <TopBar current={current} routes={routes} onGo={go} onCmd={()=>setCmdOpen(true)} isMobile={isMobile} onMenuClick={()=>setSideMobileOpen(true)}/>
        <div className="re-main" style={{flex:1, overflowY:'auto', background:'#020510'}}>
          <Router current={current} routes={routes}/>
        </div>
      </div>

      {!isTablet && <EventFeed collapsed={!feedEx} onToggle={()=>setFeedEx(e=>!e)}/>}
      <CommandPalette open={cmdOpen} onClose={()=>setCmdOpen(false)} routes={routes} onGo={go}/>
    </div>
  </ToastProvider>;
};

window.ReliantApp = App;
window.go = (p) => {
  const el = document.querySelector('[data-router]');
  if (el && el.__go) el.__go(p);
};
