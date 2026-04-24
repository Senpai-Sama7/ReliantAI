// APEX.jsx — autonomous agent OS workspace
const PURPLE = '#7c5cfc';

const UncertaintyGauge = ({ aleatoric, epistemic, confidence, width=200 }) => {
  const confW = confidence * width;
  const remW  = width - confW;
  const aleW  = remW * aleatoric / (aleatoric + epistemic || 1);
  const epiW  = remW - aleW;
  const color = confidence >= 0.92 ? '#00e5ff' : confidence >= 0.65 ? '#ffc400' : '#ff3b5c';
  return <div>
    <div style={{width, height:8, background:'#0c1a2c', display:'flex', overflow:'hidden', borderRadius:1}}>
      <div style={{width:confW, background:color, transition:'width 600ms'}}/>
      <div style={{width:aleW, background:'rgba(255,59,92,0.55)', transition:'width 600ms'}}/>
      <div style={{width:epiW, background:`rgba(124,92,252,0.55)`, transition:'width 600ms'}}/>
    </div>
    <div style={{display:'flex', gap:12, marginTop:4}}>
      {[['conf',confidence,color],['ale',aleatoric,'#ff3b5c80'],['epi',epistemic,`${PURPLE}80`]].map(([k,v,c]) => (
        <span key={k} style={{fontFamily:'IBM Plex Mono,monospace', fontSize:9, color:'#4a6880'}}>
          {k}: <span style={{color:'#a8c4de'}}>{v.toFixed(2)}</span>
        </span>
      ))}
    </div>
  </div>;
};

const TierBadge = ({ confidence, domain_novelty }) => {
  let tier, label, tone;
  if (confidence >= 0.92 && domain_novelty < 0.5) { tier='T1'; label='Reflexive'; tone='cyan'; }
  else if (confidence >= 0.65 && domain_novelty < 0.85) { tier='T2'; label='Deliberative'; tone='gold'; }
  else if (domain_novelty >= 0.85) { tier='T4'; label='Unknown'; tone='purple'; }
  else { tier='T3'; label='Contested'; tone='red'; }
  return <div style={{display:'flex', gap:6, alignItems:'center'}}>
    <Badge label={`${tier} · ${label}`} tone={tone} pulse={tier==='T4'}/>
  </div>;
};

