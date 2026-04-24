// IntegrationExtra.jsx — Saga viewer + Auth session manager

const IntegrationSagas = () => {
  const [selected, setSel] = React.useState(null);
  const sagas = [
    { id:'sg-0044', name:'hvac-dispatch-flow', status:'RUNNING',      steps:4, current:2, service:'money',     started:mins(2),  compensation:false,
      stepList:[{n:'reserve_slot',s:'done'},{n:'dispatch_tech',s:'running'},{n:'notify_customer',s:'pending'},{n:'update_crm',s:'pending'}] },
    { id:'sg-0043', name:'invoice-approval-saga', status:'COMPLETED',  steps:3, current:3, service:'cleardesk', started:mins(14), compensation:false,
      stepList:[{n:'validate_invoice',s:'done'},{n:'approve_payment',s:'done'},{n:'update_ledger',s:'done'}] },
    { id:'sg-0042', name:'onboarding-flow',     status:'COMPENSATING', steps:5, current:3, service:'admin',     started:mins(31), compensation:true,
      stepList:[{n:'create_user',s:'done'},{n:'provision_cleardesk',s:'done'},{n:'provision_apex',s:'compensating'},{n:'send_invite',s:'pending'},{n:'notify_owner',s:'pending'}] },
    { id:'sg-0041', name:'stripe-webhook-saga', status:'COMPLETED',    steps:3, current:3, service:'billing',   started:mins(55), compensation:false,
      stepList:[{n:'verify_signature',s:'done'},{n:'update_plan',s:'done'},{n:'emit_event',s:'done'}] },
    { id:'sg-0040', name:'data-export-saga',    status:'FAILED',       steps:4, current:2, service:'bap',       started:mins(80), compensation:true,
      stepList:[{n:'generate_export',s:'done'},{n:'upload_blob',s:'failed'},{n:'send_link',s:'pending'},{n:'audit_log',s:'pending'}], error:'Vercel Blob: 413 payload too large' },
  ];
  const statusTone = { RUNNING:'cyan', COMPLETED:'green', FAILED:'red', COMPENSATING:'orange' };
  const stepColor = { done:'#00ff7a', running:'#00e5ff', compensating:'#ff8c00', failed:'#ff3b5c', pending:'#1e3348' };

  return <div style={{display:'flex', height:'calc(100vh - 44px)'}}>
    <div style={{width:340, borderRight:'1px solid #0c1a2c', overflowY:'auto', flexShrink:0}}>
      <div style={{padding:'16px 18px', borderBottom:'1px solid #0c1a2c'}}>
        <div style={{fontSize:10, color:'#00ff7a', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:3, fontFamily:'IBM Plex Mono,monospace'}}>Integration · Sagas</div>
        <div style={{fontSize:18, fontWeight:600, color:'#ffffff'}}>Distributed transactions</div>
      </div>
      {sagas.map(s=>(
        <div key={s.id} onClick={()=>setSel(s)} style={{padding:'13px 18px', borderBottom:'1px solid #0c1a2c', cursor:'pointer', background:selected?.id===s.id?'#091424':'transparent', transition:'background 100ms'}}>
          <div style={{display:'flex', justifyContent:'space-between', marginBottom:6}}>
            <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#00ff7a'}}>{s.id}</span>
            <Badge label={s.status} tone={statusTone[s.status]||'neutral'} size="xs"/>
          </div>
          <div style={{fontSize:12, color:'#ffffff', marginBottom:4}}>{s.name}</div>
          <div style={{display:'flex', gap:3, marginBottom:4}}>
            {s.stepList.map((st,i)=>(
              <div key={i} style={{height:3, flex:1, background:stepColor[st.s], borderRadius:1}}/>
            ))}
          </div>
          <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', display:'flex', gap:12}}>
            <span>{s.service}</span><span>{s.current}/{s.steps} steps</span><span>{fmtAgo(s.started)} ago</span>
          </div>
          {s.error && <div style={{fontSize:10, color:'#ff3b5c', fontFamily:'IBM Plex Mono,monospace', marginTop:4}}>{s.error}</div>}
        </div>
      ))}
    </div>

    {selected ? <div style={{flex:1, overflowY:'auto', padding:'24px 28px'}}>
      <div style={{marginBottom:20, display:'flex', justifyContent:'space-between', alignItems:'flex-start'}}>
        <div>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880', marginBottom:4}}>{selected.id} · {selected.service}</div>
          <div style={{fontSize:20, fontWeight:600, color:'#ffffff', marginBottom:8}}>{selected.name}</div>
          <div style={{display:'flex', gap:8}}>
            <Badge label={selected.status} tone={statusTone[selected.status]||'neutral'}/>
            <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#4a6880'}}>{selected.current}/{selected.steps} steps · started {fmtAgo(selected.started)} ago</span>
          </div>
        </div>
        {selected.status==='FAILED' && <Btn icon="refresh-cw" variant="secondary">Retry saga</Btn>}
        {selected.compensation && <Btn icon="rotate-ccw" variant="danger" size="sm">Compensate remaining</Btn>}
      </div>

      {selected.error && <div style={{padding:'12px 16px', background:'rgba(255,59,92,0.06)', border:'1px solid rgba(255,59,92,0.2)', borderLeft:'3px solid #ff3b5c', marginBottom:20, fontSize:12, color:'#ff3b5c', fontFamily:'IBM Plex Mono,monospace'}}>{selected.error}</div>}

      <Panel>
        <PanelHeader title="Step execution" sub="saga pattern · compensate on failure"/>
        {selected.stepList.map((step,i)=>(
          <div key={i} style={{display:'flex', gap:14, padding:'14px 18px', borderBottom:'1px solid #0c1a2c', alignItems:'flex-start'}}>
            <div style={{display:'flex', flexDirection:'column', alignItems:'center', width:20, paddingTop:2}}>
              <div style={{width:10, height:10, borderRadius:'50%', background:stepColor[step.s], flexShrink:0, boxShadow:step.s==='running'?`0 0 8px #00e5ff80`:undefined, animation:step.s==='running'||step.s==='compensating'?'pulse 1s ease infinite':undefined}}/>
              {i<selected.stepList.length-1 && <div style={{width:1, height:24, background:'#0c1a2c', margin:'3px 0'}}/>}
            </div>
            <div style={{flex:1}}>
              <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:12, color: stepColor[step.s]==='#1e3348'?'#4a6880':stepColor[step.s], marginBottom:2, fontWeight:500}}>{i+1}. {step.n}</div>
              <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>
                {step.s==='done'?'Completed successfully':step.s==='running'?'Executing…':step.s==='compensating'?'Rolling back…':step.s==='failed'?'Failed — compensation triggered':'Waiting'}
              </div>
            </div>
            <Badge label={step.s.toUpperCase()} tone={step.s==='done'?'green':step.s==='running'?'cyan':step.s==='failed'?'red':step.s==='compensating'?'orange':'neutral'} size="xs"/>
          </div>
        ))}
      </Panel>
    </div> : <EmptyState icon="git-branch" title="Select a saga" body="Click a transaction on the left to inspect its step trace and compensation log."/>}
  </div>;
};

