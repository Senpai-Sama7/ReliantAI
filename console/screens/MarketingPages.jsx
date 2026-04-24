// MarketingPages.jsx — individual service landing pages

const MarketingClearDesk = () => {
  const CD = '#00FF94';
  return <div style={{minHeight:'100vh', background:'#020510', overflowY:'auto'}}>
    <nav style={{position:'sticky', top:0, zIndex:50, padding:'0 48px', height:60, display:'flex', alignItems:'center', background:'rgba(2,5,16,0.96)', backdropFilter:'blur(12px)', borderBottom:'1px solid #0c1a2c'}}>
      <div onClick={()=>window.go('/marketing/home')} style={{cursor:'pointer'}}><Logo size={18} wordSize={14}/></div>
      <div style={{flex:1}}/>
      <div style={{display:'flex', gap:24, marginRight:24}}>
        {['Product','Security','Pricing','Docs'].map(l=><span key={l} style={{fontSize:12, color:'#4a6880', cursor:'pointer'}}>{l}</span>)}
      </div>
      <Btn size="sm" variant="primary" tone="cleardesk" onClick={()=>window.go('/cleardesk/landing')}>Open ClearDesk</Btn>
    </nav>

    {/* Hero */}
    <div style={{padding:'100px 80px 80px', maxWidth:1100, margin:'0 auto'}}>
      <div style={{display:'inline-flex', alignItems:'center', gap:8, padding:'5px 14px', border:`1px solid ${CD}30`, background:`${CD}08`, borderRadius:2, marginBottom:28, fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:CD, letterSpacing:'0.1em'}}>
        <div style={{width:5, height:5, borderRadius:'50%', background:CD, animation:'pulse 1.4s ease infinite'}}/>
        CLEARDESK · v3.4.1 · ACTIVE PRODUCT
      </div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk','Inter Tight',sans-serif", fontSize:68, fontWeight:700, color:'#ffffff', letterSpacing:'-0.035em', lineHeight:1.0, marginBottom:24}}>
        AP automation<br/>that reads the fine print.
      </h1>
      <p style={{fontSize:17, color:'#a8c4de', maxWidth:560, lineHeight:1.7, marginBottom:40}}>
        ClearDesk extracts, scores, escalates, and exports your accounts payable documents — with a human in every loop that matters. Text-safe previews. Signed share codes. Dual-language summaries.
      </p>
      <div style={{display:'flex', gap:12}}>
        <Btn size="lg" variant="primary" tone="cleardesk" icon="arrow-right" onClick={()=>window.go('/cleardesk/queue')}>Open workspace</Btn>
        <Btn size="lg" variant="secondary" icon="book-open">Read the guardrails</Btn>
      </div>
    </div>

    {/* Stats */}
    <div style={{display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:2, background:'#0c1a2c', margin:'0 80px 80px'}}>
      {[['99.4%','extraction accuracy','90-day rolling average'],['4.3s','batch parse time','12 docs · parallel OCR'],['28','languages supported','OCR + Claude summarization'],['0','tokens in browser','by design · always']].map(([v,l,s])=>(
        <div key={l} style={{background:'#060c1a', padding:'28px 24px', borderTop:`2px solid ${CD}`}}>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:36, fontWeight:700, color:CD, marginBottom:6}}>{v}</div>
          <div style={{fontSize:13, color:'#ffffff', marginBottom:4}}>{l}</div>
          <div style={{fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{s}</div>
        </div>
      ))}
    </div>

    {/* Features */}
    <div style={{padding:'0 80px 80px', maxWidth:1100, margin:'0 auto'}}>
      <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.14em', textTransform:'uppercase', marginBottom:40, fontFamily:'IBM Plex Mono,monospace'}}>What ClearDesk does</div>
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:2, background:'#0c1a2c'}}>
        {[
          ['file-text','Document parsing','PDF, PNG, JPG, TIFF, EML, DOCX. OCR auto-selected per format. Parallel batch processing.'],
          ['cpu','AI extraction','Claude Sonnet extracts vendor, amount, dates, PO references. Dual-language summaries (EN + 27 others).'],
          ['shield-check','Confidence scoring','Every field gets a 0–1 confidence score. Below your threshold → human queue. Never silent failures.'],
          ['alert-triangle','Escalation rules','Amount ceiling, confidence floor, vendor allowlist, PO requirement — all configurable per org.'],
          ['message-circle','AI chat assistant','Ask questions about your document queue in plain language. Context-injected, not hallucinated.'],
          ['download','Flexible export','CSV, JSON, or XLSX. Choose fields. Filter scope. Audit-ready with full provenance.'],
          ['shield','Text-safe preview','DOMPurify on every render. No raw HTML insertion. No scripts from document bytes. Ever.'],
          ['key','Signed sync codes','Cross-device access via 6-char short-lived codes. No raw UUIDs. No tokens in browser storage.'],
        ].map(([icon, title, desc])=>(
          <div key={title} style={{background:'#060c1a', padding:'28px 24px', display:'flex', gap:16}}>
            <div style={{width:32, height:32, background:`${CD}12`, border:`1px solid ${CD}25`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, marginTop:2}}>
              <i data-lucide={icon} style={{width:15, height:15, color:CD}}/>
            </div>
            <div>
              <div style={{fontSize:13, fontWeight:600, color:'#ffffff', marginBottom:6}}>{title}</div>
              <div style={{fontSize:12, color:'#a8c4de', lineHeight:1.6}}>{desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>

    <div style={{padding:'60px 80px', borderTop:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'center', fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
      <Logo size={16} wordSize={13}/>
      <span>ClearDesk · Active product · ops@reliant.ai</span>
    </div>
  </div>;
};

const MarketingMoney = () => {
  const G = '#ffc400';
  const steps = [
    { n:'01', title:'Attract', body:'Customer calls or texts. Money picks up in < 2s, 24/7. No hold music. No voicemail.' },
    { n:'02', title:'Qualify', body:'triage_agent scores urgency: ROUTINE → URGENT → EMERGENCY → LIFE_SAFETY. Gas/CO triggers 911 — never a technician.' },
    { n:'03', title:'Convert', body:'intake_agent captures the job. scheduler_agent finds the right tech. dispatch_agent sends them. All in under 30 seconds.' },
  ];
  return <div style={{minHeight:'100vh', background:'#0b0c0e', overflowY:'auto'}}>
    <nav style={{position:'sticky', top:0, zIndex:50, padding:'0 48px', height:60, display:'flex', alignItems:'center', background:'rgba(11,12,14,0.96)', backdropFilter:'blur(12px)', borderBottom:'1px solid #1a1c20'}}>
      <div onClick={()=>window.go('/marketing/home')} style={{cursor:'pointer'}}><Logo size={18} wordSize={14}/></div>
      <div style={{flex:1}}/>
      <Btn size="sm" variant="primary" tone="money" onClick={()=>window.go('/money/admin')}>Open Money</Btn>
    </nav>

    {/* Ken Burns hero */}
    <div style={{height:'85vh', position:'relative', overflow:'hidden', display:'flex', alignItems:'center', justifyContent:'center'}}>
      <div style={{position:'absolute', inset:0, background:`url('/assets/breath-bg.jpg') center/cover no-repeat`, filter:'brightness(0.18) saturate(0.6)'}}/>
      <div style={{position:'absolute', inset:0, background:'linear-gradient(to bottom, transparent 50%, #0b0c0e 100%)'}}/>
      <div style={{position:'relative', textAlign:'center', maxWidth:800, padding:'0 32px'}}>
        <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:G, letterSpacing:'0.12em', marginBottom:24}}>MONEY · HVAC AI DISPATCH</div>
        <h1 style={{fontFamily:"'Neue Haas Grotesk','Inter Tight',sans-serif", fontSize:76, fontWeight:700, color:'#ffffff', letterSpacing:'-0.04em', lineHeight:0.95, marginBottom:24}}>
          7× more likely<br/>to <span style={{color:G}}>qualify.</span>
        </h1>
        <p style={{fontSize:17, color:'#a8c4de', lineHeight:1.6, maxWidth:520, margin:'0 auto 36px'}}>
          HBR research: leads contacted within 60 minutes are 7× more likely to qualify. The industry average is 24–48 hours. Money responds in seconds.
        </p>
        <div style={{display:'flex', gap:12, justifyContent:'center'}}>
          <Btn size="lg" variant="primary" tone="money" icon="radio" onClick={()=>window.go('/money/admin')}>View admin portal</Btn>
          <Btn size="lg" variant="secondary" icon="play">Watch dispatch demo</Btn>
        </div>
      </div>
    </div>

    {/* CardStack */}
    <div style={{padding:'80px 80px', maxWidth:1100, margin:'0 auto'}}>
      <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.14em', textTransform:'uppercase', marginBottom:48, fontFamily:'IBM Plex Mono,monospace'}}>The dispatch pipeline</div>
      <div style={{display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:2, background:'#1a1c20'}}>
        {steps.map(s=>(
          <div key={s.n} style={{background:'#111318', padding:'36px 28px', borderTop:`2px solid ${G}`}}>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:40, fontWeight:700, color:G, opacity:0.3, marginBottom:16}}>{s.n}</div>
            <div style={{fontSize:18, fontWeight:600, color:'#ffffff', marginBottom:12}}>{s.title}</div>
            <div style={{fontSize:13, color:'#a8c4de', lineHeight:1.7}}>{s.body}</div>
          </div>
        ))}
      </div>
    </div>

    {/* Metrics */}
    <div style={{padding:'60px 80px', background:'#111318', borderTop:'1px solid #1a1c20', borderBottom:'1px solid #1a1c20'}}>
      <div style={{display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:40, maxWidth:1100, margin:'0 auto'}}>
        {[['< 30s','first response time'],['7×','qualification rate'],['5-agent','CrewAI pipeline'],['0','LIFE_SAFETY auto-dispatches']].map(([v,l])=>(
          <div key={l}>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:32, fontWeight:700, color:G, marginBottom:6}}>{v}</div>
            <div style={{fontSize:12, color:'#a8c4de'}}>{l}</div>
          </div>
        ))}
      </div>
    </div>

    <div style={{padding:'60px 80px', borderTop:'1px solid #1a1c20', display:'flex', justifyContent:'space-between', alignItems:'center', fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
      <Logo size={16} wordSize={13}/>
      <span>Money · HVAC AI Dispatch · Houston TX</span>
    </div>
  </div>;
};

const MarketingAPEX = () => {
  const P = '#7c5cfc';
  const layers = [
    { l:'L1', name:'Analyze', desc:'Semantic parse, intent classification, domain novelty scoring' },
    { l:'L2', name:'Calibration Gate', desc:'Confidence scoring, tier assignment (T1–T4), uncertainty split' },
    { l:'L3', name:'Dispatch', desc:'Tool routing, specialist agent selection, parallel execution' },
    { l:'L4', name:'Quality Review', desc:'Output validation, coherence check, hallucination detection' },
    { l:'L5', name:'Metacognitive', desc:'Pattern learning, feedback capture, autonomous optimization' },
  ];
  return <div style={{minHeight:'100vh', background:'#020510', overflowY:'auto'}}>
    <nav style={{position:'sticky', top:0, zIndex:50, padding:'0 48px', height:60, display:'flex', alignItems:'center', background:'rgba(2,5,16,0.96)', backdropFilter:'blur(12px)', borderBottom:'1px solid #0c1a2c'}}>
      <div onClick={()=>window.go('/marketing/home')} style={{cursor:'pointer'}}><Logo size={18} wordSize={14}/></div>
      <div style={{flex:1}}/>
      <Btn size="sm" variant="primary" tone="apex" onClick={()=>window.go('/apex/overview')}>Open APEX</Btn>
    </nav>

    <div style={{padding:'100px 80px 60px', maxWidth:1100, margin:'0 auto'}}>
      <div style={{display:'inline-flex', alignItems:'center', gap:8, padding:'5px 14px', border:`1px solid ${P}30`, background:`${P}08`, borderRadius:2, marginBottom:28, fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:P, letterSpacing:'0.1em'}}>
        APEX · 5-LAYER AUTONOMOUS AGENT OS
      </div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk','Inter Tight',sans-serif", fontSize:68, fontWeight:700, color:'#ffffff', letterSpacing:'-0.035em', lineHeight:1.0, marginBottom:24}}>
        Every decision has<br/>a <span style={{color:P}}>confidence score.</span>
      </h1>
      <p style={{fontSize:17, color:'#a8c4de', maxWidth:600, lineHeight:1.7, marginBottom:56}}>
        APEX assigns every workflow a probabilistic tier — Reflexive, Deliberative, Contested, or Unknown — and routes it accordingly. Humans stay in every loop that matters. Uncertainty is visualized, not hidden.
      </p>

      {/* Layer stack */}
      <div style={{marginBottom:80}}>
        <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.14em', textTransform:'uppercase', marginBottom:20, fontFamily:'IBM Plex Mono,monospace'}}>Execution pipeline</div>
        <div style={{display:'flex', flexDirection:'column', gap:2}}>
          {layers.map((l,i)=>(
            <div key={l.l} style={{display:'flex', alignItems:'center', gap:0, background:'#060c1a', border:'1px solid #0c1a2c', overflow:'hidden'}}>
              <div style={{width:80, padding:'18px 20px', background:`${P}${Math.floor(15-i*2).toString(16).padStart(2,'0')}`, borderRight:'1px solid #0c1a2c', textAlign:'center', fontFamily:'IBM Plex Mono,monospace', fontSize:13, fontWeight:600, color:P}}>{l.l}</div>
              <div style={{padding:'18px 24px', flex:1}}>
                <div style={{fontSize:14, fontWeight:600, color:'#ffffff', marginBottom:4}}>{l.name}</div>
                <div style={{fontSize:12, color:'#a8c4de'}}>{l.desc}</div>
              </div>
              {i===1 && <div style={{padding:'0 20px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:P}}>T1–T4 assigned here</div>}
              {i===4 && <div style={{padding:'0 20px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#00ff7a'}}>Layer 5 · MAL</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Tier grid */}
      <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.14em', textTransform:'uppercase', marginBottom:20, fontFamily:'IBM Plex Mono,monospace'}}>Execution tiers</div>
      <div style={{display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:2, background:'#0c1a2c', marginBottom:80}}>
        {[
          ['T1','Reflexive','#00e5ff','conf ≥ 0.92, low novelty','Auto-approve. Log only. No human required.'],
          ['T2','Deliberative','#ffc400','conf 0.65–0.92','Approve with reasoning. Soft HITL.'],
          ['T3','Contested','#ff3b5c','conf < 0.65 or high stakes','Hard HITL. Decision required before proceed.'],
          ['T4','Unknown','#7c5cfc','domain novelty > 0.85','HITL + escalate to owner. Full audit trail.'],
        ].map(([t,l,c,cond,action])=>(
          <div key={t} style={{background:'#060c1a', padding:'24px 20px', borderTop:`2px solid ${c}`}}>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:22, fontWeight:700, color:c, marginBottom:4}}>{t}</div>
            <div style={{fontSize:13, fontWeight:600, color:'#ffffff', marginBottom:6}}>{l}</div>
            <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', marginBottom:10}}>{cond}</div>
            <div style={{fontSize:11, color:'#a8c4de'}}>{action}</div>
          </div>
        ))}
      </div>

      <div style={{display:'flex', gap:12}}>
        <Btn size="lg" variant="primary" tone="apex" icon="cpu" onClick={()=>window.go('/apex/hitl')}>Open HITL queue</Btn>
        <Btn size="lg" variant="secondary" icon="network" onClick={()=>window.go('/apex/langfuse')}>View trace explorer</Btn>
      </div>
    </div>

    <div style={{padding:'60px 80px', borderTop:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'center', fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
      <Logo size={16} wordSize={13}/>
      <span>APEX · Autonomous Agent OS · Next.js 15 · TypeScript</span>
    </div>
  </div>;
};

const MarketingBAP = () => {
  const T = '#00d4aa';
  return <div style={{minHeight:'100vh', background:'#020510', overflowY:'auto'}}>
    <nav style={{position:'sticky', top:0, zIndex:50, padding:'0 48px', height:60, display:'flex', alignItems:'center', background:'rgba(2,5,16,0.96)', backdropFilter:'blur(12px)', borderBottom:'1px solid #0c1a2c'}}>
      <div onClick={()=>window.go('/marketing/home')} style={{cursor:'pointer'}}><Logo size={18} wordSize={14}/></div>
      <div style={{flex:1}}/>
      <Btn size="sm" variant="primary" tone="bap" onClick={()=>window.go('/bap/analytics')}>Open B-A-P</Btn>
    </nav>

    <div style={{padding:'100px 80px 60px', maxWidth:1100, margin:'0 auto'}}>
      <div style={{display:'inline-flex', alignItems:'center', gap:8, padding:'5px 14px', border:`1px solid ${T}30`, background:`${T}08`, borderRadius:2, marginBottom:28, fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:T, letterSpacing:'0.1em'}}>
        B-A-P · BUSINESS ANALYTICS PLATFORM
      </div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk','Inter Tight',sans-serif", fontSize:68, fontWeight:700, color:'#ffffff', letterSpacing:'-0.035em', lineHeight:1.0, marginBottom:24}}>
        Your data.<br/><span style={{color:T}}>Actually analyzed.</span>
      </h1>
      <p style={{fontSize:17, color:'#a8c4de', maxWidth:600, lineHeight:1.7, marginBottom:48}}>
        Upload a CSV. B-A-P runs the ETL pipeline, generates AI insights, detects anomalies, builds forecasts, and feeds the results directly into your APEX agent context — automatically.
      </p>

      {/* Pipeline visual */}
      <div style={{marginBottom:80}}>
        <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.14em', textTransform:'uppercase', marginBottom:20, fontFamily:'IBM Plex Mono,monospace'}}>Automated pipeline</div>
        <div style={{display:'flex', alignItems:'stretch', gap:2, background:'#0c1a2c'}}>
          {[['upload-cloud','Upload','CSV, Excel, JSON, Parquet'],['check-square','Validate','Schema, nulls, types'],['shuffle','Transform','Clean, enrich, normalize'],['database','Load','Postgres + Redis cache'],['sparkles','Insights','Claude AI analysis']].map(([icon,label,sub],i)=>(
            <div key={label} style={{flex:1, background:'#060c1a', padding:'24px 16px', textAlign:'center', borderRight:i<4?'1px solid #0c1a2c':'none'}}>
              <i data-lucide={icon} style={{width:20, height:20, color:T, display:'block', margin:'0 auto 10px'}}/>
              <div style={{fontSize:12, fontWeight:600, color:'#ffffff', marginBottom:4}}>{label}</div>
              <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Features */}
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:2, background:'#0c1a2c', marginBottom:48}}>
        {[
          ['Anomaly detection','Statistical models flag outliers. Confidence-scored. Actionable.'],
          ['Revenue forecasting','AI models trained on your pipeline data. ± bounds included.'],
          ['Natural language queries','Ask questions in plain English. Get SQL + chart + summary.'],
          ['APEX context feed','Insights auto-injected into agent workflows. No copy-paste.'],
          ['Celery job queue','Parallel ETL with Redis backend. Progress streaming via SSE.'],
          ['Prometheus metrics','Cache hit rates, worker depth, lag — all in the console.'],
        ].map(([t,d])=>(
          <div key={t} style={{background:'#060c1a', padding:'24px 20px'}}>
            <div style={{fontSize:13, fontWeight:600, color:'#ffffff', marginBottom:6}}>{t}</div>
            <div style={{fontSize:12, color:'#a8c4de', lineHeight:1.6}}>{d}</div>
          </div>
        ))}
      </div>

      <div style={{display:'flex', gap:12}}>
        <Btn size="lg" variant="primary" tone="bap" icon="bar-chart-3" onClick={()=>window.go('/bap/analytics')}>Open analytics</Btn>
        <Btn size="lg" variant="secondary" icon="upload-cloud" onClick={()=>window.go('/bap/upload')}>Upload a dataset</Btn>
      </div>
    </div>

    <div style={{padding:'60px 80px', borderTop:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'center', fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
      <Logo size={16} wordSize={13}/>
      <span>B-A-P · FastAPI · Celery · Redis · Claude AI</span>
    </div>
  </div>;
};

Object.assign(window, { MarketingClearDesk, MarketingMoney, MarketingAPEX, MarketingBAP });
