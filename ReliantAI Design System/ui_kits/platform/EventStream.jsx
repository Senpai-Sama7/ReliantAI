// EventStream.jsx — Live Event Bus Stream Panel

const EVENT_DATA = [
  { id:'evt-a3f9', type:'dispatch.completed',      source:'money',      ts:'14:32:07', payload:'dispatch_id: DSP-2025-8821, tech: Rodriguez', color:'#00ff7a' },
  { id:'evt-b81c', type:'document.processed',       source:'cleardesk',  ts:'14:31:54', payload:'doc_id: INV-2025-0441, confidence: 0.61', color:'#00d4aa' },
  { id:'evt-c22d', type:'agent.hitl_required',      source:'apex',       ts:'14:31:41', payload:'wf_id: wf-a9c3-d812, stakes: HIGH', color:'#7c5cfc' },
  { id:'evt-d55e', type:'lead.created',             source:'money',      ts:'14:31:28', payload:'phone: +1713…, urgency: URGENT', color:'#ffc400' },
  { id:'evt-e90f', type:'analytics.recorded',       source:'bap',        ts:'14:31:15', payload:'dataset: Q2_Revenue_Pipeline.csv, rows: 4821', color:'#00e5ff' },
  { id:'evt-f12a', type:'saga.completed',           source:'integration', ts:'14:30:59', payload:'saga_id: sg-0041, steps: 3/3', color:'#00ff7a' },
  { id:'evt-g34b', type:'document.escalated',       source:'cleardesk',  ts:'14:30:44', payload:'doc_id: INV-2025-0398, reason: confidence_low', color:'#ff3b5c' },
  { id:'evt-h56c', type:'dispatch.requested',       source:'money',      ts:'14:30:31', payload:'urgency: LIFE_SAFETY, location: 4821 Westheimer', color:'#ff3b5c' },
  { id:'evt-i78d', type:'agent.task.completed',     source:'apex',       ts:'14:30:18', payload:'agent: research, confidence: 0.94', color:'#7c5cfc' },
  { id:'evt-j90e', type:'user.updated',             source:'auth',       ts:'14:30:05', payload:'user_id: usr-0012, role: manager', color:'#4a6880' },
  { id:'evt-k12f', type:'analytics.recorded',       source:'bap',        ts:'14:29:52', payload:'insight_type: anomaly, confidence: 0.87', color:'#00e5ff' },
  { id:'evt-l34g', type:'saga.started',             source:'integration', ts:'14:29:39', payload:'saga_id: sg-0042, service: money', color:'#00ff7a' },
];

const EventStream = () => {
  const [filter, setFilter] = React.useState('all');
  const [tick, setTick] = React.useState(0);

  React.useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 4000);
    return () => clearInterval(t);
  }, []);

  const sources = ['all','cleardesk','money','apex','bap','integration','auth'];
  const filtered = filter === 'all' ? EVENT_DATA : EVENT_DATA.filter(e => e.source === filter);

  return (
    <div style={{display:'flex',flexDirection:'column',height:'100%'}}>
      {/* Header */}
      <div style={{padding:'20px 24px 12px',borderBottom:'1px solid #0c1a2c',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
        <div>
          <div style={{fontSize:11,color:'#4a6880',letterSpacing:'0.08em',textTransform:'uppercase',marginBottom:4}}>Integration Layer</div>
          <div style={{fontSize:18,fontWeight:700,color:'#ffffff'}}>Live Event Stream</div>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:6}}>
          <div style={{width:6,height:6,borderRadius:'50%',background:'#00ff7a',boxShadow:'0 0 6px #00ff7a80'}}/>
          <span style={{fontSize:11,color:'#4a6880',fontFamily:'IBM Plex Mono,monospace'}}>LIVE · Redis Streams</span>
        </div>
      </div>

      {/* Filter */}
      <div style={{padding:'8px 24px',display:'flex',gap:6,borderBottom:'1px solid #0c1a2c',flexWrap:'wrap'}}>
        {sources.map(s => (
          <div key={s} onClick={() => setFilter(s)} style={{
            fontSize:10,fontWeight:500,padding:'3px 8px',borderRadius:2,cursor:'pointer',
            background: filter === s ? 'rgba(0,229,255,0.1)' : 'transparent',
            color: filter === s ? '#00e5ff' : '#4a6880',
            border: `1px solid ${filter === s ? 'rgba(0,229,255,0.3)' : '#0c1a2c'}`,
            transition:'all 150ms',
          }}>{s}</div>
        ))}
      </div>

      {/* Stream */}
      <div style={{flex:1,overflowY:'auto'}}>
        {filtered.map((evt, i) => (
          <div key={evt.id + tick} style={{
            display:'flex',alignItems:'flex-start',gap:12,
            padding:'9px 24px',
            borderBottom:'1px solid #0c1a2c',
            background: i === 0 && tick > 0 ? 'rgba(0,229,255,0.03)' : 'transparent',
            transition:'background 500ms',
          }}>
            <div style={{width:6,height:6,borderRadius:'50%',background:evt.color,marginTop:5,flexShrink:0,boxShadow:`0 0 4px ${evt.color}60`}}/>
            <div style={{flex:1,minWidth:0}}>
              <div style={{display:'flex',alignItems:'baseline',gap:10,marginBottom:2}}>
                <span style={{fontFamily:'IBM Plex Mono,monospace',fontSize:12,color:evt.color,fontWeight:500}}>{evt.type}</span>
                <span style={{fontSize:10,color:'#4a6880',fontFamily:'IBM Plex Mono,monospace'}}>{evt.source}</span>
              </div>
              <div style={{fontFamily:'IBM Plex Mono,monospace',fontSize:10,color:'#4a6880',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{evt.payload}</div>
            </div>
            <div style={{fontFamily:'IBM Plex Mono,monospace',fontSize:10,color:'#1e3348',flexShrink:0}}>{evt.ts}</div>
            <div style={{fontFamily:'IBM Plex Mono,monospace',fontSize:9,color:'#1e3348',flexShrink:0,marginTop:1}}>{evt.id}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

Object.assign(window, { EventStream });
