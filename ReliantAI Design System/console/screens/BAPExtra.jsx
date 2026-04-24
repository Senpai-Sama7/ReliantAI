// BAPExtra.jsx — dataset upload + AI insights list

const BAPUpload = () => {
  const [files, setFiles] = React.useState([]);
  const [drag, setDrag] = React.useState(false);

  const addFiles = (list) => {
    const newFiles = Array.from(list).map(f => ({
      name: f.name || `dataset-${Math.floor(Math.random()*999)}.csv`,
      size: f.size || Math.floor(Math.random()*5_000_000 + 100_000),
      id: Math.random().toString(36).slice(2,10),
      progress: 0,
      status: 'uploading',
    }));
    setFiles(prev => [...prev, ...newFiles]);
    newFiles.forEach(f => {
      let p = 0;
      const iv = setInterval(() => {
        p += Math.random() * 14 + 4;
        if (p >= 100) { p = 100; clearInterval(iv); setFiles(fs => fs.map(x => x.id===f.id ? {...x, progress:100, status:'validating'} : x));
          setTimeout(() => setFiles(fs => fs.map(x => x.id===f.id ? {...x, status:'ready'} : x)), 1200);
        } else {
          setFiles(fs => fs.map(x => x.id===f.id ? {...x, progress:p} : x));
        }
      }, 160);
    });
  };

  const statusColor = { uploading:'#00e5ff', validating:'#ffc400', ready:'#00ff7a', failed:'#ff3b5c' };

  return <div style={{padding:'24px 32px', maxWidth:1000}}>
    <div style={{marginBottom:22}}>
      <div style={{fontSize:10, color:'#00d4aa', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>B-A-P · Dataset Ingest</div>
      <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Upload dataset</h1>
      <div style={{fontSize:12, color:'#4a6880', marginTop:4, fontFamily:'IBM Plex Mono,monospace'}}>CSV · Excel · JSON · Parquet · up to 500MB · schema auto-detected</div>
    </div>

    {/* Drop zone */}
    <div onDragOver={e=>{e.preventDefault();setDrag(true);}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);addFiles(e.dataTransfer.files);}}
      style={{border:`1px dashed ${drag?'#00d4aa':'#152637'}`, background:drag?'rgba(0,212,170,0.04)':'#060c1a', padding:'52px 32px', textAlign:'center', transition:'all 180ms', marginBottom:20}}>
      <div style={{width:52, height:52, border:`1px solid ${drag?'#00d4aa':'#152637'}`, borderRadius:2, display:'inline-flex', alignItems:'center', justifyContent:'center', marginBottom:14}}>
        <i data-lucide="upload-cloud" style={{width:22, height:22, color:drag?'#00d4aa':'#4a6880'}}/>
      </div>
      <div style={{fontSize:15, color:'#ffffff', marginBottom:6}}>{drag?'Release to upload':'Drop CSV, Excel, or JSON files'}</div>
      <div style={{fontSize:12, color:'#4a6880', marginBottom:18}}>Files are streamed directly to the pipeline — they're never stored unprocessed</div>
      <div style={{display:'flex', gap:10, justifyContent:'center'}}>
        <Btn variant="primary" tone="bap" icon="folder-open" onClick={()=>addFiles([{name:'Q2_Revenue_Pipeline.csv',size:2_140_000},{name:'Houston_HVAC_2026.xlsx',size:890_000}])}>Browse files</Btn>
        <Btn variant="secondary" icon="database">Connect data source</Btn>
        <Btn variant="secondary" icon="sparkles" onClick={()=>addFiles([{name:'sample-dataset.csv',size:450_000}])}>Load sample</Btn>
      </div>
    </div>

    {/* File list */}
    {files.length > 0 && <Panel>
      <PanelHeader title={`Ingesting · ${files.length} dataset${files.length>1?'s':''}`} sub="auto-triggering pipeline on completion"/>
      {files.map(f=>(
        <div key={f.id} style={{padding:'12px 18px', borderBottom:'1px solid #0c1a2c', display:'flex', alignItems:'center', gap:14}}>
          <i data-lucide={f.status==='ready'?'check-circle-2':'file'} style={{width:15, height:15, color:statusColor[f.status]}}/>
          <div style={{flex:1}}>
            <div style={{fontSize:12, color:'#ffffff', fontFamily:'IBM Plex Mono,monospace', marginBottom:3}}>{f.name}</div>
            <div style={{fontSize:10, color:'#4a6880', display:'flex', gap:16}}>
              <span>{(f.size/1_000_000).toFixed(2)} MB</span>
              <span style={{color:statusColor[f.status]}}>{f.status === 'ready' ? 'Validated · pipeline queued' : f.status === 'validating' ? 'Validating schema…' : `${f.progress.toFixed(0)}% uploaded`}</span>
            </div>
          </div>
          <div style={{width:160, height:3, background:'#0c1a2c', borderRadius:1, overflow:'hidden'}}>
            <div style={{width:`${f.progress}%`, height:'100%', background:statusColor[f.status], transition:'width 160ms'}}/>
          </div>
        </div>
      ))}
      {files.some(f=>f.status==='ready') && (
        <div style={{padding:'12px 18px', display:'flex', gap:8}}>
          <Btn icon="play" variant="primary" tone="bap" onClick={()=>window.go('/bap/pipeline')}>View pipeline →</Btn>
        </div>
      )}
    </Panel>}

    {/* Schema info */}
    <Panel style={{marginTop:20}}>
      <PanelHeader title="Schema detection" sub="auto-inferred on upload"/>
      <div style={{padding:'14px 18px', display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16}}>
        {[['Supported types','int64, float64, string, bool, datetime, json'],['Null handling','Fill with col mean (numeric) or "UNKNOWN" (string)'],['Encoding','UTF-8 auto-detect · BOM stripped'],['Delimiter','Auto-detect: comma, tab, pipe, semicolon'],['Date formats','ISO 8601, US, EU, epoch — auto-parsed'],['Max columns','1,024 · wider files chunked automatically']].map(([k,v])=>(
          <div key={k}>
            <div style={{fontSize:10, color:'#4a6880', marginBottom:3, fontFamily:'IBM Plex Mono,monospace'}}>{k}</div>
            <div style={{fontSize:11, color:'#a8c4de'}}>{v}</div>
          </div>
        ))}
      </div>
    </Panel>
  </div>;
};

