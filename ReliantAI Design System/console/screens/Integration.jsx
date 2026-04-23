// Integration.jsx — Integration Layer observability workspace

const IntegrationBus = () => {
  const [events, setEvents] = React.useState(EVENTS.slice());
  const [filter, setFilter] = React.useState('all');
  const sources = ['all','cleardesk','money','apex','bap','integration'];
  const kindColor = { info:'#00e5ff', warn:'#ffc400', critical:'#ff3b5c', success:'#00ff7a' };

  React.useEffect(() => {
    const msgs = [
      {src:'cleardesk.ingest', kind:'info',    msg:()=>`Parsed INV-2026-0${Math.floor(Math.random()*900)+100} · ${(0.8+Math.random()*0.19).toFixed(2)} conf`},
      {src:'money.dispatch',   kind:'info',    msg:()=>`DSP-${Math.floor(Math.random()*900)+2400} tech assigned · eta ${Math.floor(Math.random()*60)}m`},
      {src:'apex.langfuse',    kind:'info',    msg:()=>`Trace TRC-${Math.floor(Math.random()*9999)} · ${Math.floor(Math.random()*12)+2} spans`},
      {src:'bap.pipeline',     kind:'success', msg:()=>`${['daily','weekly','dim','fact'][Math.floor(Math.random()*4)]}.${['snapshot','revenue','customers','events'][Math.floor(Math.random()*4)]} complete`},
      {src:'integration.bus',  kind:'info',    msg:()=>`webhook.delivered ${['stripe','slack','hubspot'][Math.floor(Math.random()*3)]}.com · 200`},
    ];
    const t = setInterval(() => {
      const m = msgs[Math.floor(Math.random()*msgs.length)];
      setEvents(ev => [{t:new Date(), src:m.src, kind:m.kind, msg:m.msg()}, ...ev].slice(0,60));
    }, 2800);
    return () => clearInterval(t);
  }, []);

  const filtered = filter==='all' ? events : events.filter(e=>e.src.startsWith(filter));

  return <div style={{display:'flex', flexDirection:'column', height:'calc(100vh - 44px)'}}>
    <div style={{padding:'18px 24px', borderBottom:'1px solid #0c1a2c', flexShrink:0}}>
      <div style={{fontSize:10, color:'#00ff7a', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>Integration · Event Bus</div>
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
        <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:22, fontWeight:600, color:'#ffffff'}}>Live Event Stream</h1>
        <div style={{display:'flex', alignItems:'center', gap:8}}>
          <div style={{width:6, height:6, borderRadius:'50%', background:'#00ff7a', animation:'pulse 1.6s ease infinite'}}/>
          <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#4a6880'}}>Redis Streams · SSE · live</span>
        </div>
      </div>
    </div>
    <div style={{padding:'8px 24px', borderBottom:'1px solid #0c1a2c', display:'flex', gap:6, flexShrink:0}}>
      {sources.map(s => (
        <div key={s} onClick={()=>setFilter(s)} style={{fontSize:10, fontWeight:500, padding:'3px 10px', borderRadius:2, cursor:'pointer', border:`1px solid ${filter===s?'rgba(0,255,122,0.4)':'#0c1a2c'}`, background:filter===s?'rgba(0,255,122,0.08)':'transparent', color:filter===s?'#00ff7a':'#4a6880', transition:'all 120ms'}}>{s}</div>
      ))}
      <div style={{flex:1}}/>
      <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{filtered.length} events</span>
    </div>
    <div style={{flex:1, overflowY:'auto'}}>
      {filtered.map((e,i) => (
        <div key={i} style={{display:'flex', gap:14, padding:'8px 24px', borderBottom:'1px solid #0c1a2c', borderLeft:`3px solid ${kindColor[e.kind]}`, animation:i===0?'slide-up 180ms ease-out':undefined}}>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#1e3348', width:60, flexShrink:0, paddingTop:1}}>{fmtTime(e.t)}</div>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880', width:140, flexShrink:0, paddingTop:1}}>{e.src}</div>
          <div style={{fontSize:12, color:'#a8c4de', flex:1}}>{e.msg}</div>
          <Badge label={e.kind.toUpperCase()} tone={e.kind==='info'?'cyan':e.kind==='warn'?'gold':e.kind==='critical'?'red':'green'} size="xs"/>
        </div>
      ))}
    </div>
    <div style={{padding:'10px 24px', borderTop:'1px solid #0c1a2c', display:'flex', gap:20, fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', flexShrink:0}}>
      <span>channel: integration.events</span>
      <span>retention: 24h</span>
      <span>consumer group: console-ui</span>
      <span style={{color:'#00ff7a'}}>lag: 0ms</span>
    </div>
  </div>;
};

const IntegrationOverview = () => {
  const services = [
    { name:'auth-service',    port:8001, rate:'47/min',   lat:'8ms',  status:'healthy', rateLimit:'100/min' },
    { name:'event-bus',       port:8081, rate:'2841/min', lat:'2ms',  status:'healthy', rateLimit:'2000/min' },
    { name:'apex-core',       port:8000, rate:'420/hr',   lat:'180ms',status:'healthy', rateLimit:'1000/min' },
    { name:'cleardesk-api',   port:8002, rate:'284/hr',   lat:'340ms',status:'healthy', rateLimit:'500/min' },
    { name:'money-api',       port:8003, rate:'18/hr',    lat:'94ms', status:'healthy', rateLimit:'50/min' },
    { name:'bap-api',         port:8004, rate:'12/hr',    lat:'220ms',status:'healthy', rateLimit:'200/min' },
    { name:'saga-orchestrator',port:8082,rate:'3 active', lat:'12ms', status:'healthy', rateLimit:'500/min' },
  ];
  const integrations = [
    { name:'Twilio', status:'connected', last:'12s ago', breaker:'CLOSED' },
    { name:'Anthropic Claude', status:'connected', last:'3s ago', breaker:'CLOSED' },
    { name:'Google Gemini', status:'connected', last:'1m ago', breaker:'CLOSED' },
    { name:'Stripe', status:'connected', last:'4m ago', breaker:'CLOSED' },
    { name:'HubSpot', status:'connected', last:'18m ago', breaker:'CLOSED' },
    { name:'Composio', status:'connected', last:'2m ago', breaker:'CLOSED' },
    { name:'Cloudflare KV', status:'connected', last:'8s ago', breaker:'CLOSED' },
    { name:'Notion', status:'degraded', last:'8m ago', breaker:'HALF_OPEN' },
  ];
  return <div style={{padding:'24px 32px'}}>
    <div style={{marginBottom:22}}>
      <div style={{fontSize:10, color:'#00ff7a', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>Integration · Service Registry</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Platform Infrastructure</h1>
    </div>
    <Panel style={{marginBottom:20}}>
      <PanelHeader title="Kong API Gateway" sub="declarative config · 7 services registered"/>
      <div style={{overflowX:'auto'}}>
        <table style={{width:'100%', borderCollapse:'collapse'}}>
          <thead>
            <tr style={{background:'#091424'}}>
              {['Service','Port','Rate','Latency p50','Rate limit','Status'].map(h=>(
                <th key={h} style={{padding:'8px 16px', textAlign:'left', fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', borderBottom:'1px solid #152637', whiteSpace:'nowrap'}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {services.map(s=>(
              <tr key={s.name} style={{borderBottom:'1px solid #0c1a2c'}} onMouseEnter={e=>e.currentTarget.style.background='#091424'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
                <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#00ff7a'}}>{s.name}</td>
                <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#4a6880'}}>{s.port}</td>
                <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#ffffff'}}>{s.rate}</td>
                <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de'}}>{s.lat}</td>
                <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#4a6880'}}>{s.rateLimit}</td>
                <td style={{padding:'9px 16px'}}><Badge label="OPERATIONAL" tone="green" size="xs"/></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
    <Panel>
      <PanelHeader title="Connected integrations" sub="MCP tool bus · circuit breaker status"/>
      <div style={{display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:1, background:'#0c1a2c'}}>
        {integrations.map(i=>(
          <div key={i.name} style={{background:'#060c1a', padding:'14px 16px'}}>
            <div style={{display:'flex', justifyContent:'space-between', marginBottom:6}}>
              <div style={{fontSize:12, color:'#ffffff', fontWeight:500}}>{i.name}</div>
              <Badge label={i.breaker} tone={i.breaker==='CLOSED'?'green':i.breaker==='OPEN'?'red':'gold'} size="xs"/>
            </div>
            <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>last: {i.last}</div>
          </div>
        ))}
      </div>
    </Panel>
  </div>;
};

Object.assign(window, { IntegrationBus, IntegrationOverview });
