// ConsoleHome.jsx — hub landing after sign-in
const ConsoleHome = () => {
  const [uptime, setUptime] = React.useState(0);
  React.useEffect(() => { const t = setInterval(()=>setUptime(u=>u+1), 1000); return ()=>clearInterval(t); }, []);
  const tiles = [
    { id:'cleardesk', name:'ClearDesk', tag:'AP automation', color:'#00FF94', icon:'file-text', path:'/cleardesk/queue',
      metrics:[['docs today',284,null],['escalated',12,'red'],['auto-export',89,'green']],
      status:'healthy' },
    { id:'money', name:'Money', tag:'HVAC dispatch', color:'#ffc400', icon:'radio', path:'/money/admin',
      metrics:[['dispatched',18,null],['life-safety',1,'red'],['revenue',12.4,'gold']],
      status:'healthy' },
    { id:'apex', name:'APEX', tag:'Agent orchestration', color:'#7c5cfc', icon:'cpu', path:'/apex/overview',
      metrics:[['traces/hr',420,null],['hitl queue',3,'orange'],['tool calls',2840,null]],
      status:'healthy' },
    { id:'bap', name:'B-A-P', tag:'Data pipelines', color:'#00d4aa', icon:'bar-chart-3', path:'/bap/analytics',
      metrics:[['pipelines',14,null],['rows/s',41_200,null],['lag',0.8,'green']],
      status:'healthy' },
  ];
  return <div style={{padding:'32px 40px', maxWidth:1400}}>
    <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:28}}>
      <div>
        <div style={{fontSize:11, color:'#00e5ff', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:6, fontFamily:'IBM Plex Mono,monospace'}}>Operator Console</div>
        <h1 style={{fontFamily:"'Neue Haas Grotesk','Inter Tight',sans-serif", fontSize:36, fontWeight:600, color:'#ffffff', letterSpacing:'-0.02em', lineHeight:1.1}}>
          Good afternoon, Lena.
        </h1>
        <div style={{fontSize:13, color:'#a8c4de', marginTop:8}}>
          Four services online. <span style={{color:'#ffc400'}}>3 decisions</span> waiting on you. Next SLA breach in 14 minutes.
        </div>
      </div>
      <div style={{display:'flex', gap:10}}>
        <Btn icon="plus" variant="secondary">Invite teammate</Btn>
        <Btn icon="command" variant="primary" tone="platform">Command palette <Kbd>⌘K</Kbd></Btn>
      </div>
    </div>

    {/* Service tiles */}
    <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:2, marginBottom:28, background:'#0c1a2c', border:'1px solid #0c1a2c'}}>
      {tiles.map(t => (
        <div key={t.id} onClick={()=>window.go(t.path)} style={{
          background:'#060c1a', padding:'22px 22px 16px', cursor:'pointer',
          transition:'background 150ms', position:'relative', overflow:'hidden',
        }} onMouseEnter={e=>e.currentTarget.style.background='#091424'} onMouseLeave={e=>e.currentTarget.style.background='#060c1a'}>
          <div style={{position:'absolute', top:0, left:0, right:0, height:2, background:t.color}}/>
          <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:16}}>
            <div style={{display:'flex', alignItems:'center', gap:10}}>
              <div style={{width:28, height:28, background:`${t.color}15`, border:`1px solid ${t.color}30`, borderRadius:2, display:'flex', alignItems:'center', justifyContent:'center'}}>
                <i data-lucide={t.icon} style={{width:14, height:14, color:t.color}}/>
              </div>
              <div>
                <div style={{fontSize:14, fontWeight:600, color:'#ffffff'}}>{t.name}</div>
                <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', marginTop:1}}>{t.tag}</div>
              </div>
            </div>
            <Badge label="live" tone="green" size="xs" pulse/>
          </div>
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:10}}>
            {t.metrics.map(([k,v,tone]) => (
              <div key={k}>
                <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:3}}>{k}</div>
                <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:16, fontWeight:600, color: tone==='red'?'#ff3b5c':tone==='gold'?'#ffc400':tone==='green'?'#00ff7a':tone==='orange'?'#ff8c00':'#ffffff'}}>
                  <CountUp to={v} decimals={v<10&&v%1!==0?1:0}/>{typeof v==='number'&&v>1000&&v!==41200?'':''}
                </div>
              </div>
            ))}
          </div>
          <div style={{marginTop:14, paddingTop:12, borderTop:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'center', fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
            <span>Open workspace</span>
            <i data-lucide="arrow-right" style={{width:11, height:11}}/>
          </div>
        </div>
      ))}
    </div>

    {/* Two-column: Attention + Quick routes */}
    <div style={{display:'grid', gridTemplateColumns:'1.4fr 1fr', gap:20, marginBottom:28}}>
      <Panel>
        <PanelHeader title="Needs your attention" sub="3 items · sorted by urgency" right={<Btn variant="ghost" size="sm">View all →</Btn>}/>
        <div>
          {[
            { sev:'critical', tag:'LIFE-SAFETY', title:'DSP-2419 · Gas odor at customer site', sub:'Money · 911 directive issued · 3m ago', action:'Review call' },
            { sev:'warn', tag:'ESCALATED', title:'INV-2026-0419 · $87,200 over threshold', sub:'ClearDesk · Aldridge Construction · 0.55 conf', action:'Approve or reject' },
            { sev:'info', tag:'HITL', title:'DEC-9417 · Liability cap 3.2x template', sub:'APEX · contract-review · waiting 7m', action:'Decide' },
          ].map((a,i) => (
            <div key={i} style={{padding:'14px 18px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'flex-start', gap:14, cursor:'pointer'}}>
              <div style={{width:3, alignSelf:'stretch', background: a.sev==='critical'?'#ff3b5c':a.sev==='warn'?'#ffc400':'#00e5ff', marginTop:2, animation: a.sev==='critical'?'pulse 1.4s ease infinite':'none'}}/>
              <div style={{flex:1}}>
                <div style={{display:'flex', gap:8, alignItems:'center', marginBottom:4}}>
                  <Badge label={a.tag} tone={a.sev==='critical'?'life':a.sev==='warn'?'gold':'cyan'} size="xs"/>
                </div>
                <div style={{fontSize:13, color:'#ffffff', marginBottom:3}}>{a.title}</div>
                <div style={{fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{a.sub}</div>
              </div>
              <Btn size="sm" variant="secondary">{a.action}</Btn>
            </div>
          ))}
        </div>
      </Panel>
      <Panel>
        <PanelHeader title="Platform signals" sub={`uptime ${Math.floor(uptime/60)}m ${uptime%60}s this session`}/>
        <div style={{padding:16, display:'flex', flexDirection:'column', gap:14}}>
          {[
            ['Event bus throughput', 2841, 'events/s', genTS(30, 2800, 0.04)],
            ['Cross-service latency p99', 184, 'ms', genTS(30, 180, 0.08)],
            ['Total spend today', 42.18, 'USD', genTS(30, 40, 0.05), 2],
          ].map(([label,val,unit,spark,dec]) => (
            <div key={label} style={{display:'flex', alignItems:'center', gap:14}}>
              <div style={{flex:1}}>
                <div style={{fontSize:10, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:3}}>{label}</div>
                <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:18, fontWeight:600, color:'#ffffff'}}>
                  <CountUp to={val} decimals={dec||0}/><span style={{fontSize:11, color:'#4a6880', marginLeft:4}}>{unit}</span>
                </div>
              </div>
              <Sparkline data={spark} width={100} height={32} color="#00e5ff"/>
            </div>
          ))}
        </div>
      </Panel>
    </div>

    {/* Quick routes */}
    <div>
      <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.14em', textTransform:'uppercase', marginBottom:12, fontFamily:'IBM Plex Mono,monospace'}}>Jump to</div>
      <div style={{display:'grid', gridTemplateColumns:'repeat(6, 1fr)', gap:8}}>
        {[
          ['/marketing/home','Marketing site','globe'],
          ['/cleardesk/landing','ClearDesk landing','file-text'],
          ['/integration/bus','Event bus','git-branch'],
          ['/apex/langfuse','Trace viewer','network'],
          ['/admin/billing','Billing','credit-card'],
          ['/handoff','Dev handoff','code'],
        ].map(([p,l,i]) => (
          <div key={p} onClick={()=>window.go(p)} style={{padding:'10px 14px', border:'1px solid #0c1a2c', background:'#060c1a', cursor:'pointer', display:'flex', alignItems:'center', gap:10}} onMouseEnter={e=>e.currentTarget.style.borderColor='#152637'} onMouseLeave={e=>e.currentTarget.style.borderColor='#0c1a2c'}>
            <i data-lucide={i} style={{width:12, height:12, color:'#00e5ff'}}/>
            <span style={{fontSize:11, color:'#a8c4de'}}>{l}</span>
          </div>
        ))}
      </div>
    </div>
  </div>;
};
window.ConsoleHome = ConsoleHome;