const IntegrationAuth = () => {
  const sessions = [
    { id:'sess-9f2a', user:'lena.yu@reliant.ai',   role:'super_admin', service:'console',   ip:'192.168.1.10', issued:mins(18), exp:mins(-12), active:true },
    { id:'sess-8c1b', user:'marcus.webb@reliant.ai',role:'admin',       service:'console',   ip:'192.168.1.22', issued:mins(44), exp:mins(-6),  active:true },
    { id:'sess-7d4e', user:'service:cleardesk',     role:'service',     service:'cleardesk', ip:'10.0.0.2',     issued:mins(2),  exp:mins(-28), active:true },
    { id:'sess-6b3f', user:'service:money',         role:'service',     service:'money',     ip:'10.0.0.3',     issued:mins(4),  exp:mins(-26), active:true },
    { id:'sess-5a8c', user:'service:apex',          role:'service',     service:'apex',      ip:'10.0.0.4',     issued:mins(1),  exp:mins(-29), active:true },
    { id:'sess-4e7d', user:'priya.sharma@reliant.ai',role:'operator',   service:'console',   ip:'192.168.1.31', issued:mins(180),exp:mins(150), active:false },
  ];
  const roleTone = { super_admin:'purple', admin:'cyan', operator:'neutral', service:'green' };

  return <div style={{padding:'24px 32px', maxWidth:1200}}>
    <div style={{marginBottom:22}}>
      <div style={{fontSize:10, color:'#00ff7a', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>Integration · Auth</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Active JWT sessions</h1>
    </div>

    <Panel style={{marginBottom:20}}>
      <div style={{display:'flex'}}>
        {[['Active sessions',sessions.filter(s=>s.active).length,'#00ff7a'],['Service accounts',sessions.filter(s=>s.user.startsWith('service:')).length,'#00e5ff'],['Algorithm','HS256','#4a6880'],['Expiry','30 min','#4a6880']].map(([k,v,c])=>(
          <div key={k} style={{flex:1, padding:'12px 18px', borderRight:'1px solid #0c1a2c'}}>
            <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:4}}>{k}</div>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:18, fontWeight:600, color:c}}>{v}</div>
          </div>
        ))}
        <div style={{flex:1, padding:'12px 18px', display:'flex', alignItems:'center'}}>
          <div style={{fontSize:11, color:'#4a6880', lineHeight:1.6}}>
            All tokens served server-side.<br/>Zero tokens in browser storage.<br/>Fail-closed: auth down → access denied.
          </div>
        </div>
      </div>
    </Panel>

    <Panel>
      <PanelHeader title="Session registry" sub="JWT · HS256 · 30-min expiry · sliding window" right={<Btn icon="shield-off" variant="danger" size="sm">Revoke all</Btn>}/>
      <table style={{width:'100%', borderCollapse:'collapse'}}>
        <thead>
          <tr style={{background:'#091424'}}>
            {['Session ID','Principal','Role','Service','IP','Issued','Status',''].map(h=>(
              <th key={h} style={{padding:'8px 14px', textAlign:'left', fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.07em', borderBottom:'1px solid #152637'}}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sessions.map(s=>(
            <tr key={s.id} style={{borderBottom:'1px solid #0c1a2c', opacity:s.active?1:0.45}} onMouseEnter={e=>e.currentTarget.style.background='#091424'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
              <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#00ff7a'}}>{s.id}</td>
              <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de'}}>{s.user}</td>
              <td style={{padding:'9px 14px'}}><Badge label={s.role} tone={roleTone[s.role]||'neutral'} size="xs"/></td>
              <td style={{padding:'9px 14px', fontSize:11, color:'#4a6880'}}>{s.service}</td>
              <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{s.ip}</td>
              <td style={{padding:'9px 14px', fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{fmtAgo(s.issued)} ago</td>
              <td style={{padding:'9px 14px'}}><Badge label={s.active?'ACTIVE':'EXPIRED'} tone={s.active?'green':'neutral'} size="xs"/></td>
              <td style={{padding:'9px 14px'}}>{s.active && <Btn size="xs" variant="danger" icon="x">Revoke</Btn>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  </div>;
};

Object.assign(window, { IntegrationSagas, IntegrationAuth });
