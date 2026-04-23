// Marketing.jsx — homepage + service pages (fullscreen, no chrome)

const MarketingHome = () => {
  const [scrollY, setScrollY] = React.useState(0);
  const ref = React.useRef(null);

  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const h = () => setScrollY(el.scrollTop);
    el.addEventListener('scroll', h, { passive:true });
    return () => el.removeEventListener('scroll', h);
  }, []);

  const kenBurnsScale = 1 + scrollY * 0.0003;
  const heroOpacity = Math.max(0, 1 - scrollY / 500);

  return <div ref={ref} style={{height:'100vh', overflowY:'auto', background:'#020510', scrollBehavior:'smooth'}}>
    {/* Nav */}
    <nav style={{position:'fixed', top:0, left:0, right:0, zIndex:50, padding:'0 48px', height:60, display:'flex', alignItems:'center', gap:32, background: scrollY>80?'rgba(2,5,16,0.95)':' transparent', backdropFilter:scrollY>80?'blur(12px)':undefined, borderBottom:scrollY>80?'1px solid #0c1a2c':'none', transition:'all 300ms'}}>
      <Logo size={20} wordSize={15}/>
      <div style={{flex:1}}/>
      {['Products','Pricing','Docs','Company'].map(l=>(
        <div key={l} style={{fontSize:13, color:'#a8c4de', cursor:'pointer', transition:'color 150ms'}} onMouseEnter={e=>e.target.style.color='#ffffff'} onMouseLeave={e=>e.target.style.color='#a8c4de'}>{l}</div>
      ))}
      <Btn icon="arrow-right" variant="primary" onClick={()=>window.go('/auth/signin')}>Get access</Btn>
    </nav>

    {/* Hero — Ken Burns + full viewport */}
    <div style={{height:'100vh', position:'relative', overflow:'hidden', display:'flex', alignItems:'center', justifyContent:'center'}}>
      <div style={{position:'absolute', inset:0, background:`url('/assets/breath-bg.jpg') center/cover no-repeat`, transform:`scale(${kenBurnsScale})`, transformOrigin:'center center', transition:'transform 100ms linear', filter:'brightness(0.25) saturate(0.8)'}}/>
      <div style={{position:'absolute', inset:0, background:'linear-gradient(to bottom, transparent 40%, #020510 100%)'}}/>
      <div style={{position:'relative', textAlign:'center', maxWidth:860, padding:'0 32px', opacity:heroOpacity, transform:`translateY(${scrollY*0.15}px)`}}>
        <div style={{display:'inline-flex', alignItems:'center', gap:8, padding:'5px 14px', border:'1px solid rgba(0,229,255,0.2)', background:'rgba(0,229,255,0.05)', borderRadius:2, marginBottom:32, fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#00e5ff', letterSpacing:'0.1em'}}>
          <div style={{width:5, height:5, borderRadius:'50%', background:'#00ff7a', animation:'pulse 1.6s ease infinite'}}/>
          DIGITAL OPERATIONS SUITE · NOW IN PRIVATE ACCESS
        </div>
        <h1 style={{fontFamily:"'Neue Haas Grotesk','Inter Tight',sans-serif", fontSize:80, fontWeight:700, color:'#ffffff', letterSpacing:'-0.04em', lineHeight:0.95, marginBottom:28}}>
          Leads contacted<br/>in <span style={{color:'#00e5ff'}}>seconds</span>.<br/>Not hours.
        </h1>
        <p style={{fontSize:18, color:'#a8c4de', lineHeight:1.6, maxWidth:580, margin:'0 auto 40px'}}>
          HBR research: leads contacted within 60 minutes are <strong style={{color:'#ffffff'}}>7× more likely to qualify</strong>. The industry average response time is 24–48 hours. Ours is seconds.
        </p>
        <div style={{display:'flex', gap:12, justifyContent:'center'}}>
          <Btn size="lg" variant="primary" icon="arrow-right" onClick={()=>window.go('/auth/signin')}>Request access</Btn>
          <Btn size="lg" variant="secondary" icon="play">Watch demo</Btn>
        </div>
      </div>
      <div style={{position:'absolute', bottom:32, left:'50%', transform:'translateX(-50%)', display:'flex', flexDirection:'column', alignItems:'center', gap:8, opacity:heroOpacity}}>
        <span style={{fontSize:10, color:'#4a6880', letterSpacing:'0.1em', fontFamily:'IBM Plex Mono,monospace'}}>SCROLL</span>
        <div style={{width:1, height:40, background:'linear-gradient(to bottom, #4a6880, transparent)'}}/>
      </div>
    </div>

    {/* 7× stat — breath section */}
    <div style={{minHeight:'60vh', display:'flex', alignItems:'center', justifyContent:'center', padding:'80px 48px', background:'#020510', position:'relative', overflow:'hidden'}}>
      <div style={{position:'absolute', inset:0, background:`url('/assets/breath-bg.jpg') center/cover no-repeat`, opacity:0.06, filter:'blur(4px)'}}/>
      <div style={{position:'relative', textAlign:'center', maxWidth:1000}}>
        <div style={{display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:2, background:'#0c1a2c', marginBottom:60}}>
          {[['7×','more likely to qualify','HBR research'],['< 30s','response time','industry avg: 24–48h'],['100%','uptime SLA','Sovereign plan']].map(([v,l,s])=>(
            <div key={l} style={{background:'#020510', padding:'40px 32px'}}>
              <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:56, fontWeight:700, color:'#00e5ff', lineHeight:1, marginBottom:10}}>{v}</div>
              <div style={{fontSize:16, color:'#ffffff', marginBottom:6}}>{l}</div>
              <div style={{fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{s}</div>
            </div>
          ))}
        </div>
        <p style={{fontSize:17, color:'#a8c4de', maxWidth:680, margin:'0 auto', lineHeight:1.7}}>
          Four AI-native services. One integration layer. A single operations console that shows you exactly what's happening across ClearDesk, Money, APEX, and B-A-P — in real time.
        </p>
      </div>
    </div>

    {/* Services zigzag */}
    <div style={{padding:'80px 48px', maxWidth:1200, margin:'0 auto'}}>
      {[
        { name:'ClearDesk', accent:'#00FF94', icon:'file-text', path:'/cleardesk/landing', tag:'AP automation', desc:'Parse invoices in seconds. Confidence scoring, dual-language summaries, escalation rules, and text-safe document preview — all without storing a single auth token in the browser.', metrics:[['284','docs/day'],['0.94','avg confidence'],['4.3s','parse time']] },
        { name:'Money', accent:'#ffc400', icon:'radio', path:'/money/admin', tag:'HVAC dispatch', desc:'AI-powered lead intake and dispatch, built for HVAC operators. A CrewAI pipeline handles triage → intake → scheduling → dispatch → follow-up. Gas/CO keywords always escalate to 911 — never to a technician.', metrics:[['< 30s','first response'],['7×','qualification rate'],['96%','lead-to-dispatch'] ] },
        { name:'APEX', accent:'#7c5cfc', icon:'cpu', path:'/apex/overview', tag:'Agent orchestration', desc:'5-layer probabilistic execution engine. Every workflow is assigned a confidence tier — Reflexive, Deliberative, Contested, or Unknown — and routed accordingly. Humans stay in every loop that matters.', metrics:[['T1–T4','execution tiers'],['5 layers','per workflow'],['HITL','always available']] },
        { name:'B-A-P', accent:'#00d4aa', icon:'bar-chart-3', path:'/bap/analytics', tag:'Data pipelines', desc:'ETL, AI insights, forecasting, and anomaly detection — built on FastAPI + Celery + Redis. Uploads trigger automated pipeline runs. Outputs feed directly into APEX agent context.', metrics:[['156','datasets',''],['4.3s','avg pipeline'],['89','AI insights/day']] },
      ].map((s,i)=>(
        <div key={s.name} style={{display:'grid', gridTemplateColumns: i%2===0?'1fr 1fr':'1fr 1fr', gap:0, marginBottom:2, background:'#0c1a2c'}}>
          <div style={{order:i%2===0?0:1, background:'#060c1a', padding:'56px 48px', borderTop:`2px solid ${s.accent}`}}>
            <div style={{display:'flex', alignItems:'center', gap:10, marginBottom:20}}>
              <div style={{width:32, height:32, background:`${s.accent}15`, border:`1px solid ${s.accent}30`, display:'flex', alignItems:'center', justifyContent:'center'}}>
                <i data-lucide={s.icon} style={{width:16, height:16, color:s.accent}}/>
              </div>
              <div>
                <div style={{fontSize:18, fontWeight:700, color:'#ffffff'}}>{s.name}</div>
                <div style={{fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{s.tag}</div>
              </div>
            </div>
            <p style={{fontSize:14, color:'#a8c4de', lineHeight:1.75, marginBottom:28}}>{s.desc}</p>
            <div style={{display:'flex', gap:24, marginBottom:28}}>
              {s.metrics.map(([v,l])=>(
                <div key={l}>
                  <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:20, fontWeight:600, color:s.accent}}>{v}</div>
                  <div style={{fontSize:11, color:'#4a6880'}}>{l}</div>
                </div>
              ))}
            </div>
            <Btn icon="arrow-right" variant="secondary" onClick={()=>window.go(s.path)}>Open {s.name}</Btn>
          </div>
          <div style={{order:i%2===0?1:0, background:'#020510', display:'flex', alignItems:'center', justifyContent:'center', minHeight:300, padding:40}}>
            <div style={{width:'100%', maxWidth:400, background:'#060c1a', border:'1px solid #0c1a2c', padding:24}}>
              <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:12, fontFamily:'IBM Plex Mono,monospace'}}>Live preview</div>
              {i===0 && <div>
                {['INV-2026-0441 · 0.97 · ready','INV-2026-0419 · 0.55 · escalated','INV-2026-0413 · 0.93 · ready'].map(l=>(
                  <div key={l} style={{padding:'8px 0', borderBottom:'1px solid #0c1a2c', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de'}}>{l}</div>
                ))}
              </div>}
              {i===1 && <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de', lineHeight:2}}>
                <div style={{color:'#ff3b5c'}}>LIFE-SAFETY · 911 directed</div>
                <div>DSP-2418 · dispatched · 8m ETA</div>
                <div>DSP-2421 · en-route · 22m ETA</div>
                <div style={{color:'#00ff7a'}}>3 completed today · $3,540</div>
              </div>}
              {i===2 && <div>
                {[{l:'T1 Reflexive',c:'0.94',tone:'#00e5ff'},{l:'T2 Deliberative',c:'0.78',tone:'#ffc400'},{l:'T3 Contested',c:'0.61',tone:'#ff3b5c'}].map(t=>(
                  <div key={t.l} style={{padding:'7px 0', borderBottom:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', fontFamily:'IBM Plex Mono,monospace', fontSize:11}}>
                    <span style={{color:t.tone}}>{t.l}</span><span style={{color:'#a8c4de'}}>conf: {t.c}</span>
                  </div>
                ))}
              </div>}
              {i===3 && <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de', lineHeight:1.8}}>
                <div style={{color:'#00d4aa'}}>Upload → Validate ✓</div>
                <div style={{color:'#00e5ff'}}>Transform → running ↻</div>
                <div style={{color:'#4a6880'}}>Load → pending</div>
                <div style={{color:'#4a6880'}}>Insights → pending</div>
              </div>}
            </div>
          </div>
        </div>
      ))}
    </div>

    {/* Integration logos */}
    <div style={{padding:'60px 48px', borderTop:'1px solid #0c1a2c', borderBottom:'1px solid #0c1a2c', background:'#060c1a'}}>
      <div style={{textAlign:'center', marginBottom:32}}>
        <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.14em', textTransform:'uppercase', fontFamily:'IBM Plex Mono,monospace'}}>Integrated with</div>
      </div>
      <div style={{display:'flex', gap:32, justifyContent:'center', flexWrap:'wrap', alignItems:'center'}}>
        {['Twilio','Anthropic','Google Gemini','Stripe','Composio','Cloudflare','Vercel','HubSpot','Notion'].map(n=>(
          <div key={n} style={{fontSize:14, fontWeight:500, color:'#4a6880', letterSpacing:'0.01em', padding:'8px 16px', border:'1px solid #0c1a2c', borderRadius:2}}>{n}</div>
        ))}
      </div>
    </div>

    {/* CTA */}
    <div style={{padding:'100px 48px', textAlign:'center'}}>
      <h2 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:52, fontWeight:700, color:'#ffffff', letterSpacing:'-0.03em', marginBottom:16}}>Ready to respond in seconds?</h2>
      <p style={{fontSize:15, color:'#4a6880', marginBottom:36}}>Private access. No credit card. SOC 2 Type II in review.</p>
      <div style={{display:'flex', gap:12, justifyContent:'center'}}>
        <Btn size="lg" variant="primary" icon="arrow-right" onClick={()=>window.go('/auth/signin')}>Request access</Btn>
        <Btn size="lg" variant="secondary" onClick={()=>window.go('/marketing/pricing')}>View pricing →</Btn>
      </div>
    </div>

    {/* Footer */}
    <div style={{padding:'32px 48px', borderTop:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'center', fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
      <Logo size={16} wordSize={13}/>
      <span>© 2026 ReliantAI · All rights reserved</span>
      <span>Houston, TX · ops@reliant.ai</span>
    </div>
  </div>;
};

const MarketingPricing = () => (
  <div style={{minHeight:'100vh', background:'#020510', padding:'80px 48px'}}>
    <nav style={{position:'fixed', top:0, left:0, right:0, zIndex:50, padding:'0 48px', height:60, display:'flex', alignItems:'center', background:'rgba(2,5,16,0.95)', backdropFilter:'blur(12px)', borderBottom:'1px solid #0c1a2c'}}>
      <div onClick={()=>window.go('/marketing/home')} style={{cursor:'pointer'}}><Logo size={20} wordSize={15}/></div>
      <div style={{flex:1}}/>
      <Btn variant="secondary" size="sm" onClick={()=>window.go('/marketing/home')}>← Home</Btn>
    </nav>
    <div style={{maxWidth:1100, margin:'60px auto 0', textAlign:'center', paddingTop:40}}>
      <div style={{fontSize:10, color:'#00e5ff', letterSpacing:'0.14em', textTransform:'uppercase', marginBottom:12, fontFamily:'IBM Plex Mono,monospace'}}>Pricing</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:52, fontWeight:700, color:'#ffffff', letterSpacing:'-0.03em', marginBottom:14}}>Pay for what you use.</h1>
      <p style={{fontSize:15, color:'#4a6880', marginBottom:56}}>Per-service or suite pricing. Usage-based and seat-based models. No surprise bills.</p>
      <div style={{display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:2, background:'#0c1a2c'}}>
        {PLANS.map(p=>(
          <div key={p.id} style={{background:'#060c1a', padding:'40px 32px', borderTop:`2px solid ${p.best?'#00e5ff':'#0c1a2c'}`, position:'relative'}}>
            {p.best && <div style={{position:'absolute', top:-1, left:'50%', transform:'translateX(-50%)', background:'#00e5ff', color:'#020510', fontSize:9, fontWeight:700, padding:'3px 12px', letterSpacing:'0.1em'}}>MOST POPULAR</div>}
            <div style={{fontSize:20, fontWeight:700, color:'#ffffff', marginBottom:4}}>{p.name}</div>
            <div style={{fontSize:12, color:'#4a6880', marginBottom:20}}>{p.tagline}</div>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:40, fontWeight:700, color:p.best?'#00e5ff':'#ffffff', marginBottom:6}}>${p.price.toLocaleString()}<span style={{fontSize:14, color:'#4a6880'}}>/mo</span></div>
            <div style={{fontSize:12, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', marginBottom:28}}>{typeof p.seats==='number'?`${p.seats} seats`:'unlimited seats'}</div>
            <div style={{display:'flex', flexDirection:'column', gap:10, marginBottom:28, textAlign:'left'}}>
              {p.features.map(f=>(
                <div key={f} style={{display:'flex', gap:10, alignItems:'flex-start'}}>
                  <i data-lucide="check" style={{width:13, height:13, color:p.best?'#00e5ff':'#00ff7a', flexShrink:0, marginTop:1}}/>
                  <span style={{fontSize:12, color:'#a8c4de'}}>{f}</span>
                </div>
              ))}
            </div>
            <Btn variant={p.best?'primary':'secondary'} style={{width:'100%', justifyContent:'center'}} onClick={()=>window.go('/auth/signin')}>Get started</Btn>
          </div>
        ))}
      </div>
      <div style={{marginTop:48, fontSize:12, color:'#4a6880', lineHeight:1.8}}>
        All plans include the integration layer (auth, event bus, API gateway, saga orchestration).<br/>Enterprise plans include SOC 2 audit reports, BAA for HIPAA, and custom DPA.
      </div>
    </div>
  </div>
);

Object.assign(window, { MarketingHome, MarketingPricing });
