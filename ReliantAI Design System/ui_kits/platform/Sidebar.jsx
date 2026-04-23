// Sidebar.jsx — ReliantAI Platform Sidebar
// Shared nav shell for all platform screens

const SidebarNav = ({ active, onNavigate, collapsed }) => {
  const navItems = [
    { id: 'overview',    icon: 'layout-dashboard', label: 'Overview',    accent: null },
    { id: 'cleardesk',  icon: 'file-text',         label: 'ClearDesk',  accent: '#00d4aa' },
    { id: 'money',      icon: 'zap',               label: 'Money',      accent: '#ffc400' },
    { id: 'bap',        icon: 'bar-chart-2',       label: 'B-A-P',      accent: '#00e5ff' },
    { id: 'apex',       icon: 'cpu',               label: 'APEX',       accent: '#7c5cfc' },
    { id: 'integration',icon: 'layers',            label: 'Integration',accent: '#00ff7a' },
  ];
  const bottomItems = [
    { id: 'settings', icon: 'settings',     label: 'Settings' },
    { id: 'billing',  icon: 'credit-card',  label: 'Billing'  },
    { id: 'admin',    icon: 'users',        label: 'Admin'    },
  ];

  return (
    <div style={sidebarStyles.sidebar}>
      {/* Logo */}
      <div style={sidebarStyles.logo}>
        <svg width="20" height="26" viewBox="0 0 24 32" fill="none">
          <rect x="2" y="2" width="3" height="28" fill="#00e5ff"/>
          <rect x="2" y="2" width="14" height="3" fill="#00e5ff"/>
          <rect x="2" y="14" width="12" height="3" fill="#00e5ff"/>
          <rect x="13" y="2" width="3" height="15" fill="#00e5ff"/>
          <polygon points="14,17 17,17 24,30 20,30" fill="#00e5ff"/>
        </svg>
        {!collapsed && (
          <span style={sidebarStyles.logoText}>ReliantAI</span>
        )}
      </div>

      {/* Main nav */}
      <nav style={sidebarStyles.nav}>
        {navItems.map(item => (
          <NavItem key={item.id} item={item} active={active === item.id}
            onNavigate={onNavigate} collapsed={collapsed} />
        ))}
      </nav>

      {/* Bottom nav */}
      <div style={sidebarStyles.bottomNav}>
        <div style={sidebarStyles.divider}/>
        {bottomItems.map(item => (
          <NavItem key={item.id} item={item} active={active === item.id}
            onNavigate={onNavigate} collapsed={collapsed} />
        ))}
        {/* User */}
        <div style={{...sidebarStyles.userRow, ...(collapsed ? {justifyContent:'center'} : {})}}>
          <div style={sidebarStyles.avatar}>D</div>
          {!collapsed && (
            <div>
              <div style={{fontSize:11,color:'#ffffff',fontWeight:500}}>Douglas Mitchell</div>
              <div style={{fontSize:10,color:'#4a6880',fontFamily:'IBM Plex Mono,monospace'}}>admin · Houston TX</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const NavItem = ({ item, active, onNavigate, collapsed }) => {
  const [hovered, setHovered] = React.useState(false);
  const accent = item.accent || '#00e5ff';

  return (
    <div
      onClick={() => onNavigate(item.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        ...sidebarStyles.navItem,
        background: active ? '#091424' : hovered ? 'rgba(255,255,255,0.02)' : 'transparent',
        borderLeft: active ? `2px solid ${accent}` : '2px solid transparent',
        color: active ? '#ffffff' : hovered ? '#a8c4de' : '#4a6880',
        justifyContent: collapsed ? 'center' : 'flex-start',
        cursor: 'pointer',
      }}
    >
      <i data-lucide={item.icon} style={{width:16,height:16,flexShrink:0,color: active ? accent : 'inherit'}}/>
      {!collapsed && <span style={{fontSize:13,fontWeight: active ? 500 : 400}}>{item.label}</span>}
    </div>
  );
};

const sidebarStyles = {
  sidebar: {
    width: 200,
    background: '#060c1a',
    borderRight: '1px solid #0c1a2c',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    flexShrink: 0,
  },
  logo: {
    padding: '18px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    borderBottom: '1px solid #0c1a2c',
  },
  logoText: {
    fontFamily: 'IBM Plex Sans, sans-serif',
    fontSize: 14,
    fontWeight: 700,
    color: '#ffffff',
    letterSpacing: '-0.01em',
  },
  nav: {
    flex: 1,
    padding: '8px 0',
    overflowY: 'auto',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '9px 16px',
    transition: 'all 150ms ease',
    userSelect: 'none',
  },
  bottomNav: {
    padding: '0 0 8px',
  },
  divider: {
    borderTop: '1px solid #0c1a2c',
    margin: '8px 0',
  },
  userRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '10px 16px',
  },
  avatar: {
    width: 28,
    height: 28,
    background: '#091424',
    border: '1px solid #152637',
    borderRadius: 2,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 12,
    fontWeight: 600,
    color: '#00e5ff',
    flexShrink: 0,
  },
};

Object.assign(window, { SidebarNav });
