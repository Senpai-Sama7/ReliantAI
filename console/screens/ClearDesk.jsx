// ClearDesk.jsx — AP automation workspace
const CD_GREEN = '#00FF94';

const ClearDeskLanding = () => {
  const [entered, setEntered] = React.useState(false);
  return <div style={{minHeight:'100vh', background:'radial-gradient(ellipse at 50% 30%, rgba(0,255,148,0.08) 0%, transparent 60%), #020510', display:'flex', alignItems:'center', justifyContent:'center', padding:40}}>
    <div style={{maxWidth:800, textAlign:'center'}}>
      <div style={{display:'inline-flex', alignItems:'center', gap:10, padding:'6px 14px', border:`1px solid ${CD_GREEN}30`, background:`${CD_GREEN}08`, borderRadius:2, marginBottom:32, fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:CD_GREEN, letterSpacing:'0.1em'}}>
        <div style={{width:6, height:6, borderRadius:'50%', background:CD_GREEN, animation:'pulse 1.4s ease infinite'}}/>
        CLEARDESK · v3.4.1
      </div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk','Inter Tight',sans-serif", fontSize:72, fontWeight:600, color:'#ffffff', letterSpacing:'-0.03em', lineHeight:1.0, marginBottom:20}}>
        Clear the desk.<br/><span style={{color:CD_GREEN}}>Not the controls.</span>
      </h1>
      <p style={{fontSize:17, color:'#a8c4de', maxWidth:540, margin:'0 auto 40px', lineHeight:1.6}}>
        AP automation with a human in every loop that matters. Text-safe document preview. Signed share codes, no raw UUIDs. Your thresholds, your escalation rules, your exports.
      </p>
      <div style={{display:'flex', gap:12, justifyContent:'center', marginBottom:56}}>
        <Btn size="lg" variant="primary" tone="cleardesk" icon="arrow-right" onClick={()=>window.go('/cleardesk/queue')}>Enter ClearDesk</Btn>
        <Btn size="lg" variant="secondary" icon="book-open">Read the guardrails</Btn>
      </div>
      <div style={{display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:2, background:'#0c1a2c', border:'1px solid #0c1a2c'}}>
        {[
          ['99.4%','extraction accuracy','on 90-day rolling'],
          ['4.3s','batch commit p50','12 docs · parallel'],
          ['0','auth tokens in browser','by design'],
          ['28','languages supported','OCR + summarization'],
        ].map(([v,l,s])=>(
          <div key={l} style={{background:'#060c1a', padding:'18px 16px', textAlign:'left'}}>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:22, fontWeight:600, color:CD_GREEN}}>{v}</div>
            <div style={{fontSize:11, color:'#ffffff', marginTop:4}}>{l}</div>
            <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', marginTop:2}}>{s}</div>
          </div>
        ))}
      </div>
    </div>
  </div>;
};

