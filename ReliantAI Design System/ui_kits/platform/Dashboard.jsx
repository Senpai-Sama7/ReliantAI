// Dashboard.jsx — Platform Command Center Overview

const ServiceCard = ({ service, accent, status, metric, metricLabel, sub1Label, sub1Val, sub1Color, sub2Label, sub2Val, onClick }) => {
  const [hovered, setHovered] = React.useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? '#091424' : '#060c1a',
        border: `1px solid ${hovered ? accent + '40' : '#0c1a2c'}`,
        padding: 16,
        cursor: 'pointer',
        transition: 'all 150ms ease',
        flex: 1,
        minWidth: 150,
      }}
    >
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:12}}>
        <div>
          <div style={{fontSize:12,fontWeight:600,color:'#ffffff',marginBottom:2}}>{service}</div>
          <div style={{fontSize:10,color:'#4a6880',fontFamily:'IBM Plex Mono,monospace'}}>{metricLabel}</div>
        </div>
        <div style={{
          fontSize:9,fontWeight:600,padding:'2px 7px',borderRadius:2,
          background: status === 'OPERATIONAL' ? 'rgba(0,255,122,0.08)' : 'rgba(255,196,0,0.08)',
          color: status === 'OPERATIONAL' ? '#00ff7a' : '#ffc400',
          border: `1px solid ${status === 'OPERATIONAL' ? 'rgba(0,255,122,0.25)' : 'rgba(255,196,0,0.25)'}`,
          letterSpacing:'0.05em',
        }}>{status}</div>
      </div>
      <div style={{fontFamily:'IBM Plex Mono,monospace',fontSize:22,fontWeight:600,color:accent,marginBottom:4}}>{metric}</div>
      <div style={{borderTop:'1px solid #0c1a2c',paddingTop:8,display:'flex',flexDirection:'column',gap:4}}>
        <div style={{display:'flex',justifyContent:'space-between'}}>
          <span style={{fontSize:10,color:'#4a6880'}}>{sub1Label}</span>
          <span style={{fontFamily:'IBM Plex Mono,monospace',fontSize:10,color:sub1Color||'#a8c4de'}}>{sub1Val}</span>
        </div>
        <div style={{display:'flex',justifyContent:'space-between'}}>
          <span style={{fontSize:10,color:'#4a6880'}}>{sub2Label}</span>
          <span style={{fontFamily:'IBM Plex Mono,monospace',fontSize:10,color:'#a8c4de'}}>{sub2Val}</span>
        </div>
      </div>
    </div>
  );
};

const MetricsStrip = () => {
  const metrics = [
    { label: 'Kong req/s',       val: '284',   unit: 'req/s',  color: '#00e5ff' },
    { label: 'Redis queue depth',val: '12',    unit: 'msgs',   color: '#00ff7a' },
    { label: 'Kafka lag',        val: '0',     unit: 'msgs',   color: '#00ff7a' },
    { label: 'PG connections',   val: '38/100',unit: '',       color: '#a8c4de' },
    { label: 'Auth tokens/min',  val: '47',    unit: '/min',   color: '#a8c4de' },
    { label: 'Saga active',      val: '3',     unit: 'sagas',  color: '#ffc400' },
  ];
  return (
    <div style={{display:'flex',borderTop:'1px solid #0c1a2c',borderBottom:'1px solid #0c1a2c',background:'#060c1a'}}>
      {metrics.map((m, i) => (
        <div key={i} style={{flex:1,padding:'10px 16px',borderRight: i < metrics.length-1 ? '1px solid #0c1a2c' : 'none'}}>
          <div style={{fontSize:9,color:'#4a6880',textTransform:'uppercase',letterSpacing:'0.07em',marginBottom:4}}>{m.label}</div>
          <div style={{fontFamily:'IBM Plex Mono,monospace',fontSize:14,fontWeight:600,color:m.color}}>
            {m.val}<span style={{fontSize:10,color:'#4a6880',marginLeft:3}}>{m.unit}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

const PlatformDashboard = ({ onNavigate }) => {
  return (
    <div style={{display:'flex',flexDirection:'column',gap:0,height:'100%',overflow:'auto'}}>
      {/* Header */}
      <div style={{padding:'20px 24px 16px',borderBottom:'1px solid #0c1a2c'}}>
        <div style={{fontSize:11,color:'#4a6880',letterSpacing:'0.08em',textTransform:'uppercase',marginBottom:4}}>Platform</div>
        <div style={{fontSize:20,fontWeight:700,color:'#ffffff'}}>Command Center</div>
      </div>

      {/* Metrics strip */}
      <MetricsStrip />

      {/* Service health grid */}
      <div style={{padding:'20px 24px',display:'flex',gap:10,flexWrap:'wrap'}}>
        <ServiceCard service="ClearDesk" accent="#00d4aa" status="OPERATIONAL"
          metric="1,284" metricLabel="docs processed today"
          sub1Label="Escalated" sub1Val="12" sub1Color="#ff3b5c"
          sub2Label="Avg confidence" sub2Val="0.91"
          onClick={() => onNavigate('cleardesk')}/>
        <ServiceCard service="Money" accent="#ffc400" status="OPERATIONAL"
          metric="47" metricLabel="dispatches today"
          sub1Label="Pending" sub1Val="3" sub1Color="#ffc400"
          sub2Label="Completed" sub2Val="44"
          onClick={() => onNavigate('money')}/>
        <ServiceCard service="B-A-P" accent="#00e5ff" status="OPERATIONAL"
          metric="8" metricLabel="active ETL jobs"
          sub1Label="AI insights" sub1Val="24"
          sub2Label="Datasets" sub2Val="156"
          onClick={() => onNavigate('bap')}/>
        <ServiceCard service="APEX" accent="#7c5cfc" status="DEGRADED"
          metric="2" metricLabel="HITL pending"
          sub1Label="Completed runs" sub1Val="91" sub1Color="#00ff7a"
          sub2Label="Avg confidence" sub2Val="0.78"
          onClick={() => onNavigate('apex')}/>
        <ServiceCard service="Integration" accent="#00ff7a" status="OPERATIONAL"
          metric="99.97%" metricLabel="uptime · 30d"
          sub1Label="Events/hr" sub1Val="2,840"
          sub2Label="Active sagas" sub2Val="3"
          onClick={() => onNavigate('integration')}/>
      </div>

      {/* Alert */}
      <div style={{margin:'0 24px',padding:'10px 14px',background:'rgba(124,92,252,0.06)',border:'1px solid rgba(124,92,252,0.2)',borderLeft:'3px solid #7c5cfc',marginBottom:16}}>
        <div style={{fontSize:11,fontWeight:600,color:'#7c5cfc',marginBottom:3}}>APEX — HITL Decision Required</div>
        <div style={{fontSize:12,color:'#a8c4de'}}>Workflow <span style={{fontFamily:'IBM Plex Mono,monospace',color:'#7c5cfc'}}>wf-a9c3-d812</span> · confidence: <span style={{fontFamily:'IBM Plex Mono,monospace'}}>0.63</span> · Stakes: HIGH · <span style={{color:'#00e5ff',cursor:'pointer'}} onClick={() => onNavigate('apex')}>Review →</span></div>
      </div>
    </div>
  );
};

Object.assign(window, { PlatformDashboard });
