// Money.jsx — HVAC AI dispatch workspace
const GOLD = '#ffc400';

const MoneyAdmin = () => {
  const [sel, setSel] = React.useState(null);
  const [tab, setTab] = React.useState('active');
  const [tick, setTick] = React.useState(0);
  const hasLS = DISPATCHES.some(d => d.lifeSafety);

  React.useEffect(() => {
    const t = setInterval(() => setTick(n => n+1), 5000);
    return () => clearInterval(t);
  }, []);

  const filtered = tab === 'active'
    ? DISPATCHES.filter(d => d.status !== 'scheduled' || d.urgencyScore > 0.5)
    : tab === 'completed' ? [] : DISPATCHES;

  const stats = [
    { label:'Active', value:DISPATCHES.filter(d=>!['completed'].includes(d.status)).length, color:'#ffffff' },
    { label:'Life-safety', value:DISPATCHES.filter(d=>d.lifeSafety).length, color:'#ff3b5c' },
    { label:'Revenue today', value:DISPATCHES.reduce((a,d)=>a+d.revenue,0), color:GOLD, prefix:'$', unit:'',   decimals:0 },
    { label:'Avg confidence', value:0.94, color:'#00ff7a', decimals:2 },
    { label:'Updated', value:`${tick*5}s`, color:'#4a6880', noCountUp:true },
  ];

  const priorityTone = { 'P0-LIFE':'life', P1:'red', P2:'gold', P3:'neutral', P4:'neutral' };
  const statusColor = { 'life-safety':'#ff3b5c', 'dispatched':'#ff8c00', 'en-route':GOLD, 'on-site':'#00ff7a', 'scheduled':'#4a6880', 'completed':'#4a6880' };

  return <div style={{display:'flex', flexDirection:'column', height:'calc(100vh - 44px)'}}>
    {/* LIFE-SAFETY banner */}
    {hasLS && <div style={{
      padding:'11px 24px', background:'rgba(255,59,92,0.1)', borderBottom:'1px solid #ff3b5c',
      display:'flex', alignItems:'center', gap:12, animation:'pulse 1.4s ease infinite', flexShrink:0,
    }}>
      <i data-lucide="alert-octagon" style={{width:16, height:16, color:'#ff3b5c'}}/>
      <div style={{fontSize:12, fontWeight:700, color:'#ff3b5c', letterSpacing:'0.05em'}}>LIFE-SAFETY · GAS ODOR REPORTED · 911 DIRECTIVE ISSUED — NO TECHNICIAN DISPATCHED</div>
      <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#ff3b5c'}}>DSP-2419 · {fmtAgo(DISPATCHES[1].createdAt)} ago</div>
      <div style={{flex:1}}/>
      <Btn size="sm" variant="danger" icon="phone">Call owner</Btn>
    </div>}

    {/* Stats strip */}
    <Panel style={{borderRadius:0, border:'none', borderBottom:'1px solid #0c1a2c', flexShrink:0}}>
      <div style={{display:'flex'}}>
        {stats.map(s => (
          <div key={s.label} style={{flex:1, padding:'14px 20px', borderRight:'1px solid #0c1a2c'}}>
            <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:5}}>{s.label}</div>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:22, fontWeight:600, color:s.color}}>
              {s.noCountUp ? s.value : <>{s.prefix||''}<CountUp to={typeof s.value==='number'?s.value:0} decimals={s.decimals||0}/>{s.unit||''}</>}
            </div>
          </div>
        ))}
        <div style={{flex:1, padding:'14px 20px'}}>
          <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:5}}>Houston weather</div>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:16, fontWeight:600, color:'#ff3b5c'}}>96°F <span style={{fontSize:11, color:'#4a6880'}}>· demand surge</span></div>
        </div>
      </div>
    </Panel>

    {/* Toolbar */}
    <div style={{padding:'10px 24px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:12, flexShrink:0}}>
      <Tabs active={tab} onChange={setTab} tone={GOLD} tabs={[
        {id:'active', label:'Active', count:DISPATCHES.length},
        {id:'completed', label:'Completed today', count:44},
        {id:'all', label:'All', count:DISPATCHES.length},
      ]}/>
      <div style={{flex:1}}/>
      <Input icon="search" placeholder="DSP-…, customer, tech" size="sm" style={{width:240}}/>
      <Btn icon="filter" variant="secondary" size="sm">Priority</Btn>
      <Btn icon="refresh-cw" variant="secondary" size="sm">Refresh</Btn>
    </div>

    {/* Table */}
    <div style={{flex:1, overflowY:'auto'}}>
      <table style={{width:'100%', borderCollapse:'collapse'}}>
        <thead>
          <tr style={{background:'#091424', position:'sticky', top:0, zIndex:1}}>
            {['ID','Customer','Issue','Priority','Tech','ETA','Status','Revenue','Age'].map(h => (
              <th key={h} style={{padding:'9px 16px', textAlign:'left', fontSize:9, fontWeight:500, color:'#4a6880', letterSpacing:'0.08em', textTransform:'uppercase', borderBottom:'1px solid #152637', whiteSpace:'nowrap'}}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.map((d, i) => (
            <tr key={d.id} onClick={()=>setSel(d)} style={{borderBottom:'1px solid #0c1a2c', cursor:'pointer', animation:`slide-up ${200+i*40}ms ease-out both`}}
              onMouseEnter={e=>e.currentTarget.style.background='#091424'}
              onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
              <td style={{padding:'10px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:GOLD}}>{d.id}</td>
              <td style={{padding:'10px 16px'}}>
                <div style={{fontSize:12, color:'#ffffff'}}>{d.lead}</div>
                <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{d.phone}</div>
              </td>
              <td style={{padding:'10px 16px', fontSize:11, color:'#a8c4de', maxWidth:220}}>
                <div style={{overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{d.issue}</div>
              </td>
              <td style={{padding:'10px 16px'}}><Badge label={d.priority} tone={priorityTone[d.priority]||'neutral'} size="xs" pulse={d.lifeSafety}/></td>
              <td style={{padding:'10px 16px', fontSize:11, color:'#a8c4de'}}>{d.tech}</td>
              <td style={{padding:'10px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de'}}>{d.eta}</td>
              <td style={{padding:'10px 16px'}}>
                <div style={{display:'flex', alignItems:'center', gap:6}}>
                  <div style={{width:6, height:6, borderRadius:'50%', background:statusColor[d.status]||'#4a6880'}}/>
                  <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:statusColor[d.status]||'#4a6880', textTransform:'uppercase'}}>{d.status}</span>
                </div>
              </td>
              <td style={{padding:'10px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color: d.revenue>1000?GOLD:'#a8c4de'}}>{d.revenue>0?`$${d.revenue.toLocaleString()}`:'—'}</td>
              <td style={{padding:'10px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{fmtAgo(d.createdAt)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

    {sel && <DispatchModal d={sel} onClose={()=>setSel(null)}/>}
  </div>;
};

const DispatchModal = ({ d, onClose }) => {
  const [tab, setTab] = React.useState('detail');
  const AGENTS = [
    { id:'triage_agent',    label:'Triage',    done:true,  tool:'triage_urgency',           out:`urgency=${d.priority} · life_safety=${!!d.lifeSafety}` },
    { id:'intake_agent',    label:'Intake',    done:true,  tool:'capture_lead_details',      out:`lead=${d.lead} · phone=${d.phone}` },
    { id:'scheduler_agent', label:'Scheduler', done:d.status!=='life-safety', running:d.status==='on-site'||d.status==='en-route', tool:'check_tech_availability', out: d.lifeSafety ? '911 directive → skip dispatch' : `tech=${d.tech} · eta=${d.eta}` },
    { id:'dispatch_agent',  label:'Dispatch',  done:['on-site','dispatched','en-route'].includes(d.status), tool:'dispatch_to_tech', out: d.lifeSafety ? '— (skipped)' : `sms_sent=true · eta_confirmed=true` },
    { id:'followup_agent',  label:'Follow-up', done:d.status==='completed', tool:'send_customer_update', out: d.status==='completed'?'survey=sent · rating=4.9':'pending on-site confirmation' },
  ];
  const smsThread = [
    { dir:'in',  t:fmtTime(d.createdAt), body: d.issue },
    { dir:'out', t:fmtTime(new Date(d.createdAt.getTime()+12000)), body: d.lifeSafety ? 'URGENT: For gas odors, please leave the building immediately and call 911. Do NOT turn any switches on or off. We\'ve notified emergency services.' : `Hi ${d.lead.split(' ')[0]}, we\'ve received your request and are dispatching a technician. You\'ll get a confirmation with ETA shortly.` },
    ...(!d.lifeSafety ? [
      { dir:'in',  t:fmtTime(new Date(d.createdAt.getTime()+90000)),  body:'Thank you! How long until they arrive?' },
      { dir:'out', t:fmtTime(new Date(d.createdAt.getTime()+105000)), body:`${d.tech} is heading your way and should arrive by ${d.eta}. We'll send a link to track their location.` },
    ] : []),
  ];
  return <div style={{position:'fixed', inset:0, background:'rgba(2,5,16,0.75)', zIndex:50, display:'flex', justifyContent:'flex-end'}} onClick={onClose}>
    <div onClick={e=>e.stopPropagation()} style={{width:'min(780px,90vw)', background:'#060c1a', borderLeft:'1px solid #152637', height:'100vh', overflow:'hidden', display:'flex', flexDirection:'column', animation:'slide-left 260ms ease-out'}}>
      <div style={{padding:'16px 22px', borderBottom:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexShrink:0}}>
        <div>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880', marginBottom:4}}>{d.id} · {fmtAgo(d.createdAt)} ago</div>
          <div style={{fontSize:16, fontWeight:600, color:'#ffffff', marginBottom:6}}>{d.lead} <span style={{fontSize:13, color:'#4a6880', fontWeight:400}}>· {d.phone}</span></div>
          <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
            <Badge label={d.priority} tone={d.lifeSafety?'life':d.priority==='P1'?'red':d.priority==='P2'?'gold':'neutral'} pulse={d.lifeSafety}/>
            <Badge label={d.status.toUpperCase()} tone={d.status==='life-safety'?'life':d.status==='on-site'?'green':'neutral'}/>
            <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>conf: {d.confidence}</span>
          </div>
        </div>
        <i data-lucide="x" onClick={onClose} style={{width:16, height:16, color:'#4a6880', cursor:'pointer'}}/>
      </div>
      <Tabs active={tab} onChange={setTab} tone={GOLD} tabs={['detail','sms','agents']}/>
      <div style={{flex:1, overflowY:'auto', padding:'18px 22px'}}>
        {tab==='detail' && <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'12px 24px'}}>
          {[['Issue',d.issue,true],['Address',d.source],[`Tech`,d.tech],[`ETA`,d.eta],[`Revenue`,d.revenue>0?`$${d.revenue}`:'—'],[`Urgency score`,d.urgencyScore.toFixed(2)]].map(([k,v,full]) => (
            <div key={k} style={{gridColumn:full?'1/-1':'auto'}}>
              <div style={{fontSize:10, color:'#4a6880', marginBottom:3, fontFamily:'IBM Plex Mono,monospace'}}>{k}</div>
              <div style={{fontSize:12, color:'#a8c4de'}}>{v}</div>
            </div>
          ))}
          {d.lifeSafety && <div style={{gridColumn:'1/-1', padding:'12px 16px', background:'rgba(255,59,92,0.08)', border:'1px solid #ff3b5c', borderLeft:'3px solid #ff3b5c', marginTop:8}}>
            <div style={{fontSize:12, fontWeight:700, color:'#ff3b5c', marginBottom:4}}>LIFE-SAFETY PROTOCOL ACTIVATED</div>
            <div style={{fontSize:12, color:'#a8c4de'}}>Keywords detected: {d.keywords?.join(', ')}. Customer directed to evacuate. 911 called. Owner notified. No technician dispatched per policy §3.1.</div>
          </div>}
        </div>}
        {tab==='sms' && <div style={{display:'flex', flexDirection:'column', gap:10}}>
          {smsThread.map((m,i) => (
            <div key={i} style={{display:'flex', flexDirection:'column', alignItems:m.dir==='out'?'flex-end':'flex-start'}}>
              <div style={{maxWidth:'76%', padding:'10px 14px', background:m.dir==='out'?'rgba(255,196,0,0.08)':'#091424', border:`1px solid ${m.dir==='out'?'rgba(255,196,0,0.2)':'#152637'}`, fontSize:12, color:'#a8c4de', lineHeight:1.5}}>{m.body}</div>
              <div style={{fontSize:9, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', margin:'3px 4px'}}>{m.t} · {m.dir==='out'?'outbound':'inbound'} SMS</div>
            </div>
          ))}
        </div>}
        {tab==='agents' && <div>
          <div style={{fontSize:10, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:14, fontFamily:'IBM Plex Mono,monospace'}}>CrewAI pipeline · {AGENTS.filter(a=>a.done).length}/{AGENTS.length} complete</div>
          {AGENTS.map((a, i) => (
            <div key={a.id} style={{display:'flex', gap:12, marginBottom: i<AGENTS.length-1?0:0}}>
              <div style={{display:'flex', flexDirection:'column', alignItems:'center', width:20}}>
                <div style={{width:8, height:8, borderRadius:'50%', background: a.done?'#00ff7a':a.running?GOLD:'#1e3348', marginTop:4, flexShrink:0, boxShadow:a.running?`0 0 8px ${GOLD}80`:undefined}}/>
                {i<AGENTS.length-1 && <div style={{width:1, flex:1, background:'#0c1a2c', margin:'3px 0'}}/>}
              </div>
              <div style={{paddingBottom:16}}>
                <div style={{display:'flex', gap:8, alignItems:'center', marginBottom:2}}>
                  <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:12, fontWeight:500, color:a.done?'#00ff7a':a.running?GOLD:'#4a6880'}}>{a.id}</span>
                  {a.running && <span style={{fontSize:10, color:GOLD, display:'inline-block', animation:'spin 1s linear infinite'}}>↻</span>}
                  <span style={{fontSize:9, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{a.tool}</span>
                </div>
                <div style={{fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{a.out}</div>
              </div>
            </div>
          ))}
        </div>}
      </div>
      <div style={{padding:'12px 22px', borderTop:'1px solid #0c1a2c', display:'flex', gap:8, flexShrink:0}}>
        <Btn icon="message-circle" variant="secondary" size="sm">Resend SMS</Btn>
        <Btn icon="edit-3" variant="secondary" size="sm">Update status</Btn>
        <Btn icon="phone-call" variant="secondary" size="sm">Call tech</Btn>
        <div style={{flex:1}}/>
        {d.lifeSafety && <Btn icon="alert-octagon" variant="danger">Incident report</Btn>}
      </div>
    </div>
  </div>;
};

const MoneyBilling = () => {
  const plans = [
    { name:'Starter', price:299, dispatches:200, seats:3, current:false },
    { name:'Growth', price:799, dispatches:1000, seats:10, current:true },
    { name:'Enterprise', price:2499, dispatches:'unlimited', seats:'unlimited', current:false },
  ];
  return <div style={{padding:'24px 32px', maxWidth:1100}}>
    <div style={{marginBottom:24}}>
      <div style={{fontSize:10, color:GOLD, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>Money · Billing</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Subscription & usage</h1>
    </div>
    <div style={{display:'grid', gridTemplateColumns:'1.4fr 1fr', gap:20}}>
      <div style={{display:'flex', flexDirection:'column', gap:16}}>
        <Panel>
          <PanelHeader title="Current plan" sub="Billing period ends May 23, 2026"/>
          <div style={{padding:'20px 20px 16px'}}>
            <div style={{display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:20}}>
              <div>
                <div style={{fontSize:24, fontWeight:700, color:GOLD, fontFamily:'IBM Plex Mono,monospace'}}>Growth</div>
                <div style={{fontSize:13, color:'#a8c4de', marginTop:2}}>$799/month · 1,000 dispatches · 10 seats</div>
              </div>
              <Badge label="ACTIVE" tone="green"/>
            </div>
            <div style={{marginBottom:16}}>
              <div style={{display:'flex', justifyContent:'space-between', fontSize:11, marginBottom:4}}>
                <span style={{color:'#4a6880'}}>Dispatches used</span>
                <span style={{fontFamily:'IBM Plex Mono,monospace', color:'#ffffff'}}>647 / 1,000</span>
              </div>
              <div style={{height:4, background:'#0c1a2c', borderRadius:1}}>
                <div style={{width:'64.7%', height:'100%', background:GOLD}}/>
              </div>
              <div style={{fontSize:10, color:'#4a6880', marginTop:3, fontFamily:'IBM Plex Mono,monospace'}}>353 remaining · resets May 23</div>
            </div>
            <div style={{display:'flex', gap:8}}>
              <Btn icon="zap" variant="primary" tone="money">Upgrade to Enterprise</Btn>
              <Btn icon="x" variant="ghost" size="sm">Cancel subscription</Btn>
            </div>
          </div>
        </Panel>
        <Panel>
          <PanelHeader title="Invoice history" right={<Btn icon="download" variant="ghost" size="sm">Download all</Btn>}/>
          {[['Apr 23, 2026','$799.00','paid'],['Mar 23, 2026','$799.00','paid'],['Feb 23, 2026','$799.00','paid'],['Jan 23, 2026','$499.00','paid']].map(([d,a,s]) => (
            <div key={d} style={{padding:'10px 16px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:14}}>
              <i data-lucide="file-text" style={{width:13, height:13, color:'#4a6880'}}/>
              <span style={{fontSize:12, color:'#a8c4de', flex:1}}>{d}</span>
              <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:12, color:'#ffffff'}}>{a}</span>
              <Badge label={s.toUpperCase()} tone="green" size="xs"/>
              <i data-lucide="download" style={{width:12, height:12, color:'#4a6880', cursor:'pointer'}}/>
            </div>
          ))}
        </Panel>
      </div>
      <Panel>
        <PanelHeader title="Plan comparison"/>
        <div style={{padding:'16px 16px 0'}}>
          {plans.map(p => (
            <div key={p.name} style={{padding:'16px 14px', marginBottom:8, border:`1px solid ${p.current?GOLD+'60':'#0c1a2c'}`, background:p.current?'rgba(255,196,0,0.04)':'transparent'}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:10}}>
                <div>
                  <div style={{fontSize:14, fontWeight:600, color:p.current?GOLD:'#ffffff'}}>{p.name}</div>
                  <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:20, fontWeight:600, color:'#ffffff', marginTop:2}}>${p.price}<span style={{fontSize:11, color:'#4a6880'}}>/mo</span></div>
                </div>
                {p.current && <Badge label="CURRENT" tone="gold" size="xs"/>}
              </div>
              <div style={{fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', display:'flex', gap:14}}>
                <span>{p.dispatches} dispatches</span><span>{p.seats} seats</span>
              </div>
              {!p.current && <Btn size="sm" variant="secondary" style={{marginTop:10}}>Switch to {p.name}</Btn>}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  </div>;
};

Object.assign(window, { MoneyAdmin, MoneyBilling });
