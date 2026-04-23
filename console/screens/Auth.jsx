// Auth.jsx — sign-in, sign-up, MFA screens (fullscreen, no chrome)

const AuthSignIn = () => {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  const submit = (e) => {
    e.preventDefault();
    if (!email || !password) { setError('Email and password are required.'); return; }
    setError(''); setLoading(true);
    setTimeout(() => { setLoading(false); window.go('/console/home'); }, 900);
  };

  return <div style={{minHeight:'100vh', background:'radial-gradient(ellipse at 50% 0%, rgba(0,229,255,0.04) 0%, transparent 55%), #020510', display:'flex', alignItems:'center', justifyContent:'center', padding:24}}>
    <div style={{width:'100%', maxWidth:400}}>
      <div style={{textAlign:'center', marginBottom:40}}>
        <div style={{display:'flex', justifyContent:'center', marginBottom:20}}><Logo size={28} wordSize={18}/></div>
        <div style={{fontSize:12, color:'#4a6880', fontFamily:'IBM Plex Mono,monospace'}}>Operator Console · Sign in</div>
      </div>
      <form onSubmit={submit} style={{display:'flex', flexDirection:'column', gap:14}}>
        <div>
          <div style={{fontSize:10, color:'#4a6880', marginBottom:5, textTransform:'uppercase', letterSpacing:'0.08em'}}>Email</div>
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="ops@reliant.ai" autoFocus style={{width:'100%', background:'#091424', border:`1px solid ${error?'#ff3b5c':'#152637'}`, color:'#ffffff', fontSize:13, padding:'10px 12px', borderRadius:2, outline:'none'}}/>
        </div>
        <div>
          <div style={{fontSize:10, color:'#4a6880', marginBottom:5, textTransform:'uppercase', letterSpacing:'0.08em'}}>Password</div>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" style={{width:'100%', background:'#091424', border:`1px solid ${error?'#ff3b5c':'#152637'}`, color:'#ffffff', fontSize:13, padding:'10px 12px', borderRadius:2, outline:'none'}}/>
        </div>
        {error && <div style={{fontSize:11, color:'#ff3b5c', display:'flex', alignItems:'center', gap:6}}>
          <i data-lucide="alert-circle" style={{width:12, height:12}}/>{error}
        </div>}
        <button type="submit" disabled={loading} style={{background:'#00e5ff', color:'#020510', border:'none', padding:'11px 16px', fontSize:13, fontWeight:700, borderRadius:2, cursor:'pointer', marginTop:4, opacity:loading?0.7:1, display:'flex', alignItems:'center', justifyContent:'center', gap:8}}>
          {loading ? <><span style={{display:'inline-block', animation:'spin 1s linear infinite'}}>↻</span> Signing in…</> : 'Sign in'}
        </button>
        <div style={{textAlign:'center', fontSize:11, color:'#4a6880'}}>
          <span style={{color:'#00e5ff', cursor:'pointer'}} onClick={()=>window.go('/auth/mfa')}>Use authenticator app →</span>
        </div>
      </form>
      <div style={{marginTop:32, padding:'14px 16px', background:'#060c1a', border:'1px solid #0c1a2c', fontSize:11, color:'#4a6880', lineHeight:1.7, fontFamily:'IBM Plex Mono,monospace'}}>
        <div style={{color:'#ffffff', marginBottom:4}}>Security notice</div>
        No credentials stored in browser. Session tokens served server-side only. Fail-closed auth — if service unavailable, access denied.
      </div>
    </div>
  </div>;
};

const AuthMFA = () => {
  const [code, setCode] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  return <div style={{minHeight:'100vh', background:'#020510', display:'flex', alignItems:'center', justifyContent:'center', padding:24}}>
    <div style={{width:'100%', maxWidth:380, textAlign:'center'}}>
      <div style={{display:'flex', justifyContent:'center', marginBottom:24}}><Logo size={24} wordSize={16}/></div>
      <div style={{fontSize:14, fontWeight:600, color:'#ffffff', marginBottom:6}}>Two-factor authentication</div>
      <div style={{fontSize:12, color:'#4a6880', marginBottom:32}}>Enter the 6-digit code from your authenticator app.</div>
      <div style={{display:'flex', gap:8, justifyContent:'center', marginBottom:24}}>
        {Array.from({length:6}).map((_,i) => (
          <input key={i} maxLength={1} style={{width:44, height:56, background:'#091424', border:'1px solid #152637', color:'#ffffff', fontSize:24, textAlign:'center', borderRadius:2, outline:'none', fontFamily:'IBM Plex Mono,monospace'}} onChange={e=>{ if(e.target.value && e.target.nextSibling) e.target.nextSibling.focus(); }}/>
        ))}
      </div>
      <Btn variant="primary" icon="shield-check" style={{width:'100%', justifyContent:'center'}} onClick={()=>window.go('/console/home')}>Verify &amp; continue</Btn>
      <div style={{marginTop:16, fontSize:11, color:'#4a6880'}}>Lost your device? <span style={{color:'#00e5ff', cursor:'pointer'}}>Use recovery code →</span></div>
    </div>
  </div>;
};

Object.assign(window, { AuthSignIn, AuthMFA });
