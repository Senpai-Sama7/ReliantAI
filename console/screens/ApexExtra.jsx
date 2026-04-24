// Langfuse.jsx — APEX trace viewer + tool bus (appended to APEX screens)

const ApexLangfuse = () => {
  const [selected, setSelected] = React.useState(null);
  const [filter, setFilter] = React.useState('all');

  const traces = [
    { id:'TRC-9841', workflow:'contract-review', model:'claude-sonnet-4.5', spans:9,  cost:0.042, duration:4820, status:'completed', confidence:0.63, tier:'T3', ts:mins(2),  tokens:{in:4210, out:812} },
    { id:'TRC-9840', workflow:'revenue-summary', model:'claude-sonnet-4.5', spans:5,  cost:0.018, duration:2140, status:'completed', confidence:0.94, tier:'T1', ts:mins(4),  tokens:{in:1840, out:420} },
    { id:'TRC-9839', workflow:'expense-approval', model:'gpt-4.1',          spans:7,  cost:0.031, duration:3610, status:'hitl',      confidence:0.71, tier:'T2', ts:mins(9),  tokens:{in:2980, out:640} },
    { id:'TRC-9838', workflow:'anomaly-detect',   model:'claude-opus-4.5',  spans:12, cost:0.094, duration:8230, status:'completed', confidence:0.88, tier:'T1', ts:mins(14), tokens:{in:6120, out:1840} },
    { id:'TRC-9837', workflow:'outreach-draft',   model:'claude-sonnet-4.5',spans:6,  cost:0.024, duration:2980, status:'failed',    confidence:0.41, tier:'T3', ts:mins(18), tokens:{in:2210, out:540} },
    { id:'TRC-9836', workflow:'invoice-review',   model:'gpt-4.1',          spans:4,  cost:0.011, duration:1420, status:'completed', confidence:0.97, tier:'T1', ts:mins(22), tokens:{in:980,  out:210} },
  ];

  const SPAN_TYPES = ['analyze','calibration-gate','tool-call','quality-review','metacognitive','hitl-gate','output'];
  const statusTone = { completed:'green', hitl:'gold', failed:'red' };
  const tierColor  = { T1:'#00e5ff', T2:'#ffc400', T3:'#ff3b5c', T4:'#7c5cfc' };

  const SpanDetail = ({ trace }) => {
    const spanDurations = Array.from({length:trace.spans}, (_,i) => ({
      name: SPAN_TYPES[i % SPAN_TYPES.length],
      ms: Math.floor(trace.duration / trace.spans * (0.6 + Math.random()*0.8)),
      tool: i===2 ? ['hubspot.search','notion.query','stripe.retrieve'][i%3] : null,
      cost: trace.cost / trace.spans,
    }));
    const totalMs = spanDurations.reduce((a,s)=>a+s.ms,0);
    return <div style={{borderTop:'1px solid #0c1a2c', marginTop:0}}>
      {/* Flame chart */}
      <div style={{padding:'14px 18px', borderBottom:'1px solid #0c1a2c'}}>
        <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:8, fontFamily:'IBM Plex Mono,monospace'}}>Span timeline · {trace.duration}ms total</div>
        <div style={{position:'relative', height: trace.spans * 22 + 8}}>
          {spanDurations.map((s,i) => {
            const left = spanDurations.slice(0,i).reduce((a,x)=>a+x.ms,0) / totalMs * 100;
            const width = s.ms / totalMs * 100;
            const colors = { 'analyze':'#00e5ff','calibration-gate':'#7c5cfc','tool-call':'#ffc400','quality-review':'#00ff7a','metacognitive':'#7c5cfc','hitl-gate':'#ff3b5c','output':'#00d4aa' };
            return <div key={i} style={{position:'absolute', top: i*22, left:`${left}%`, width:`${Math.max(width,0.5)}%`, height:18, background:`${colors[s.name]||'#4a6880'}30`, border:`1px solid ${colors[s.name]||'#4a6880'}60`, display:'flex', alignItems:'center', paddingLeft:4, overflow:'hidden', fontSize:9, color:colors[s.name]||'#a8c4de', fontFamily:'IBM Plex Mono,monospace', whiteSpace:'nowrap'}}>
              {s.name}{s.tool?` · ${s.tool}`:''}
            </div>;
          })}
        </div>
      </div>
      {/* Span list */}
      <div style={{maxHeight:220, overflowY:'auto'}}>
        {spanDurations.map((s,i) => (
          <div key={i} style={{display:'flex', alignItems:'center', gap:12, padding:'8px 18px', borderBottom:'1px solid #0c1a2c', fontSize:11}}>
            <span style={{fontFamily:'IBM Plex Mono,monospace', color:'#4a6880', width:20}}>{i+1}</span>
            <span style={{fontFamily:'IBM Plex Mono,monospace', color:'#a8c4de', flex:1}}>{s.name}</span>
            {s.tool && <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#ffc400'}}>{s.tool}</span>}
            <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{s.ms}ms</span>
            <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>${s.cost.toFixed(4)}</span>
          </div>
        ))}
      </div>
      {/* Totals */}
      <div style={{padding:'10px 18px', display:'flex', gap:24, fontSize:10, fontFamily:'IBM Plex Mono,monospace', color:'#4a6880', borderTop:'1px solid #0c1a2c'}}>
        <span>tokens in: <span style={{color:'#a8c4de'}}>{trace.tokens.in.toLocaleString()}</span></span>
        <span>tokens out: <span style={{color:'#a8c4de'}}>{trace.tokens.out.toLocaleString()}</span></span>
        <span>total cost: <span style={{color:'#ffc400'}}>${trace.cost.toFixed(4)}</span></span>
        <span>model: <span style={{color:'#7c5cfc'}}>{trace.model}</span></span>
      </div>
    </div>;
  };

  const filtered = filter === 'all' ? traces : traces.filter(t => t.status === filter || t.tier === filter);
  const todayCost = traces.reduce((a,t) => a+t.cost, 0);

  return <div style={{display:'flex', height:'calc(100vh - 44px)'}}>
    {/* Trace list */}
    <div style={{flex:1, display:'flex', flexDirection:'column', minWidth:0}}>
      <div style={{padding:'18px 24px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:16}}>
        <div>
          <div style={{fontSize:10, color:'#7c5cfc', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:3, fontFamily:'IBM Plex Mono,monospace'}}>APEX · Langfuse</div>
          <div style={{fontSize:20, fontWeight:600, color:'#ffffff'}}>Trace Explorer</div>
        </div>
        <div style={{flex:1}}/>
        <Panel style={{padding:'8px 16px', display:'flex', gap:20}}>
          {[['traces today',traces.length,'#ffffff'],['cost today',`$${todayCost.toFixed(3)}`,'#ffc400'],['avg duration',`${Math.floor(traces.reduce((a,t)=>a+t.duration,0)/traces.length)}ms`,'#a8c4de'],['hitl rate',`${Math.round(traces.filter(t=>t.status==='hitl').length/traces.length*100)}%`,'#ffc400']].map(([k,v,c])=>(
            <div key={k}>
              <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:2}}>{k}</div>
              <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:14, fontWeight:600, color:c}}>{v}</div>
            </div>
          ))}
        </Panel>
      </div>

      {/* Filter pills */}
      <div style={{padding:'8px 24px', borderBottom:'1px solid #0c1a2c', display:'flex', gap:6}}>
        {['all','completed','hitl','failed','T1','T2','T3'].map(f => (
          <div key={f} onClick={()=>setFilter(f)} style={{fontSize:10, padding:'3px 10px', borderRadius:2, cursor:'pointer', border:`1px solid ${filter===f?'#7c5cfc60':'#0c1a2c'}`, background:filter===f?'rgba(124,92,252,0.1)':'transparent', color:filter===f?'#7c5cfc':'#4a6880', transition:'all 120ms'}}>{f}</div>
        ))}
      </div>

      {/* Table */}
      <div style={{flex:1, overflowY:'auto'}}>
        <table style={{width:'100%', borderCollapse:'collapse'}}>
          <thead>
            <tr style={{background:'#091424', position:'sticky', top:0}}>
              {['Trace ID','Workflow','Model','Tier','Spans','Duration','Tokens','Cost','Status','Age'].map(h=>(
                <th key={h} style={{padding:'8px 14px', textAlign:'left', fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.07em', borderBottom:'1px solid #152637', whiteSpace:'nowrap'}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(t => (
              <React.Fragment key={t.id}>
                <tr onClick={()=>setSelected(selected?.id===t.id ? null : t)}
                  style={{borderBottom:'1px solid #0c1a2c', cursor:'pointer', background:selected?.id===t.id?'#091424':'transparent'}}
                  onMouseEnter={e=>{ if(selected?.id!==t.id) e.currentTarget.style.background='#091424'; }}
                  onMouseLeave={e=>{ if(selected?.id!==t.id) e.currentTarget.style.background='transparent'; }}>
                  <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#7c5cfc'}}>{t.id}</td>
                  <td style={{padding:'9px 14px', fontSize:12, color:'#a8c4de'}}>{t.workflow}</td>
                  <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{t.model}</td>
                  <td style={{padding:'9px 14px'}}><span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, fontWeight:600, color:tierColor[t.tier]}}>{t.tier}</span></td>
                  <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de'}}>{t.spans}</td>
                  <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de'}}>{t.duration}ms</td>
                  <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{(t.tokens.in+t.tokens.out).toLocaleString()}</td>
                  <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#ffc400'}}>${t.cost.toFixed(4)}</td>
                  <td style={{padding:'9px 14px'}}><Badge label={t.status.toUpperCase()} tone={statusTone[t.status]||'neutral'} size="xs"/></td>
                  <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{fmtAgo(t.ts)}</td>
                </tr>
                {selected?.id===t.id && <tr><td colSpan={10} style={{padding:0, background:'#060c1a'}}><SpanDetail trace={t}/></td></tr>}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>;
};

const ApexTools = () => {
  const tools = [
    { name:'hubspot.contacts.search',  status:'CLOSED', calls:284, lat:'180ms', circuit:'green', category:'CRM' },
    { name:'hubspot.deals.create',     status:'CLOSED', calls:42,  lat:'210ms', circuit:'green', category:'CRM' },
    { name:'notion.pages.query',       status:'CLOSED', calls:128, lat:'320ms', circuit:'green', category:'Knowledge' },
    { name:'notion.pages.create',      status:'HALF_OPEN',calls:8, lat:'—',     circuit:'gold',  category:'Knowledge' },
    { name:'stripe.customers.retrieve',status:'CLOSED', calls:94,  lat:'145ms', circuit:'green', category:'Billing' },
    { name:'stripe.invoices.list',     status:'CLOSED', calls:31,  lat:'162ms', circuit:'green', category:'Billing' },
    { name:'composio.gmail.send',      status:'CLOSED', calls:18,  lat:'890ms', circuit:'green', category:'Comms' },
    { name:'composio.slack.post',      status:'CLOSED', calls:64,  lat:'240ms', circuit:'green', category:'Comms' },
    { name:'cleardesk.documents.get',  status:'CLOSED', calls:412, lat:'94ms',  circuit:'green', category:'Internal' },
    { name:'money.dispatches.list',    status:'CLOSED', calls:88,  lat:'112ms', circuit:'green', category:'Internal' },
    { name:'bap.insights.query',       status:'CLOSED', calls:56,  lat:'280ms', circuit:'green', category:'Internal' },
    { name:'web.search',               status:'OPEN',   calls:0,   lat:'—',     circuit:'red',   category:'External' },
    { name:'calendar.availability',    status:'CLOSED', calls:12,  lat:'440ms', circuit:'green', category:'Comms' },
    { name:'cloudflare.kv.get',        status:'CLOSED', calls:2840,lat:'8ms',   circuit:'green', category:'Infra' },
    { name:'cloudflare.kv.set',        status:'CLOSED', calls:914, lat:'9ms',   circuit:'green', category:'Infra' },
  ];
  const [manual, setManual] = React.useState({ tool:'', input:'', result:null, running:false });
  const categories = [...new Set(tools.map(t=>t.category))];
  const [catFilter, setCatFilter] = React.useState('All');

  const runTool = () => {
    if (!manual.tool) return;
    setManual(m=>({...m, running:true, result:null}));
    setTimeout(()=>setManual(m=>({...m, running:false, result:`{\n  "status": "ok",\n  "tool": "${m.tool}",\n  "latency_ms": ${Math.floor(Math.random()*300+50)},\n  "result": { "count": ${Math.floor(Math.random()*40+1)}, "data": "[...truncated]" }\n}`})), 800+Math.random()*600);
  };

  const filtered = catFilter==='All' ? tools : tools.filter(t=>t.category===catFilter);

  return <div style={{padding:'24px 32px'}}>
    <div style={{marginBottom:22}}>
      <div style={{fontSize:10, color:'#7c5cfc', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>APEX · MCP Tool Bus</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Registered tools · {tools.length}</h1>
    </div>

    <div style={{display:'grid', gridTemplateColumns:'1.6fr 1fr', gap:20, marginBottom:20}}>
      <Panel>
        <PanelHeader title="Tool registry" sub="GET /tools · circuit breaker status" right={
          <div style={{display:'flex', gap:6}}>
            {['All',...categories].map(c=>(
              <div key={c} onClick={()=>setCatFilter(c)} style={{fontSize:10, padding:'2px 8px', borderRadius:2, cursor:'pointer', background:catFilter===c?'rgba(124,92,252,0.12)':'transparent', color:catFilter===c?'#7c5cfc':'#4a6880', border:`1px solid ${catFilter===c?'rgba(124,92,252,0.3)':'#0c1a2c'}`}}>{c}</div>
            ))}
          </div>
        }/>
        <div style={{maxHeight:400, overflowY:'auto'}}>
          {filtered.map(t=>(
            <div key={t.name} style={{padding:'9px 16px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:12}}
              onMouseEnter={e=>e.currentTarget.style.background='#091424'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
              <div style={{width:8, height:8, borderRadius:'50%', flexShrink:0, background:t.circuit==='green'?'#00ff7a':t.circuit==='gold'?'#ffc400':'#ff3b5c', boxShadow:`0 0 4px ${t.circuit==='green'?'#00ff7a':t.circuit==='gold'?'#ffc400':'#ff3b5c'}60`}}/>
              <div style={{flex:1, fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de', cursor:'pointer'}} onClick={()=>setManual(m=>({...m, tool:t.name}))}>{t.name}</div>
              <span style={{fontSize:9, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{t.calls} calls</span>
              <span style={{fontSize:9, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', width:50, textAlign:'right'}}>{t.lat}</span>
              <Badge label={t.status} tone={t.status==='CLOSED'?'green':t.status==='OPEN'?'red':'gold'} size="xs"/>
            </div>
          ))}
        </div>
      </Panel>

      <Panel>
        <PanelHeader title="Manual tool call" sub="POST /tools/call"/>
        <div style={{padding:16, display:'flex', flexDirection:'column', gap:12}}>
          <div>
            <div style={{fontSize:10, color:'#4a6880', marginBottom:5, textTransform:'uppercase', letterSpacing:'0.08em'}}>Tool</div>
            <select value={manual.tool} onChange={e=>setManual(m=>({...m,tool:e.target.value}))} style={{width:'100%', background:'#091424', border:'1px solid #152637', color:manual.tool?'#ffffff':'#4a6880', fontSize:12, padding:'7px 10px', borderRadius:2, outline:'none'}}>
              <option value="">Select a tool…</option>
              {tools.filter(t=>t.status!=='OPEN').map(t=><option key={t.name} value={t.name}>{t.name}</option>)}
            </select>
          </div>
          <div>
            <div style={{fontSize:10, color:'#4a6880', marginBottom:5, textTransform:'uppercase', letterSpacing:'0.08em'}}>Input (JSON)</div>
            <textarea value={manual.input} onChange={e=>setManual(m=>({...m,input:e.target.value}))} placeholder={'{\n  "query": "at-risk accounts"\n}'} style={{width:'100%', height:80, background:'#091424', border:'1px solid #152637', color:'#ffffff', fontSize:11, padding:'8px 10px', resize:'none', outline:'none', fontFamily:'IBM Plex Mono,monospace', borderRadius:2}}/>
          </div>
          <Btn variant="primary" tone="apex" icon={manual.running?'loader':'play'} disabled={!manual.tool||manual.running} onClick={runTool}>
            {manual.running?'Running…':'Execute tool'}
          </Btn>
          {manual.result && <div style={{background:'#020510', border:'1px solid #0c1a2c', padding:12, fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#00ff7a', whiteSpace:'pre', overflowX:'auto', borderRadius:1}}>{manual.result}</div>}
        </div>
      </Panel>
    </div>
  </div>;
};

Object.assign(window, { ApexLangfuse, ApexTools });
