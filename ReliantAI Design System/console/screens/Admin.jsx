// Admin.jsx — settings, team, billing, audit log

const AdminSettings = () => {
  const [tab, setTab] = React.useState('org');
  const keys = [
    { name:'Production API key', key:'rel_live_sk_...a82f', created:'2026-01-15', last:'2m ago' },
    { name:'Webhook signing secret', key:'whsec_...c441', created:'2026-02-01', last:'4h ago' },
  ];
  return <div style={{padding:'24px 32px', maxWidth:960}}>
    <div style={{marginBottom:22}}>
      <div style={{fontSize:10, color:'#a8c4de', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>Admin · Settings</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Organization settings</h1>
    </div>
    <Tabs active={tab} onChange={setTab} tone="#a8c4de" tabs={['org','api-keys','team','integrations','security']}/>
    <div style={{marginTop:24}}>
      {tab==='org' && <div style={{display:'flex', flexDirection:'column', gap:16}}>
        <Panel>
          <PanelHeader title="Organization profile"/>
          <div style={{padding:20, display:'grid', gridTemplateColumns:'1fr 1fr', gap:16}}>
            {[['Organization name','ReliantAI'],['Owner','Lena Yu'],['Email','ops@reliant.ai'],['Location','Houston, TX'],['Plan','Conduit · $3,800/mo'],['Seats','8 / 25 used']].map(([k,v])=>(
              <div key={k}>
                <div style={{fontSize:10, color:'#4a6880', marginBottom:4}}>{k}</div>
                <input defaultValue={v} style={{background:'#091424', border:'1px solid #152637', color:'#ffffff', fontSize:12, padding:'7px 10px', borderRadius:2, outline:'none', width:'100%'}}/>
              </div>
            ))}
          </div>
          <div style={{padding:'0 20px 20px'}}>
            <Btn icon="save" variant="primary">Save changes</Btn>
          </div>
        </Panel>
      </div>}

      {tab==='api-keys' && <Panel>
        <PanelHeader title="API keys" right={<Btn icon="plus" variant="secondary" size="sm">Generate new key</Btn>}/>
        {keys.map(k=>(
          <div key={k.name} style={{padding:'14px 18px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:14}}>
            <i data-lucide="key" style={{width:14, height:14, color:'#4a6880'}}/>
            <div style={{flex:1}}>
              <div style={{fontSize:12, color:'#ffffff'}}>{k.name}</div>
              <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880', marginTop:2}}>{k.key} · created {k.created} · last used {k.last}</div>
            </div>
            <Btn size="xs" variant="secondary" icon="refresh-cw">Rotate</Btn>
            <Btn size="xs" variant="danger" icon="trash-2">Revoke</Btn>
          </div>
        ))}
        <div style={{padding:'14px 18px', fontSize:11, color:'#4a6880'}}>Never store API keys in browser storage. All tokens served server-side only.</div>
      </Panel>}

      {tab==='team' && <Panel>
        <PanelHeader title="Team members" sub="8 active · 25 seat limit" right={<Btn icon="user-plus" variant="secondary" size="sm">Invite</Btn>}/>
        {[
          { name:'Lena Yu',        email:'lena@reliant.ai',   role:'super_admin', active:true,  last:'Now' },
          { name:'Marcus Webb',    email:'marcus@reliant.ai',  role:'admin',       active:true,  last:'1h ago' },
          { name:'Priya Sharma',   email:'priya@reliant.ai',   role:'operator',    active:true,  last:'3h ago' },
          { name:'Jordan Lee',     email:'jordan@reliant.ai',  role:'technician',  active:true,  last:'Yesterday' },
          { name:'Sofia Reyes',    email:'sofia@reliant.ai',   role:'operator',    active:false, last:'Apr 18' },
        ].map(u=>(
          <div key={u.email} style={{padding:'11px 18px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:14}}>
            <div style={{width:28, height:28, borderRadius:'50%', background: u.active?'linear-gradient(135deg,#00e5ff,#7c5cfc)':'#152637', fontSize:10, fontWeight:700, color:'#020510', display:'flex', alignItems:'center', justifyContent:'center'}}>{u.name.split(' ').map(n=>n[0]).join('')}</div>
            <div style={{flex:1}}>
              <div style={{fontSize:12, color:u.active?'#ffffff':'#4a6880'}}>{u.name}</div>
              <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{u.email}</div>
            </div>
            <Badge label={u.role} tone={u.role==='super_admin'?'purple':u.role==='admin'?'cyan':'neutral'} size="xs"/>
            <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', width:80, textAlign:'right'}}>{u.last}</div>
            {!u.active && <Badge label="INACTIVE" tone="neutral" size="xs"/>}
          </div>
        ))}
      </Panel>}

      {tab==='security' && <Panel>
        <PanelHeader title="Security invariants" sub="read-only · enforced at auth service"/>
        {[
          ['No tokens in browser storage','Enforced — all auth tokens served server-side only','check-circle-2'],
          ['Fail-closed auth','If auth service unavailable, all services refuse to start','shield-check'],
          ['No direct service-to-service calls','All cross-system via event bus or Kong gateway','git-branch'],
          ['Document preview sanitization','DOMPurify + text-safe renderer — no raw HTML insertion','eye-off'],
          ['No default credentials','All services require explicit env vars with :?required syntax','lock'],
          ['Life-safety auto-dispatch blocked','Gas/CO/smoke → 911 directive only, never auto-dispatch','alert-octagon'],
          ['No raw UUID KV access','Cross-device sync via signed sessions + short-lived codes only','key'],
        ].map(([k,v,icon])=>(
          <div key={k} style={{padding:'12px 18px', borderBottom:'1px solid #0c1a2c', display:'flex', gap:14, alignItems:'flex-start'}}>
            <i data-lucide={icon} style={{width:16, height:16, color:'#00ff7a', marginTop:1, flexShrink:0}}/>
            <div>
              <div style={{fontSize:12, color:'#ffffff', marginBottom:2}}>{k}</div>
              <div style={{fontSize:11, color:'#4a6880'}}>{v}</div>
            </div>
            <Badge label="ENFORCED" tone="green" size="xs" style={{marginLeft:'auto', flexShrink:0}}/>
          </div>
        ))}
      </Panel>}
    </div>
  </div>;
};

const AdminBilling = () => (
  <div style={{padding:'24px 32px', maxWidth:960}}>
    <div style={{marginBottom:22}}>
      <div style={{fontSize:10, color:'#a8c4de', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>Admin · Billing</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Platform billing</h1>
    </div>
    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, marginBottom:20}}>
      <Panel>
        <PanelHeader title="Active plan" sub="Conduit · renews May 23"/>
        <div style={{padding:20}}>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:28, fontWeight:600, color:'#00e5ff', marginBottom:4}}>$3,800<span style={{fontSize:14, color:'#4a6880'}}>/mo</span></div>
          <div style={{fontSize:12, color:'#4a6880', marginBottom:16}}>Up to 3 products · 25 seats · 50k docs/mo</div>
          {[['ClearDesk docs','12,840 / 50,000',0.257],['Money dispatches','647 / unlimited',0.0],['APEX traces','2,840 / 10,000',0.284],['Seats','8 / 25',0.32]].map(([k,v,pct])=>(
            <div key={k} style={{marginBottom:12}}>
              <div style={{display:'flex', justifyContent:'space-between', fontSize:11, marginBottom:4}}>
                <span style={{color:'#a8c4de'}}>{k}</span>
                <span style={{fontFamily:'IBM Plex Mono,monospace', color:'#ffffff'}}>{v}</span>
              </div>
              {pct>0&&<div style={{height:3, background:'#0c1a2c', borderRadius:1}}><div style={{width:`${pct*100}%`, height:'100%', background:'#00e5ff'}}/></div>}
            </div>
          ))}
        </div>
      </Panel>
      <Panel>
        <PanelHeader title="This month so far"/>
        <div style={{padding:20}}>
          {[['API calls','284,192','$28.42'],['Documents processed','12,840','$6.42'],['Agent traces','2,840','$5.68'],['Storage','4.2 GB','$1.68']].map(([k,v,c])=>(
            <div key={k} style={{display:'flex', alignItems:'center', gap:12, padding:'8px 0', borderBottom:'1px solid #0c1a2c'}}>
              <div style={{flex:1, fontSize:12, color:'#a8c4de'}}>{k}</div>
              <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#4a6880'}}>{v}</div>
              <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:12, color:'#ffffff', width:60, textAlign:'right'}}>{c}</div>
            </div>
          ))}
          <div style={{marginTop:12, display:'flex', justifyContent:'space-between', fontFamily:'IBM Plex Mono,monospace'}}>
            <span style={{fontSize:12, color:'#4a6880'}}>Total this month</span>
            <span style={{fontSize:16, color:'#ffc400', fontWeight:600}}>$42.20</span>
          </div>
        </div>
      </Panel>
    </div>
    <div style={{display:'flex', gap:10}}>
      <Btn icon="zap" variant="primary">Upgrade to Sovereign</Btn>
      <Btn icon="file-text" variant="secondary">Download invoice</Btn>
      <Btn icon="credit-card" variant="secondary">Update payment method</Btn>
    </div>
  </div>
);

const AuditLog = () => {
  const entries = [
    { t:'14:32:07', svc:'cleardesk', user:'lena.yu', action:'document.approved', target:'INV-2026-0413', ip:'192.168.1.10' },
    { t:'14:31:41', svc:'apex',      user:'system',   action:'hitl.escalated',   target:'DEC-9417',      ip:'10.0.0.4' },
    { t:'14:30:59', svc:'money',     user:'lena.yu', action:'dispatch.updated',  target:'DSP-2421',      ip:'192.168.1.10' },
    { t:'14:28:01', svc:'money',     user:'system',   action:'life_safety.triggered', target:'DSP-2419', ip:'10.0.0.3' },
    { t:'14:15:00', svc:'admin',     user:'lena.yu', action:'api_key.rotated',   target:'rel_live_sk…',  ip:'192.168.1.10' },
    { t:'11:02:44', svc:'cleardesk', user:'marcus.webb','action':'batch.exported',target:'12 docs',      ip:'192.168.1.22' },
    { t:'09:00:01', svc:'bap',       user:'system',   action:'pipeline.started', target:'etl-2026-04-23',ip:'10.0.0.5' },
  ];
  return <div style={{padding:'24px 32px', maxWidth:1200}}>
    <div style={{marginBottom:22}}>
      <div style={{fontSize:10, color:'#a8c4de', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>Admin · Audit</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Audit log</h1>
    </div>
    <Panel>
      <PanelHeader title="Cross-service audit trail" sub="immutable · 90-day retention" right={<Btn icon="download" variant="ghost" size="sm">Export</Btn>}/>
      <table style={{width:'100%', borderCollapse:'collapse'}}>
        <thead>
          <tr style={{background:'#091424'}}>
            {['Time','Service','User','Action','Target','IP'].map(h=>(
              <th key={h} style={{padding:'8px 16px', textAlign:'left', fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', borderBottom:'1px solid #152637'}}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {entries.map((e,i)=>(
            <tr key={i} style={{borderBottom:'1px solid #0c1a2c'}} onMouseEnter={el=>el.currentTarget.style.background='#091424'} onMouseLeave={el=>el.currentTarget.style.background='transparent'}>
              <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{e.t}</td>
              <td style={{padding:'9px 16px'}}><Badge label={e.svc} tone={e.svc==='money'?'gold':e.svc==='cleardesk'?'teal':e.svc==='apex'?'purple':'neutral'} size="xs"/></td>
              <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de'}}>{e.user}</td>
              <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:e.action.includes('life_safety')?'#ff3b5c':'#00e5ff'}}>{e.action}</td>
              <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#4a6880'}}>{e.target}</td>
              <td style={{padding:'9px 16px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#1e3348'}}>{e.ip}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  </div>;
};

Object.assign(window, { AdminSettings, AdminBilling, AuditLog });