const ClearDeskQueue = () => {
  const [tab, setTab] = React.useState('all');
  const [sel, setSel] = React.useState(null);
  const [search, setSearch] = React.useState('');
  const filtered = INVOICES.filter(i => {
    if (tab === 'escalated' && !i.escalated) return false;
    if (tab === 'review' && i.status !== 'review') return false;
    if (tab === 'ready' && i.status !== 'ready') return false;
    if (tab === 'exported' && i.status !== 'exported') return false;
    if (search && !(i.id+i.vendor).toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });
  const stats = {
    all: INVOICES.length,
    review: INVOICES.filter(i=>i.status==='review').length,
    escalated: INVOICES.filter(i=>i.escalated).length,
    ready: INVOICES.filter(i=>i.status==='ready').length,
    exported: INVOICES.filter(i=>i.status==='exported').length,
  };
  return <div style={{padding:'24px 32px'}}>
    {/* Header + metrics */}
    <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:20}}>
      <div>
        <div style={{fontSize:10, color:CD_GREEN, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>ClearDesk · Document Queue</div>
        <h1 style={{fontFamily:"'Neue Haas Grotesk','Inter Tight',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff', letterSpacing:'-0.015em'}}>Today · Apr 21, 2026</h1>
      </div>
      <div style={{display:'flex', gap:8}}>
        <Btn icon="upload" variant="secondary" onClick={()=>window.go('/cleardesk/upload')}>Upload</Btn>
        <Btn icon="download" variant="secondary" onClick={()=>window.go('/cleardesk/export')}>Export view</Btn>
        <Btn icon="message-circle" variant="primary" tone="cleardesk" onClick={()=>window.go('/cleardesk/chat')}>Ask ClearDesk</Btn>
      </div>
    </div>
    <Panel style={{marginBottom:16}}>
      <div style={{display:'flex'}}>
        <MetricTile icon="file-text" label="parsed today" value={284}/>
        <MetricTile icon="alert-triangle" label="escalated" value={12} color="#ff3b5c"/>
        <MetricTile icon="check-circle-2" label="auto-exported" value={89} color="#00ff7a" unit="%"/>
        <MetricTile icon="clock" label="avg parse" value={340} unit="ms"/>
        <MetricTile icon="dollar-sign" label="value processed" value={2.84} unit="M" color="#ffc400" delta={+14}/>
      </div>
    </Panel>

    <div style={{display:'flex', gap:12, marginBottom:12, alignItems:'center'}}>
      <Tabs tone={CD_GREEN} active={tab} onChange={setTab} tabs={[
        {id:'all',label:'All',count:stats.all},
        {id:'review',label:'Needs review',count:stats.review},
        {id:'escalated',label:'Escalated',count:stats.escalated},
        {id:'ready',label:'Ready',count:stats.ready},
        {id:'exported',label:'Exported',count:stats.exported},
      ]}/>
      <div style={{flex:1}}/>
      <Input icon="search" placeholder="INV-…, vendor, amount" value={search} onChange={e=>setSearch(e.target.value)} style={{width:260}} size="sm"/>
      <Btn size="sm" icon="filter" variant="secondary">Filters</Btn>
    </div>

    <Panel>
      <div style={{display:'grid', gridTemplateColumns:'1fr 240px 130px 100px 120px 90px 60px', padding:'10px 16px', borderBottom:'1px solid #0c1a2c', fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.08em', fontFamily:'IBM Plex Mono,monospace', gap:12}}>
        <div>Document</div><div>Vendor</div><div style={{textAlign:'right'}}>Amount</div><div>Confidence</div><div>Status</div><div>Due</div><div/>
      </div>
      {filtered.map((d,i) => (
        <div key={d.id} onClick={()=>setSel(d)} style={{display:'grid', gridTemplateColumns:'1fr 240px 130px 100px 120px 90px 60px', padding:'12px 16px', borderBottom:'1px solid #0c1a2c', fontSize:12, alignItems:'center', gap:12, cursor:'pointer', animation:`slide-up ${200+i*30}ms ease-out both`}} onMouseEnter={e=>e.currentTarget.style.background='#091424'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
          <div style={{display:'flex', alignItems:'center', gap:10}}>
            <i data-lucide="file-text" style={{width:13, height:13, color:'#4a6880'}}/>
            <div>
              <div style={{color:'#ffffff', fontFamily:'IBM Plex Mono,monospace', fontSize:11}}>{d.id}</div>
              <div style={{fontSize:10, color:'#4a6880', marginTop:1}}>{d.docType} · {d.lang.toUpperCase()}</div>
            </div>
          </div>
          <div style={{color:'#a8c4de'}}>{d.vendor}</div>
          <div style={{fontFamily:'IBM Plex Mono,monospace', color:'#ffffff', textAlign:'right'}}>{d.currency==='USD'?'$':d.currency==='EUR'?'€':d.currency==='JPY'?'¥':''}{d.amount.toLocaleString()}</div>
          <ConfBar val={d.conf} width={70}/>
          <div>
            <Badge label={d.status.toUpperCase()} tone={d.status==='escalated'?'red':d.status==='ready'?'green':d.status==='exported'?'cyan':'gold'} size="xs"/>
            {d.escalated && <div style={{fontSize:9, color:'#ff3b5c', marginTop:3}}>{d.escalationReasons.length} reason{d.escalationReasons.length>1?'s':''}</div>}
          </div>
          <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:10, color:'#4a6880'}}>{d.due.slice(5)}</div>
          <i data-lucide="chevron-right" style={{width:12, height:12, color:'#4a6880', justifySelf:'end'}}/>
        </div>
      ))}
      {filtered.length === 0 && <EmptyState icon="inbox" title="No documents match" body={`Filter: ${tab} · Search: "${search||'none'}"`}/>}
    </Panel>

    {sel && <DocumentDetail doc={sel} onClose={()=>setSel(null)}/>}
  </div>;
};

const DocumentDetail = ({ doc, onClose }) => (
  <div style={{position:'fixed', inset:0, background:'rgba(2,5,16,0.7)', zIndex:50, backdropFilter:'blur(4px)', display:'flex', justifyContent:'flex-end'}} onClick={onClose}>
    <div onClick={e=>e.stopPropagation()} style={{width:'min(920px, 90vw)', background:'#060c1a', borderLeft:'1px solid #152637', height:'100vh', overflowY:'auto', animation:'slide-left 260ms ease-out'}}>
      <div style={{padding:'18px 24px', borderBottom:'1px solid #0c1a2c', display:'flex', justifyContent:'space-between', alignItems:'center', position:'sticky', top:0, background:'#060c1a', zIndex:2}}>
        <div style={{display:'flex', alignItems:'center', gap:14}}>
          <i data-lucide="file-text" style={{width:16, height:16, color:CD_GREEN}}/>
          <div>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:13, color:'#ffffff'}}>{doc.id}</div>
            <div style={{fontSize:11, color:'#4a6880', marginTop:1}}>{doc.vendor} · {doc.lang.toUpperCase()}</div>
          </div>
        </div>
        <div style={{display:'flex', gap:8}}>
          {doc.escalated && <Btn icon="x" variant="danger">Reject</Btn>}
          <Btn icon="check" variant="success">Approve</Btn>
          <i data-lucide="x" onClick={onClose} style={{width:16, height:16, color:'#4a6880', cursor:'pointer', marginLeft:8}}/>
        </div>
      </div>

      {doc.escalated && <div style={{padding:'14px 24px', background:'rgba(255,59,92,0.06)', borderBottom:'1px solid rgba(255,59,92,0.2)'}}>
        <div style={{display:'flex', alignItems:'center', gap:8, marginBottom:8}}>
          <i data-lucide="alert-triangle" style={{width:13, height:13, color:'#ff3b5c'}}/>
          <div style={{fontSize:11, fontWeight:600, color:'#ff3b5c', letterSpacing:'0.04em', textTransform:'uppercase'}}>Escalated to human queue · {doc.escalationReasons.length} reasons</div>
        </div>
        <ul style={{listStyle:'none', paddingLeft:20, margin:0}}>
          {doc.escalationReasons.map((r,i) => <li key={i} style={{fontSize:12, color:'#a8c4de', marginBottom:3, fontFamily:'IBM Plex Mono,monospace', position:'relative'}}>
            <span style={{position:'absolute', left:-14, color:'#ff3b5c'}}>›</span>{r}
          </li>)}
        </ul>
      </div>}

      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:1, background:'#0c1a2c'}}>
        {/* Left: document preview (text-safe) */}
        <div style={{background:'#060c1a', padding:'20px 24px'}}>
          <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:10, fontFamily:'IBM Plex Mono,monospace'}}>Document preview · text-safe</div>
          <div style={{background:'#020510', border:'1px solid #0c1a2c', padding:'24px 28px', fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de', lineHeight:1.7, whiteSpace:'pre-wrap'}}>
{`INVOICE ${doc.id}
${doc.vendor}
${doc.po ? `PO: ${doc.po}` : 'No PO referenced'}

Issued: ${doc.issued}
Due:    ${doc.due}
Terms:  ${doc.terms}

LINE ITEMS (extracted)
────────────────────────────────
${doc.docType === 'invoice' ? 'Professional services     ' : 'Utility charges            '} ${doc.currency} ${(doc.amount*0.8).toFixed(2)}
${doc.docType === 'invoice' ? 'Expenses reimbursement    ' : 'Base service fee           '} ${doc.currency} ${(doc.amount*0.15).toFixed(2)}
Tax                          ${doc.currency} ${(doc.amount*0.05).toFixed(2)}
                             ─────────────────
TOTAL                        ${doc.currency} ${doc.amount.toLocaleString()}`}
          </div>
          <div style={{marginTop:12, fontSize:10, color:'#4a6880', display:'flex', alignItems:'center', gap:8}}>
            <i data-lucide="shield-check" style={{width:11, height:11, color:'#00ff7a'}}/>
            Sanitized before render · no HTML, no scripts, no embedded links
          </div>
        </div>

        {/* Right: extracted data + summary */}
        <div style={{background:'#060c1a', padding:'20px 24px'}}>
          <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:12, fontFamily:'IBM Plex Mono,monospace'}}>Extracted data · confidence {doc.conf.toFixed(2)}</div>
          <div style={{display:'grid', gap:10, marginBottom:24}}>
            {[
              ['Vendor', doc.vendor, 0.98],
              ['Amount', `${doc.currency} ${doc.amount.toLocaleString()}`, doc.conf],
              ['Currency', doc.currency, 0.99],
              ['Issued', doc.issued, 0.96],
              ['Due', doc.due, 0.94],
              ['Terms', doc.terms, 0.87],
              ['PO Reference', doc.po || '— missing', doc.po?0.98:0.2],
            ].map(([k,v,c])=>(
              <div key={k} style={{display:'grid', gridTemplateColumns:'110px 1fr 70px', gap:10, alignItems:'center', fontSize:12, padding:'6px 0', borderBottom:'1px solid #0c1a2c'}}>
                <div style={{color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', fontSize:11}}>{k}</div>
                <div style={{color:'#ffffff'}}>{v}</div>
                <ConfBar val={c} width={50} showLabel={false}/>
              </div>
            ))}
          </div>
          <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:8, fontFamily:'IBM Plex Mono,monospace'}}>Summary · {doc.lang.toUpperCase()}</div>
          <div style={{background:'#020510', border:'1px solid #0c1a2c', padding:14, fontSize:12, color:'#a8c4de', lineHeight:1.6, marginBottom:14}}>
            Invoice from {doc.vendor} for {doc.currency} {doc.amount.toLocaleString()}, due {doc.due}. {doc.po ? `Referenced against PO ${doc.po}.` : 'No purchase order reference on document.'} {doc.escalated ? 'Flagged for manual review due to escalation rules.' : 'Within normal thresholds for auto-approval.'}
          </div>
          <div style={{fontSize:9, color:'#4a6880', textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:8, fontFamily:'IBM Plex Mono,monospace'}}>Summary · EN (translated)</div>
          <div style={{background:'#020510', border:'1px solid #0c1a2c', padding:14, fontSize:12, color:'#a8c4de', lineHeight:1.6}}>
            {doc.lang === 'en' ? 'Source document is English — translation identical.' : `Rechnung von ${doc.vendor} — translation from ${doc.lang.toUpperCase()} would appear here.`}
          </div>
        </div>
      </div>
    </div>
  </div>
);