const ApexOverview = () => {
  const metrics = [
    { label:'Traces today', value:2840, color:'#ffffff', spark:genTS(30, 2800, 0.05) },
    { label:'HITL pending', value:3, color:'#ffc400', spark:genTS(30, 3, 0.3) },
    { label:'Tool calls', value:18420, color:PURPLE, spark:genTS(30, 18000, 0.03) },
    { label:'Avg confidence', value:0.84, color:'#00ff7a', decimals:2, spark:genTS(30, 0.84, 0.02) },
    { label:'Cost today', value:42.18, color:'#ffc400', unit:'USD', decimals:2, spark:genTS(30, 40, 0.05) },
  ];
  const agents = [
    { id:'research',  status:'idle',   calls:1240, success:0.97, model:'claude-sonnet-4.5' },
    { id:'creative',  status:'active', calls:412,  success:0.94, model:'claude-opus-4.5' },
    { id:'analytics', status:'idle',   calls:3812, success:0.99, model:'gpt-4.1' },
    { id:'sales',     status:'idle',   calls:718,  success:0.91, model:'gemini-2.5-pro' },
  ];
  return <div style={{padding:'24px 32px'}}>
    <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:22}}>
      <div>
        <div style={{fontSize:10, color:PURPLE, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>APEX · System Overview</div>
        <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff', letterSpacing:'-0.015em'}}>Autonomous Agent OS</h1>
      </div>
      <div style={{display:'flex', gap:8}}>
        <Btn icon="play" variant="secondary" onClick={()=>window.go('/apex/workflows')}>New workflow</Btn>
        <Btn icon="clock" variant="primary" tone="apex" onClick={()=>window.go('/apex/hitl')}>
          Review HITL queue <Badge label={String(APEX_DECISIONS.length)} tone="red" size="xs" style={{marginLeft:4}}/>
        </Btn>
      </div>
    </div>
    <Panel style={{marginBottom:20}}>
      <div style={{display:'flex'}}>
        {metrics.map(m => (
          <div key={m.label} style={{flex:1, padding:'14px 18px', borderRight:'1px solid #0c1a2c'}}>
            <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:6}}>{m.label}</div>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:20, fontWeight:600, color:m.color, marginBottom:8}}>
              <CountUp to={m.value} decimals={m.decimals||0}/>{m.unit?<span style={{fontSize:10, color:'#4a6880', marginLeft:3}}>{m.unit}</span>:null}
            </div>
            <Sparkline data={m.spark} width={100} height={20} color={m.color}/>
          </div>
        ))}
      </div>
    </Panel>
    <div style={{display:'grid', gridTemplateColumns:'1.2fr 1fr', gap:20}}>
      <Panel>
        <PanelHeader title="Specialist agents" sub="4 registered · 1 active"/>
        {agents.map(a => (
          <div key={a.id} style={{padding:'12px 16px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:14}}>
            <div style={{width:8, height:8, borderRadius:'50%', background:a.status==='active'?'#00ff7a':'#1e3348', animation:a.status==='active'?'pulse 1.6s ease infinite':undefined}}/>
            <div style={{flex:1}}>
              <div style={{fontSize:12, color:'#ffffff', fontFamily:'IBM Plex Mono,monospace'}}>{a.id}_agent</div>
              <div style={{fontSize:10, color:'#4a6880', marginTop:1}}>{a.model} · {a.calls.toLocaleString()} calls · {(a.success*100).toFixed(0)}% success</div>
            </div>
            <Badge label={a.status.toUpperCase()} tone={a.status==='active'?'green':'neutral'} size="xs"/>
          </div>
        ))}
      </Panel>
      <Panel>
        <PanelHeader title="Execution tiers" sub="auto-assigned by confidence"/>
        {[
          ['T1','Reflexive','>0.92 · low stakes','cyan','→ auto-approve, log only'],
          ['T2','Deliberative','0.65–0.92','gold','→ approve with reasoning'],
          ['T3','Contested','<0.65 or high stakes','red','→ HITL required'],
          ['T4','Unknown','domain_novelty >0.85','purple','→ HITL + escalate'],
        ].map(([t,l,c,tone,action]) => (
          <div key={t} style={{padding:'10px 16px', borderBottom:'1px solid #0c1a2c', display:'grid', gridTemplateColumns:'100px 1fr auto', alignItems:'center', gap:12}}>
            <Badge label={`${t} · ${l}`} tone={tone} size="xs"/>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{c}</div>
            <div style={{fontSize:10, color:'#a8c4de'}}>{action}</div>
          </div>
        ))}
      </Panel>
    </div>
  </div>;
};

const ApexHITL = () => {
  const [decisions, setDecisions] = React.useState(APEX_DECISIONS);
  const [log, setLog] = React.useState([]);
  const [focused, setFocused] = React.useState(null);

  const decide = (id, action, reason='') => {
    setLog(l => [{ id, action, reason, ts:fmtTime(new Date()) }, ...l]);
    setDecisions(ds => ds.filter(d => d.id !== id));
    if (focused?.id === id) setFocused(null);
  };

  return <div style={{display:'flex', height:'calc(100vh - 44px)'}}>
    {/* Queue */}
    <div style={{width:380, borderRight:'1px solid #0c1a2c', overflowY:'auto', flexShrink:0}}>
      <div style={{padding:'16px 18px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:10}}>
        <div style={{fontSize:14, fontWeight:600, color:'#ffffff'}}>HITL Queue</div>
        <Badge label={String(decisions.length)} tone={decisions.length>0?'red':'green'} pulse={decisions.length>0}/>
        <div style={{flex:1}}/>
        <Btn size="xs" variant="secondary">Batch approve T2</Btn>
      </div>
      {decisions.length === 0 && <EmptyState icon="check-circle-2" title="Queue clear" body="All decisions resolved. Nice work."/>}
      {decisions.map(d => (
        <div key={d.id} onClick={()=>setFocused(d)} style={{padding:'14px 18px', borderBottom:'1px solid #0c1a2c', cursor:'pointer', background: focused?.id===d.id ? '#091424' : 'transparent', transition:'background 100ms'}}>
          <div style={{display:'flex', justifyContent:'space-between', marginBottom:6}}>
            <TierBadge confidence={d.confidence} domain_novelty={d.uncertainty}/>
            <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{fmtAgo(d.waitingSince)}</span>
          </div>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880', marginBottom:6}}>{d.id} · {d.workflow}</div>
          <div style={{fontSize:11, color:'#a8c4de', lineHeight:1.5, marginBottom:8}}>{d.reason}</div>
          <UncertaintyGauge aleatoric={d.uncertainty*0.5} epistemic={d.uncertainty*0.5} confidence={d.confidence} width={300}/>
        </div>
      ))}
      {log.length > 0 && <>
        <Divider label="resolved" style={{margin:'8px 16px'}}/>
        {log.map((l,i) => (
          <div key={i} style={{padding:'10px 18px', borderBottom:'1px solid #0c1a2c', fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
            <div style={{display:'flex', gap:8, alignItems:'center'}}>
              <div style={{width:6, height:6, borderRadius:'50%', background:l.action==='APPROVED'?'#00ff7a':'#ff3b5c'}}/>
              <span style={{color:l.action==='APPROVED'?'#00ff7a':'#ff3b5c'}}>{l.action}</span>
              <span>{l.id}</span>
              <span style={{marginLeft:'auto'}}>{l.ts}</span>
            </div>
            {l.reason && <div style={{marginTop:3, color:'#1e3348'}}>"{l.reason}"</div>}
          </div>
        ))}
      </>}
    </div>

    {/* Detail */}
    {focused ? <div style={{flex:1, overflowY:'auto', padding:'24px 28px'}}>
      <div style={{marginBottom:20}}>
        <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#4a6880', marginBottom:6}}>{focused.id} · {focused.workflow} · stage: {focused.stage}</div>
        <TierBadge confidence={focused.confidence} domain_novelty={focused.uncertainty}/>
      </div>
      <div style={{marginBottom:20}}>
        <div style={{fontSize:10, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:8, fontFamily:'IBM Plex Mono,monospace'}}>Input prompt</div>
        <Panel elevated style={{padding:14, fontSize:12, color:'#a8c4de', lineHeight:1.65}}>{focused.reason}</Panel>
      </div>
      <div style={{marginBottom:20}}>
        <div style={{fontSize:10, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:8, fontFamily:'IBM Plex Mono,monospace'}}>Evidence</div>
        <ul style={{listStyle:'none', margin:0, padding:0}}>
          {focused.evidence.map((e,i) => <li key={i} style={{padding:'7px 14px', borderBottom:'1px solid #0c1a2c', fontSize:12, color:'#a8c4de', fontFamily:'IBM Plex Mono,monospace', display:'flex', gap:10}}>
            <span style={{color:PURPLE}}>›</span>{e}
          </li>)}
        </ul>
      </div>
      <div style={{marginBottom:24}}>
        <div style={{fontSize:10, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:10, fontFamily:'IBM Plex Mono,monospace'}}>Uncertainty breakdown</div>
        <UncertaintyGauge aleatoric={focused.uncertainty*0.5} epistemic={focused.uncertainty*0.5} confidence={focused.confidence} width={400}/>
      </div>
      <HITLDecisionPanel decision={focused} onDecide={decide}/>
    </div> : <div style={{flex:1, display:'flex', alignItems:'center', justifyContent:'center'}}>
      <EmptyState icon="mouse-pointer" title="Select a decision" body="Click a queued item on the left to review the full evidence and decide."/>
    </div>}
  </div>;
};

const HITLDecisionPanel = ({ decision, onDecide }) => {
  const [reason, setReason] = React.useState('');
  const [decided, setDecided] = React.useState(null);
  if (decided) return <Panel elevated style={{padding:'16px 18px', display:'flex', alignItems:'center', gap:12}}>
    <div style={{width:8, height:8, borderRadius:'50%', background:decided==='APPROVED'?'#00ff7a':'#ff3b5c'}}/>
    <span style={{fontSize:13, color:decided==='APPROVED'?'#00ff7a':'#ff3b5c', fontFamily:'IBM Plex Mono,monospace'}}>{decided}</span>
    {reason && <span style={{fontSize:12, color:'#4a6880'}}>— "{reason}"</span>}
  </Panel>;
  return <Panel elevated style={{padding:'16px 18px'}}>
    <div style={{fontSize:11, color:'#4a6880', marginBottom:8}}>Add reasoning (optional)</div>
    <textarea value={reason} onChange={e=>setReason(e.target.value)} placeholder={`Model recommends: approve · click to override`} style={{width:'100%', height:72, background:'#060c1a', border:'1px solid #152637', color:'#ffffff', fontSize:12, padding:'8px 12px', resize:'none', outline:'none', borderRadius:2, fontFamily:'IBM Plex Sans,sans-serif', marginBottom:12}}/>
    <div style={{display:'flex', gap:8}}>
      <Btn variant="success" icon="check" onClick={()=>{ onDecide(decision.id,'APPROVED',reason); setDecided('APPROVED'); }}>Approve</Btn>
      <Btn variant="danger" icon="x" onClick={()=>{ onDecide(decision.id,'REJECTED',reason); setDecided('REJECTED'); }}>Reject</Btn>
      <Btn variant="secondary" icon="edit-3" size="sm">Edit prompt</Btn>
    </div>
  </Panel>;
};

const ApexWorkflows = () => {
  const [input, setInput] = React.useState('');
  const [running, setRunning] = React.useState(false);
  const [steps, setSteps] = React.useState([]);

  const run = () => {
    if (!input.trim()) return;
    setRunning(true);
    setSteps([]);
    const pipeline = [
      { layer:'L1', label:'analyze', ms:600 },
      { layer:'L2', label:'calibration-gate', ms:900 },
      { layer:'L3', label:'dispatch', ms:700 },
      { layer:'L4', label:'quality-review', ms:500 },
      { layer:'L5', label:'metacognitive', ms:400 },
    ];
    let elapsed = 0;
    pipeline.forEach((p, i) => {
      elapsed += p.ms;
      setTimeout(() => {
        const conf = 0.92 - i*0.06 + Math.random()*0.04;
        setSteps(s => [...s, { ...p, conf, done:true }]);
        if (i === pipeline.length-1) setRunning(false);
      }, elapsed);
    });
  };

  return <div style={{padding:'24px 32px', maxWidth:980}}>
    <div style={{marginBottom:24}}>
      <div style={{fontSize:10, color:PURPLE, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>APEX · Workflow Runner</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>New workflow</h1>
    </div>
    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:20}}>
      <Panel>
        <PanelHeader title="Input" sub="POST /workflow/run"/>
        <div style={{padding:16}}>
          <textarea value={input} onChange={e=>setInput(e.target.value)} placeholder="Describe the task for the agent pipeline…&#10;&#10;e.g. Analyze Q2 revenue by region and flag any accounts at risk of churn." style={{width:'100%', height:120, background:'#091424', border:'1px solid #152637', color:'#ffffff', fontSize:12, padding:'10px 12px', resize:'none', outline:'none', borderRadius:2, fontFamily:'IBM Plex Sans,sans-serif', marginBottom:12}}/>
          <div style={{display:'flex', gap:8, flexWrap:'wrap', marginBottom:12}}>
            {['Analyze Q2 revenue pipeline', 'Summarize this week\'s incidents', 'Draft outreach for at-risk accounts'].map(s => (
              <div key={s} onClick={()=>setInput(s)} style={{fontSize:11, color:PURPLE, border:`1px solid ${PURPLE}30`, padding:'4px 10px', cursor:'pointer'}}>{s}</div>
            ))}
          </div>
          <Btn icon={running?'loader':'play'} variant="primary" tone="apex" onClick={run} disabled={running}>
            {running ? 'Running…' : 'Run workflow'}
          </Btn>
        </div>
      </Panel>
      <Panel>
        <PanelHeader title="Execution trace" sub="5-layer pipeline"/>
        <div style={{padding:'12px 16px'}}>
          {[
            ['L1','analyze','Semantic parse + intent classification'],
            ['L2','calibration-gate','Confidence scoring + tier assignment'],
            ['L3','dispatch','Tool routing + specialist agent call'],
            ['L4','quality-review','Output validation + coherence check'],
            ['L5','metacognitive','Pattern learning + feedback capture'],
          ].map(([layer, label, desc], i) => {
            const step = steps.find(s => s.layer === layer);
            const isActive = running && steps.length === i;
            return <div key={layer} style={{display:'flex', gap:12, marginBottom:0}}>
              <div style={{display:'flex', flexDirection:'column', alignItems:'center', width:20}}>
                <div style={{width:8, height:8, borderRadius:'50%', marginTop:4, flexShrink:0, background: step ? '#00ff7a' : isActive ? PURPLE : '#1e3348', animation:isActive?'pulse 0.8s ease infinite':undefined}}/>
                {i < 4 && <div style={{width:1, flex:1, background:'#0c1a2c', margin:'3px 0'}}/>}
              </div>
              <div style={{paddingBottom:14}}>
                <div style={{display:'flex', gap:8, alignItems:'center', marginBottom:2}}>
                  <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:step?'#00ff7a':isActive?PURPLE:'#4a6880'}}>{layer} · {label}</span>
                  {isActive && <span style={{fontSize:10, color:PURPLE, display:'inline-block', animation:'spin 1s linear infinite'}}>↻</span>}
                  {step && <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>conf: {step.conf.toFixed(2)}</span>}
                </div>
                <div style={{fontSize:10, color:'#4a6880'}}>{desc}</div>
              </div>
            </div>;
          })}
          {steps.length === 5 && <div style={{marginTop:12, padding:'10px 14px', background:`${PURPLE}10`, border:`1px solid ${PURPLE}30`}}>
            <div style={{fontSize:11, color:PURPLE, fontFamily:'IBM Plex Mono,monospace', marginBottom:3}}>Workflow complete</div>
            <div style={{fontSize:12, color:'#a8c4de'}}>Final confidence: {steps[steps.length-1].conf.toFixed(2)} · T{steps[steps.length-1].conf > 0.92 ? '1' : steps[steps.length-1].conf > 0.65 ? '2' : '3'} resolution · trace saved</div>
          </div>}
        </div>
      </Panel>
    </div>
  </div>;
};

Object.assign(window, { ApexOverview, ApexHITL, ApexWorkflows });