const BAPInsights = () => {
  const [typeFilter, setTypeFilter] = React.useState('all');
  const [confMin, setConfMin] = React.useState(0);

  const insights = [
    { id:'INS-2026-0441', type:'anomaly',  conf:0.91, model:'claude-sonnet-4.5', dataset:'Houston_HVAC_2026.xlsx', title:'Dispatch volume 42% above 7-day average', body:'Likely driven by heat index ≥ 102°F. Pattern consistent with summer 2024 surge (May–Sep). Recommend pre-allocating 3 additional technicians through end of month.', ts:mins(3), tags:['weather','capacity','dispatch'] },
    { id:'INS-2026-0440', type:'forecast', conf:0.87, model:'claude-sonnet-4.5', dataset:'Q2_Revenue_Pipeline.csv', title:'Q2 revenue projected at $1.24M ± $80k', body:'Based on current pipeline velocity (47 dispatches/day at $820 avg) and ClearDesk AR recovery rate of 94%. Upside scenario: $1.34M if heat persists through June. Downside: $1.09M if dispatch rate normalizes.', ts:mins(12), tags:['revenue','forecast','q2'] },
    { id:'INS-2026-0439', type:'summary',  conf:0.96, model:'claude-sonnet-4.5', dataset:'ClearDesk_Exports_Apr.csv', title:'AP extraction accuracy improved 1.2pp since Apr 18', body:'Threshold tuning on Apr 18 reduced escalation rate from 5.4% to 4.2%. Confidence distribution shifted: p25 from 0.71 → 0.78, p50 from 0.88 → 0.91. Aldridge Construction still outlier at 0.55.', ts:mins(28), tags:['cleardesk','accuracy','threshold'] },
    { id:'INS-2026-0438', type:'anomaly',  conf:0.78, model:'gpt-4.1',           dataset:'Q2_Revenue_Pipeline.csv', title:'3 accounts showing churn signals', body:'Engagement drop > 40% over 30 days: Sable & Finch (legal, 67 days since last dispatch), Orbital Telecom (missed 2 renewals), Hexagon Materials (support tickets +180%). Recommend outreach within 48h.', ts:mins(45), tags:['churn','accounts','risk'] },
    { id:'INS-2026-0437', type:'forecast', conf:0.82, model:'claude-sonnet-4.5', dataset:'Houston_HVAC_2026.xlsx',  title:'Technician capacity reaches ceiling by May 7', body:'At current dispatch rate, estimated on-site hours will exceed Jorge Villanueva\'s weekly cap on May 7 and Dana Okafor\'s on May 9. Recommend hiring or contractor arrangement before May 5.', ts:mins(72), tags:['capacity','staffing','forecast'] },
    { id:'INS-2026-0436', type:'summary',  conf:0.94, model:'claude-sonnet-4.5', dataset:'Audit_Log_Apr.csv',       title:'Security posture: no anomalies in 30-day window', body:'Zero failed auth attempts since last rotation. API key rotation compliance: 100%. No raw UUID KV access detected. Document preview sanitization fired 0 exceptions. All 7 security invariants passing.', ts:mins(120), tags:['security','audit','compliance'] },
  ];

  const typeTone = { anomaly:'red', forecast:'gold', summary:'cyan' };
  const filtered = insights.filter(i => (typeFilter==='all' || i.type===typeFilter) && i.conf >= confMin);

  return <div style={{padding:'24px 32px'}}>
    <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-end', marginBottom:22}}>
      <div>
        <div style={{fontSize:10, color:'#00d4aa', letterSpacing:'0.12em', textTransform:'uppercase', marginBottom:4, fontFamily:'IBM Plex Mono,monospace'}}>B-A-P · AI Insights</div>
        <h1 style={{fontFamily:"'Neue Haas Grotesk',sans-serif", fontSize:26, fontWeight:600, color:'#ffffff'}}>Insights</h1>
      </div>
      <div style={{display:'flex', gap:8, alignItems:'center'}}>
        <span style={{fontSize:11, color:'#4a6880'}}>Conf ≥</span>
        <input type="range" min={0} max={0.9} step={0.05} value={confMin} onChange={e=>setConfMin(+e.target.value)} style={{width:100, accentColor:'#00d4aa'}}/>
        <span style={{fontFamily:'IBM Plex Mono,monospace', fontSize:11, color:'#00d4aa', width:32}}>{confMin.toFixed(2)}</span>
      </div>
    </div>

    <div style={{display:'flex', gap:6, marginBottom:16}}>
      {['all','anomaly','forecast','summary'].map(t=>(
        <div key={t} onClick={()=>setTypeFilter(t)} style={{fontSize:10, padding:'4px 12px', borderRadius:2, cursor:'pointer', border:`1px solid ${typeFilter===t?'rgba(0,212,170,0.4)':'#0c1a2c'}`, background:typeFilter===t?'rgba(0,212,170,0.08)':'transparent', color:typeFilter===t?'#00d4aa':'#4a6880', transition:'all 120ms', textTransform:'capitalize'}}>{t}</div>
      ))}
      <div style={{flex:1}}/>
      <span style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace', alignSelf:'center'}}>{filtered.length} insight{filtered.length!==1?'s':''}</span>
    </div>

    <div style={{display:'flex', flexDirection:'column', gap:10}}>
      {filtered.map((ins,i)=>(
        <Panel key={ins.id} style={{borderLeft:`3px solid ${typeTone[ins.type]==='red'?'#ff3b5c':typeTone[ins.type]==='gold'?'#ffc400':'#00e5ff'}`, animation:`slide-up ${200+i*60}ms ease-out both`}}>
          <div style={{padding:'16px 20px'}}>
            <div style={{display:'flex', alignItems:'flex-start', gap:12, marginBottom:10}}>
              <Badge label={ins.type.toUpperCase()} tone={typeTone[ins.type]} size="sm"/>
              <div style={{flex:1}}>
                <div style={{fontSize:14, fontWeight:500, color:'#ffffff', marginBottom:3}}>{ins.title}</div>
                <div style={{fontSize:10, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>{ins.dataset} · {ins.model} · {fmtAgo(ins.ts)} ago</div>
              </div>
              <ConfBar val={ins.conf} width={80}/>
            </div>
            <div style={{fontSize:12, color:'#a8c4de', lineHeight:1.7, marginBottom:10}}>{ins.body}</div>
            <div style={{display:'flex', gap:6, flexWrap:'wrap'}}>
              {ins.tags.map(t=><span key={t} style={{fontFamily:'IBM Plex Mono,monospace', fontSize:9, color:'#4a6880', background:'#091424', border:'1px solid #152637', padding:'2px 7px', borderRadius:2}}>{t}</span>)}
            </div>
          </div>
        </Panel>
      ))}
      {filtered.length===0 && <EmptyState icon="search" title="No insights match" body={`Type: ${typeFilter} · Conf ≥ ${confMin.toFixed(2)}`}/>}
    </div>
  </div>;
};

Object.assign(window, { BAPUpload, BAPInsights });