const ClearDeskUpload = () => {
  const [files, setFiles] = React.useState([]);
  const [progress, setProgress] = React.useState({});
  const [dragOver, setDragOver] = React.useState(false);
  const add = (fs) => {
    const newFs = fs.map((f, i) => ({ name:f.name || `sample-${i+1}.pdf`, size: f.size || Math.floor(Math.random()*500_000+50_000), id:'tmp_'+Math.random().toString(36).slice(2,10) }));
    setFiles(prev => [...prev, ...newFs]);
    newFs.forEach((f, i) => {
      let p = 0;
      const interval = setInterval(() => {
        p += Math.random()*12 + 3;
        if (p >= 100) { p = 100; clearInterval(interval); }
        setProgress(pg => ({ ...pg, [f.id]: p }));
      }, 180 + i*60);
    });
  };
  return <div style={{padding:'24px 32px', maxWidth:1100}}>
    <div style={{marginBottom:24}}>
      <div style={{fontSize:10, color:CD_GREEN, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>ClearDesk · Ingest</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Upload documents</h1>
      <div style={{fontSize:12, color:'#4a6880', marginTop:4, fontFamily:'IBM Plex Mono,monospace'}}>PDF · PNG · JPG · TIFF · EML · up to 50MB · OCR auto-detected</div>
    </div>
    <div onDragOver={e=>{e.preventDefault(); setDragOver(true);}} onDragLeave={()=>setDragOver(false)} onDrop={e=>{e.preventDefault(); setDragOver(false); add(Array.from(e.dataTransfer.files));}} style={{
      border:`1px dashed ${dragOver?CD_GREEN:'#152637'}`, background: dragOver?`${CD_GREEN}06`:'#060c1a', padding:'56px 32px', textAlign:'center',
      transition:'all 180ms',
    }}>
      <div style={{width:56, height:56, border:`1px solid ${dragOver?CD_GREEN:'#152637'}`, borderRadius:2, display:'inline-flex', alignItems:'center', justifyContent:'center', marginBottom:16}}>
        <i data-lucide="upload-cloud" style={{width:24, height:24, color:dragOver?CD_GREEN:'#4a6880'}}/>
      </div>
      <div style={{fontSize:16, color:'#ffffff', marginBottom:6}}>{dragOver ? 'Release to ingest' : 'Drop PDFs, emails, or photos here'}</div>
      <div style={{fontSize:12, color:'#4a6880', marginBottom:16}}>or</div>
      <div style={{display:'flex', gap:10, justifyContent:'center'}}>
        <Btn variant="primary" tone="cleardesk" icon="folder-open" onClick={()=>add(Array.from({length:3}, (_,i)=>({name:`sample-${i+1}.pdf`})))}>Browse files</Btn>
        <Btn variant="secondary" icon="mail">Forward to ingest@</Btn>
        <Btn variant="secondary" icon="sparkles" onClick={()=>add(Array.from({length:5}, (_,i)=>({name:`demo-invoice-${i+1}.pdf`})))}>Load 5 samples</Btn>
      </div>
    </div>

    {files.length > 0 && <div style={{marginTop:20}}>
      <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:10, fontFamily:'IBM Plex Mono,monospace'}}>Ingesting · {files.length} file{files.length>1?'s':''}</div>
      <Panel>
        {files.map(f => {
          const p = progress[f.id] || 0;
          const done = p >= 100;
          return <div key={f.id} style={{padding:'12px 16px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:14}}>
            <i data-lucide={done?'check-circle-2':'file'} style={{width:14, height:14, color:done?'#00ff7a':'#4a6880'}}/>
            <div style={{flex:1}}>
              <div style={{fontSize:12, color:'#ffffff', fontFamily:'IBM Plex Mono,monospace'}}>{f.name}</div>
              <div style={{fontSize:10, color:'#4a6880', marginTop:3, display:'flex', gap:12}}>
                <span>{(f.size/1024).toFixed(1)} KB</span>
                <span>{done ? 'Parsed · 0.94 conf · 320ms' : `uploading ${p.toFixed(0)}%`}</span>
              </div>
            </div>
            <div style={{width:140, height:3, background:'#0c1a2c', borderRadius:1, overflow:'hidden'}}>
              <div style={{width:`${p}%`, height:'100%', background:done?'#00ff7a':CD_GREEN, transition:'width 180ms'}}/>
            </div>
          </div>;
        })}
      </Panel>
    </div>}
  </div>;
};

const ClearDeskChat = () => {
  const [msgs, setMsgs] = React.useState([
    { role:'system', t:'Context: 284 documents parsed today. Filters applied: none.' },
    { role:'user', t:'Which vendors sent us invoices over $40k this week?' },
    { role:'assistant', t:'Two vendors breached the $40k threshold this week and are sitting in the escalation queue:\n\n• Sable & Finch Attorneys — INV-2026-0414 · $42,190\n• Aldridge Construction LLC — INV-2026-0419 · $87,200\n\nBoth require manager approval per your threshold rule. Shall I open them side-by-side?', context:['INV-2026-0414','INV-2026-0419','rule:threshold.40k'] },
    { role:'user', t:'Yes and show me Aldridge\'s payment history.' },
  ]);
  const [drafting, setDrafting] = React.useState(false);
  const [input, setInput] = React.useState('');
  React.useEffect(() => {
    setDrafting(true);
    const t = setTimeout(() => {
      setMsgs(m => [...m, { role:'assistant', t:'Opened both invoices in the detail pane.\n\nAldridge Construction LLC payment history (12 months):\n\n• 14 invoices processed · 13 auto-approved · 1 previously escalated\n• Total paid: $412,880\n• Average invoice: $29,490\n• Longest delay: INV-2025-1108 · 47 days\n\nThis week\'s $87,200 is 3x their rolling average — consistent with the Q1 site expansion PO.', context:['vendor:aldridge','hist:12mo','po:Q1-expansion'] }]);
      setDrafting(false);
    }, 1400);
    return () => clearTimeout(t);
  }, []);
  return <div style={{padding:'24px 32px', maxWidth:900, margin:'0 auto', display:'flex', flexDirection:'column', height:'calc(100vh - 44px)'}}>
    <div style={{marginBottom:20}}>
      <div style={{fontSize:10, color:CD_GREEN, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>ClearDesk · Assistant</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:22, fontWeight:600, color:'#ffffff'}}>Ask ClearDesk</h1>
    </div>
    <div style={{flex:1, overflowY:'auto', padding:'0 4px'}}>
      {msgs.map((m,i) => m.role === 'system' ? <div key={i} style={{padding:'8px 0', marginBottom:20, borderBottom:'1px solid #0c1a2c', fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', display:'flex', alignItems:'center', gap:8}}>
        <i data-lucide="terminal" style={{width:10, height:10}}/>{m.t}
      </div> : <div key={i} style={{marginBottom:20, animation:'slide-up 240ms ease-out'}}>
        <div style={{display:'flex', alignItems:'center', gap:8, marginBottom:6}}>
          {m.role==='user' ? <div style={{width:18, height:18, borderRadius:'50%', background:'linear-gradient(135deg,#00e5ff,#7c5cfc)', fontSize:9, fontWeight:700, color:'#020510', display:'flex', alignItems:'center', justifyContent:'center'}}>LY</div> : <div style={{width:18, height:18, border:`1px solid ${CD_GREEN}`, borderRadius:2, display:'flex', alignItems:'center', justifyContent:'center'}}><i data-lucide="sparkles" style={{width:9, height:9, color:CD_GREEN}}/></div>}
          <div style={{fontSize:11, color:'#ffffff', fontWeight:500}}>{m.role==='user'?'Lena Yu':'ClearDesk'}</div>
          {m.context && <div style={{display:'flex', gap:4}}>{m.context.map(c => <Badge key={c} label={c} tone="cyan" size="xs"/>)}</div>}
        </div>
        <div style={{fontSize:13, color:m.role==='user'?'#ffffff':'#a8c4de', lineHeight:1.65, whiteSpace:'pre-wrap', paddingLeft:26}}>{m.t}</div>
      </div>)}
      {drafting && <div style={{paddingLeft:26, display:'flex', gap:4, alignItems:'center'}}>
        {[0,1,2].map(i => <div key={i} style={{width:5, height:5, borderRadius:'50%', background:CD_GREEN, opacity:0.4, animation:`pulse 1s ease infinite`, animationDelay:`${i*150}ms`}}/>)}
        <span style={{fontSize:11, color:'#4a6880', marginLeft:6}}>Drafting with context…</span>
      </div>}
    </div>
    <div style={{borderTop:'1px solid #0c1a2c', paddingTop:16, marginTop:16}}>
      <div style={{display:'flex', gap:10, marginBottom:10}}>
        {['Show escalated over $40k','Vendors with dropping confidence','Export this view as CSV'].map(s => <div key={s} onClick={()=>setInput(s)} style={{padding:'5px 10px', border:'1px solid #0c1a2c', fontSize:11, color:'#4a6880', cursor:'pointer'}} onMouseEnter={e=>e.currentTarget.style.borderColor=CD_GREEN+'40'} onMouseLeave={e=>e.currentTarget.style.borderColor='#0c1a2c'}>{s}</div>)}
      </div>
      <div style={{display:'flex', gap:8, alignItems:'flex-end', background:'#091424', border:'1px solid #152637', padding:10}}>
        <i data-lucide="paperclip" style={{width:14, height:14, color:'#4a6880', cursor:'pointer'}}/>
        <textarea value={input} onChange={e=>setInput(e.target.value)} placeholder="Ask about documents, vendors, thresholds…" style={{flex:1, background:'transparent', border:'none', outline:'none', color:'#ffffff', fontSize:13, resize:'none', minHeight:22, maxHeight:120, fontFamily:'inherit'}}/>
        <Btn size="sm" variant="primary" tone="cleardesk" icon="send">Send</Btn>
      </div>
      <div style={{fontSize:10, color:'#4a6880', marginTop:6, fontFamily:'IBM Plex Mono,monospace'}}>Context: current queue filters · vendor history · policy rules · NOT source document bytes</div>
    </div>
  </div>;
};

const ClearDeskExport = () => {
  const [format, setFormat] = React.useState('csv');
  const [fields, setFields] = React.useState(['id','vendor','amount','currency','due','conf','status']);
  const allFields = ['id','vendor','amount','currency','issued','due','terms','conf','status','po','lang','docType'];
  const sample = INVOICES.slice(0,3);
  return <div style={{padding:'24px 32px', maxWidth:1100}}>
    <div style={{marginBottom:24}}>
      <div style={{fontSize:10, color:CD_GREEN, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>ClearDesk · Export</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Export filtered view</h1>
    </div>
    <div style={{display:'grid', gridTemplateColumns:'1fr 1.3fr', gap:20}}>
      <Panel>
        <PanelHeader title="Configure export"/>
        <div style={{padding:20, display:'flex', flexDirection:'column', gap:20}}>
          <div>
            <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:8, fontFamily:'IBM Plex Mono,monospace'}}>Format</div>
            <div style={{display:'flex', gap:8}}>
              {['csv','json','xlsx'].map(f => <div key={f} onClick={()=>setFormat(f)} style={{padding:'8px 18px', border:`1px solid ${format===f?CD_GREEN:'#152637'}`, color:format===f?CD_GREEN:'#a8c4de', cursor:'pointer', fontSize:12, textTransform:'uppercase', fontFamily:'IBM Plex Mono,monospace', background: format===f?`${CD_GREEN}08`:'transparent'}}>{f}</div>)}
            </div>
          </div>
          <div>
            <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:8, fontFamily:'IBM Plex Mono,monospace'}}>Fields · {fields.length}/{allFields.length}</div>
            <div style={{display:'flex', flexWrap:'wrap', gap:6}}>
              {allFields.map(f => <div key={f} onClick={()=>setFields(fs => fs.includes(f) ? fs.filter(x=>x!==f) : [...fs, f])} style={{padding:'5px 10px', border:`1px solid ${fields.includes(f)?CD_GREEN+'50':'#152637'}`, background: fields.includes(f)?`${CD_GREEN}10`:'transparent', color:fields.includes(f)?CD_GREEN:'#a8c4de', cursor:'pointer', fontSize:11, fontFamily:'IBM Plex Mono,monospace'}}>{f}</div>)}
            </div>
          </div>
          <div>
            <div style={{fontSize:10, color:'#4a6880', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:8, fontFamily:'IBM Plex Mono,monospace'}}>Filter scope</div>
            <div style={{fontSize:12, color:'#a8c4de', padding:12, background:'#091424', border:'1px solid #152637', fontFamily:'IBM Plex Mono,monospace'}}>
              tab=<span style={{color:CD_GREEN}}>all</span> · search=<span style={{color:CD_GREEN}}>""</span> · dateRange=<span style={{color:CD_GREEN}}>today</span>
            </div>
            <div style={{fontSize:10, color:'#4a6880', marginTop:6}}>Matches: 284 documents · estimated 18 KB ({format})</div>
          </div>
          <Btn variant="primary" tone="cleardesk" icon="download">Generate export</Btn>
        </div>
      </Panel>
      <Panel>
        <PanelHeader title="Preview · first 3 rows" sub={`format: ${format}`}/>
        <div style={{padding:20, fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#a8c4de', lineHeight:1.7, whiteSpace:'pre', overflow:'auto'}}>
{format === 'csv' && (fields.join(',') + '\n' + sample.map(r => fields.map(f => JSON.stringify(r[f] ?? '')).join(',')).join('\n'))}
{format === 'json' && JSON.stringify(sample.map(r => Object.fromEntries(fields.map(f=>[f, r[f]]))), null, 2)}
{format === 'xlsx' && '(binary) 3 rows · ' + fields.length + ' columns\n\nPreview not available — click Generate.'}
        </div>
      </Panel>
    </div>
  </div>;
};

const ClearDeskSettings = () => {
  const [tab, setTab] = React.useState('thresholds');
  return <div style={{padding:'24px 32px', maxWidth:900}}>
    <div style={{marginBottom:20}}>
      <div style={{fontSize:10, color:CD_GREEN, letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>ClearDesk · Settings</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Workspace settings</h1>
    </div>
    <Tabs tone={CD_GREEN} active={tab} onChange={setTab} tabs={['thresholds','sync','appearance','security']}/>
    <div style={{marginTop:24}}>
      {tab === 'thresholds' && <Panel>
        <div style={{padding:20, display:'flex', flexDirection:'column', gap:18}}>
          {[
            ['Auto-approve ceiling', 5000, 'USD', 'Invoices below this auto-export if confidence ≥ 0.90'],
            ['Escalation threshold', 40000, 'USD', 'Invoices at/above require manager approval'],
            ['Minimum confidence', 0.70, '', 'Below this routes to human review regardless of amount'],
            ['OCR retry limit', 3, 'attempts', 'Page failures retry with alternate engine'],
          ].map(([k,v,u,d])=>(
            <div key={k} style={{display:'grid', gridTemplateColumns:'1fr 160px', gap:16, alignItems:'center', paddingBottom:18, borderBottom:'1px solid #0c1a2c'}}>
              <div>
                <div style={{fontSize:13, color:'#ffffff', marginBottom:3}}>{k}</div>
                <div style={{fontSize:11, color:'#4a6880'}}>{d}</div>
              </div>
              <div style={{display:'flex', alignItems:'center', gap:8, background:'#091424', border:'1px solid #152637', padding:'6px 10px'}}>
                <input defaultValue={v} style={{background:'transparent', border:'none', outline:'none', color:'#ffffff', fontFamily:'IBM Plex Mono,monospace', width:'100%'}}/>
                {u && <span style={{fontSize:11, color:'#4a6880'}}>{u}</span>}
              </div>
            </div>
          ))}
        </div>
      </Panel>}
      {tab === 'sync' && <Panel>
        <div style={{padding:20}}>
          <div style={{fontSize:13, color:'#ffffff', marginBottom:4}}>Cross-device share codes</div>
          <div style={{fontSize:11, color:'#4a6880', marginBottom:16}}>Short-lived signed session codes. No raw UUIDs. No tokens in storage.</div>
          <div style={{background:'#091424', border:`1px solid ${CD_GREEN}40`, padding:20, display:'flex', alignItems:'center', gap:20}}>
            <div style={{fontFamily:'IBM Plex Mono,monospace', fontSize:32, fontWeight:600, color:CD_GREEN, letterSpacing:'0.15em'}}>K7-49P-2X</div>
            <div style={{flex:1}}>
              <div style={{fontSize:11, color:'#a8c4de'}}>Enter this code on another device to link it to your session.</div>
              <div style={{fontSize:10, color:'#4a6880', marginTop:3, fontFamily:'IBM Plex Mono,monospace'}}>Expires in 4:42 · single-use · signed with HS256</div>
            </div>
            <Btn icon="refresh-cw" variant="secondary">Rotate</Btn>
          </div>
        </div>
      </Panel>}
      {tab === 'appearance' && <Panel><div style={{padding:20}}>
        <div style={{fontSize:13, color:'#ffffff', marginBottom:12}}>Theme</div>
        <div style={{display:'flex', gap:10}}>
          {['Dark (default)','Dark-ultra','High contrast'].map((t,i) => <div key={t} style={{padding:'12px 16px', border:`1px solid ${i===0?CD_GREEN:'#152637'}`, flex:1, cursor:'pointer'}}>
            <div style={{fontSize:12, color:'#ffffff'}}>{t}</div>
            <div style={{fontSize:10, color:'#4a6880', marginTop:2, fontFamily:'IBM Plex Mono,monospace'}}>{['#020510','#000000','#020510/#ffffff'][i]}</div>
          </div>)}
        </div>
      </div></Panel>}
      {tab === 'security' && <Panel><div style={{padding:20, display:'flex', flexDirection:'column', gap:14}}>
        {[
          ['Browser storage audit','clean · no tokens, no capability secrets','check','green'],
          ['Auth service','healthy · fail-closed mode','shield-check','green'],
          ['Document preview sanitization','active · DOMPurify + text-safe renderer','shield','green'],
          ['Service-to-service routes','via event bus only · 0 direct calls today','git-branch','green'],
        ].map(([k,v,icon,tone]) => <div key={k} style={{display:'flex', gap:14, alignItems:'center', padding:'10px 0', borderBottom:'1px solid #0c1a2c'}}>
          <i data-lucide={icon} style={{width:16, height:16, color:'#00ff7a'}}/>
          <div style={{flex:1}}>
            <div style={{fontSize:12, color:'#ffffff'}}>{k}</div>
            <div style={{fontSize:11, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{v}</div>
          </div>
          <Badge label="OK" tone="green" size="xs"/>
        </div>)}
      </div></Panel>}
    </div>
  </div>;
};

Object.assign(window, { ClearDeskLanding, ClearDeskQueue, ClearDeskUpload, ClearDeskChat, ClearDeskExport, ClearDeskSettings });
