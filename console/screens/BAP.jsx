// BAP.jsx — Business Analytics Platform workspace
const TEAL = '#00d4aa';

const BAPAnalytics = () => {
  const [activeChart, setActiveChart] = React.useState('revenue');
  const [tab, setTab] = React.useState('overview');

  const charts = {
    revenue:  { label:'Monthly Revenue', data: genTS(12, 280000, 0.12), color:'#ffc400', unit:'$', prefix:'$', decimals:0 },
    dispatch: { label:'Dispatches / week', data: genTS(16, 42, 0.15), color:'#00e5ff', unit:'', prefix:'', decimals:0 },
    conf:     { label:'Extraction confidence', data: genTS(20, 0.88, 0.04), color:'#00FF94', unit:'', prefix:'', decimals:2 },
  };
  const ch = charts[activeChart];
  const max = Math.max(...ch.data);
  const min = Math.min(...ch.data);
  const range = max - min || 1;
  const W = 560, H = 160, step = W / (ch.data.length - 1);
  const pts = ch.data.map((v,i) => ({ x: i*step, y: H - ((v-min)/range)*(H-20)-10 }));
  const pathD = 'M ' + pts.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' L ');
  const areaD = pathD + ` L ${W},${H} L 0,${H} Z`;

  return <div style={{padding:'24px 32px'}}>
    <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:22}}>
      <div>
        <div style={{fontSize:10, color:TEAL, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>B-A-P · Analytics</div>
        <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff', letterSpacing:'-0.015em'}}>Business Analytics</h1>
      </div>
      <div style={{display:'flex', gap:8}}>
        <Btn icon="upload" variant="secondary" onClick={()=>window.go('/bap/upload')}>Upload dataset</Btn>
        <Btn icon="git-branch" variant="primary" tone="bap" onClick={()=>window.go('/bap/pipeline')}>Pipeline builder</Btn>
      </div>
    </div>

    {/* KPI strip */}
    <Panel style={{marginBottom:20}}>
      <div style={{display:'flex'}}>
        <MetricTile icon="database" label="datasets" value={156} delta={+8}/>
        <MetricTile icon="activity" label="pipelines active" value={14} color="#00e5ff"/>
        <MetricTile icon="trending-up" label="rows processed" value={2100000} unit="M" color={TEAL}/>
        <MetricTile icon="zap" label="AI insights" value={89} color="#ffc400"/>
        <MetricTile icon="clock" label="avg pipeline" value={4.3} unit="s" decimals={1}/>
      </div>
    </Panel>

    {/* Chart selector tabs */}
    <div style={{display:'flex', gap:6, marginBottom:12}}>
      {Object.entries(charts).map(([id,c]) => (
        <div key={id} onClick={()=>setActiveChart(id)} style={{
          padding:'6px 14px', border:`1px solid ${activeChart===id?TEAL+'60':'#152637'}`,
          background: activeChart===id?`${TEAL}08`:'transparent', cursor:'pointer',
          fontSize:11, color:activeChart===id?TEAL:'#4a6880', transition:'all 150ms',
        }}>{c.label}</div>
      ))}
    </div>

    {/* Chart */}
    <Panel style={{marginBottom:20}}>
      <PanelHeader title={ch.label} sub={`${ch.data.length} data points · live`} right={<Btn variant="ghost" size="sm" icon="download">Export</Btn>}/>
      <div style={{padding:'20px 24px 16px'}}>
        <svg width="100%" viewBox={`0 0 ${W} ${H+20}`} style={{overflow:'visible'}}>
          <defs>
            <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ch.color} stopOpacity="0.2"/>
              <stop offset="100%" stopColor={ch.color} stopOpacity="0"/>
            </linearGradient>
          </defs>
          <path d={areaD} fill="url(#chartFill)"/>
          <path d={pathD} fill="none" stroke={ch.color} strokeWidth="1.5"/>
          {pts.map((p,i) => i%3===0 && <g key={i}>
            <circle cx={p.x} cy={p.y} r={3} fill={ch.color}/>
            <text x={p.x} y={H+16} textAnchor="middle" fontSize="9" fill="#4a6880">{i+1}</text>
          </g>)}
        </svg>
        <div style={{display:'flex', justifyContent:'space-between', fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', marginTop:4}}>
          <span>min: {ch.prefix}{min.toFixed(ch.decimals)}</span>
          <span>max: {ch.prefix}{max.toFixed(ch.decimals)}</span>
          <span>latest: {ch.prefix}{ch.data[ch.data.length-1].toFixed(ch.decimals)}</span>
        </div>
      </div>
    </Panel>

    {/* AI Insights */}
    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:20}}>
      <Panel>
        <PanelHeader title="AI Insights" sub="claude-sonnet-4.5 · last run 3m ago"/>
        {[
          { type:'anomaly',  conf:0.91, text:'Dispatch volume 42% above 7-day rolling average — likely weather-driven surge. Houston heat index ≥ 102°F.' },
          { type:'forecast', conf:0.87, text:'Q2 revenue projected at $1.24M ± $80k based on current pipeline velocity and historical close rates.' },
          { type:'summary',  conf:0.96, text:'ClearDesk extraction accuracy improved 1.2pp since threshold tuning on Apr 18. Escalation rate fell to 4.2%.' },
        ].map((ins,i) => (
          <div key={i} style={{padding:'12px 16px', borderBottom:'1px solid #0c1a2c'}}>
            <div style={{display:'flex', gap:8, alignItems:'center', marginBottom:6}}>
              <Badge label={ins.type.toUpperCase()} tone={ins.type==='anomaly'?'red':ins.type==='forecast'?'gold':'cyan'} size="xs"/>
              <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:9, color:'#4a6880'}}>conf: {ins.conf.toFixed(2)}</span>
            </div>
            <div style={{fontSize:12, color:'#a8c4de', lineHeight:1.6}}>{ins.text}</div>
          </div>
        ))}
      </Panel>
      <Panel>
        <PanelHeader title="ETL queue" sub="Celery · Redis backend"/>
        {[
          { name:'daily.snapshot', status:'running',   rows:'2.1M', t:'00:04:12' },
          { name:'dim.customers',  status:'completed', rows:'418k', t:'00:01:08' },
          { name:'fact.revenue',   status:'pending',   rows:'—',    t:'—' },
          { name:'ml.features',    status:'failed',    rows:'—',    t:'—', err:'OOM on worker-3' },
        ].map((j,i) => (
          <div key={i} style={{padding:'10px 16px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:12}}>
            <div style={{width:6, height:6, borderRadius:'50%', background:j.status==='running'?'#00e5ff':j.status==='completed'?'#00ff7a':j.status==='failed'?'#ff3b5c':'#4a6880', animation:j.status==='running'?'pulse 1.2s ease infinite':undefined}}/>
            <div style={{flex:1}}>
              <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#ffffff'}}>{j.name}</div>
              {j.err && <div style={{fontSize:10, color:'#ff3b5c', fontFamily:'IBM Plex Mono,monospace'}}>{j.err}</div>}
            </div>
            <span style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{j.rows}</span>
            <Badge label={j.status.toUpperCase()} tone={j.status==='running'?'cyan':j.status==='completed'?'green':j.status==='failed'?'red':'neutral'} size="xs"/>
          </div>
        ))}
      </Panel>
    </div>
  </div>;
};

const BAPPipeline = () => {
  const [nodes] = React.useState([
    { id:'upload',    x:40,  y:100, label:'Upload',    sub:'CSV/Excel/JSON', done:true, icon:'upload-cloud' },
    { id:'validate',  x:180, y:100, label:'Validate',  sub:'schema + types', done:true, icon:'check-square' },
    { id:'transform', x:320, y:100, label:'Transform', sub:'clean + enrich',  done:true, icon:'shuffle' },
    { id:'load',      x:460, y:100, label:'Load',      sub:'Postgres + cache',running:true, icon:'database' },
    { id:'insights',  x:600, y:100, label:'Insights',  sub:'AI analysis',     pending:true, icon:'sparkles' },
  ]);
  const edges = [[0,1],[1,2],[2,3],[3,4]];
  return <div style={{padding:'24px 32px'}}>
    <div style={{marginBottom:24}}>
      <div style={{fontSize:10, color:TEAL, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>B-A-P · Pipeline Builder</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>ETL pipeline · Houston_HVAC_2026.csv</h1>
    </div>
    <Panel style={{marginBottom:20}}>
      <div style={{padding:'32px 24px'}}>
        <svg viewBox="0 0 780 180" style={{width:'100%', overflow:'visible'}}>
          {edges.map(([a,b]) => {
            const A = nodes[a], B = nodes[b];
            const ax = A.x+64, ay = A.y+24, bx = B.x, by = B.y+24;
            const done = A.done && B.done;
            const active = A.done && B.running;
            return <line key={`${a}-${b}`} x1={ax} y1={ay} x2={bx} y2={by} stroke={done?TEAL:active?'#ffc400':'#0c1a2c'} strokeWidth="2" strokeDasharray={active?"6,4":undefined}>
              {active && <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="0.8s" repeatCount="indefinite"/>}
            </line>;
          })}
          {nodes.map(n => (
            <g key={n.id} transform={`translate(${n.x},${n.y-10})`}>
              <rect width="120" height="48" rx="1" fill={n.done?`${TEAL}18`:n.running?'rgba(0,229,255,0.1)':'#060c1a'} stroke={n.done?TEAL:n.running?'#00e5ff':'#152637'} strokeWidth="1"/>
              <text x="60" y="18" textAnchor="middle" fontSize="12" fill={n.done?'#ffffff':n.running?'#00e5ff':'#4a6880'} fontFamily="IBM Plex Sans,sans-serif" fontWeight="500">{n.label}</text>
              <text x="60" y="34" textAnchor="middle" fontSize="10" fill="#4a6880" fontFamily="IBM Plex Mono,monospace">{n.sub}</text>
              {n.running && <circle cx="108" cy="8" r="4" fill="#00e5ff"><animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite"/></circle>}
              {n.done && <text x="108" y="12" fontSize="10" fill={TEAL} textAnchor="middle">✓</text>}
            </g>
          ))}
        </svg>
      </div>
      <div style={{padding:'12px 24px', borderTop:'1px solid #0c1a2c', display:'flex', gap:20, fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
        <span>Job: etl-2026-04-23-1432</span>
        <span>Status: <span style={{color:'#00e5ff'}}>RUNNING</span></span>
        <span>4/5 stages</span>
        <span>Rows: 284,419</span>
        <span>Elapsed: 4m 12s</span>
      </div>
    </Panel>
    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:20}}>
      <Panel>
        <PanelHeader title="Stage log"/>
        {['[04:12] Validate complete — 284,419 rows, 24 columns, 0 schema errors','[04:09] Transform complete — 2.1% nulls filled, 14 columns type-cast','[04:08] Upload accepted — 284,419 rows at 61,024 rows/s','[04:01] Job created by lena.yu@reliant.ai'].map((l,i) => (
          <div key={i} style={{padding:'8px 16px', borderBottom:'1px solid #0c1a2c', fontSize:11, fontFamily:'IBM Plex Mono,monospace', color:'#a8c4de'}}>{l}</div>
        ))}
      </Panel>
      <Panel>
        <PanelHeader title="Quality checks" sub="automated pre-load validation"/>
        {[
          ['Duplicate rows','0 found','green'],
          ['Null ratio','2.1% — within 5% threshold','green'],
          ['Date formats','ISO 8601 — consistent','green'],
          ['Amount outliers','3 rows > 3σ — flagged for review','gold'],
          ['Schema match','24/24 columns — exact','green'],
        ].map(([k,v,tone]) => (
          <div key={k} style={{padding:'8px 16px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:12}}>
            <i data-lucide={tone==='green'?'check':'alert-triangle'} style={{width:12, height:12, color:tone==='green'?'#00ff7a':'#ffc400'}}/>
            <div style={{flex:1, fontSize:11, color:'#a8c4de'}}>{k}</div>
            <div style={{fontSize:11, color:'#4a6880'}}>{v}</div>
          </div>
        ))}
      </Panel>
    </div>
  </div>;
};

Object.assign(window, { BAPAnalytics, BAPPipeline });
