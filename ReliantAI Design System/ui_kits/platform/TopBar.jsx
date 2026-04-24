// TopBar.jsx — ReliantAI Platform Top Bar

const TopBar = ({ onCommandK, notifications = 3 }) => {
  const services = [
    { label: 'ClearDesk', status: 'ok',   color: '#00d4aa' },
    { label: 'Money',     status: 'ok',   color: '#ffc400' },
    { label: 'B-A-P',     status: 'ok',   color: '#00e5ff' },
    { label: 'APEX',      status: 'warn', color: '#7c5cfc' },
    { label: 'Integration',status:'ok',   color: '#00ff7a' },
  ];

  return (
    <div style={topBarStyles.bar}>
      {/* Search / Command palette trigger */}
      <div style={topBarStyles.search} onClick={onCommandK}>
        <i data-lucide="search" style={{width:13,height:13,color:'#4a6880'}}/>
        <span style={topBarStyles.searchText}>Search or Cmd+K…</span>
        <span style={topBarStyles.kbd}>⌘K</span>
      </div>

      <div style={{flex:1}}/>

      {/* Service health strip */}
      <div style={topBarStyles.healthStrip}>
        {services.map(s => (
          <div key={s.label} style={topBarStyles.healthDot} title={`${s.label}: ${s.status === 'ok' ? 'Operational' : 'Degraded'}`}>
            <div style={{
              width: 6, height: 6, borderRadius: '50%',
              background: s.status === 'ok' ? s.color : '#ff3b5c',
              boxShadow: `0 0 4px ${s.status === 'ok' ? s.color : '#ff3b5c'}80`,
            }}/>
            <span style={{fontSize:10,color:'#4a6880'}}>{s.label}</span>
          </div>
        ))}
      </div>

      {/* Notifications */}
      <div style={topBarStyles.iconBtn}>
        <i data-lucide="bell" style={{width:15,height:15,color:'#4a6880'}}/>
        {notifications > 0 && (
          <div style={topBarStyles.badge}>{notifications}</div>
        )}
      </div>

      {/* User avatar */}
      <div style={{...topBarStyles.iconBtn, background:'#091424', border:'1px solid #152637', borderRadius:2, padding:'4px 8px', gap:6, cursor:'pointer'}}>
        <div style={{width:20,height:20,background:'#060c1a',border:'1px solid #152637',borderRadius:2,display:'flex',alignItems:'center',justifyContent:'center',fontSize:10,fontWeight:700,color:'#00e5ff'}}>D</div>
        <span style={{fontSize:12,color:'#a8c4de'}}>Mitchell</span>
        <i data-lucide="chevron-down" style={{width:12,height:12,color:'#4a6880'}}/>
      </div>
    </div>
  );
};

const topBarStyles = {
  bar: {
    height: 48,
    background: '#060c1a',
    borderBottom: '1px solid #0c1a2c',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '0 20px',
    flexShrink: 0,
  },
  search: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: '#091424',
    border: '1px solid #152637',
    borderRadius: 2,
    padding: '5px 12px',
    cursor: 'pointer',
    width: 220,
  },
  searchText: {
    fontSize: 12,
    color: '#4a6880',
    flex: 1,
  },
  kbd: {
    fontSize: 10,
    color: '#1e3348',
    background: '#060c1a',
    border: '1px solid #0c1a2c',
    borderRadius: 2,
    padding: '1px 5px',
    fontFamily: 'IBM Plex Mono, monospace',
  },
  healthStrip: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
  },
  healthDot: {
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    cursor: 'default',
  },
  iconBtn: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    gap: 4,
    padding: 6,
    cursor: 'pointer',
  },
  badge: {
    position: 'absolute',
    top: 2,
    right: 2,
    background: '#ff3b5c',
    color: '#fff',
    fontSize: 9,
    fontWeight: 700,
    borderRadius: '50%',
    width: 14,
    height: 14,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
};

Object.assign(window, { TopBar });
