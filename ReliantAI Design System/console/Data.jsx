// Data.jsx — synthetic fixtures shared across the console
const now = Date.now();
const mins = (n) => new Date(now - n*60000);
const fmtAgo = (d) => {
  const s = Math.floor((now - d.getTime())/1000);
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s/60)}m`;
  if (s < 86400) return `${Math.floor(s/3600)}h`;
  return `${Math.floor(s/86400)}d`;
};
const fmtTime = (d) => d.toTimeString().slice(0,8);

// Invoices for ClearDesk
const INVOICES = [
  { id:'INV-2026-0412', vendor:'Kinetic Logistics Corp', amount:18_420.55, currency:'USD', conf:0.97, status:'ready', lang:'en', due:'2026-05-02', issued:'2026-04-18', escalated:false, docType:'invoice', po:'PO-88421', terms:'Net 30' },
  { id:'INV-2026-0413', vendor:'Hexagon Materials GmbH', amount:9_340.00, currency:'EUR', conf:0.93, status:'ready', lang:'de', due:'2026-04-28', issued:'2026-04-14', escalated:false, docType:'invoice', po:'PO-88517', terms:'Net 14' },
  { id:'INV-2026-0414', vendor:'Sable & Finch Attorneys', amount:42_190.00, currency:'USD', conf:0.62, status:'escalated', lang:'en', due:'2026-04-25', issued:'2026-04-11', escalated:true, escalationReasons:['Amount exceeds $40k threshold','Vendor not in approved list','Missing PO reference'], docType:'invoice', po:null, terms:'Due on receipt' },
  { id:'INV-2026-0415', vendor:'Taikan 商事株式会社', amount:1_284_500, currency:'JPY', conf:0.88, status:'ready', lang:'ja', due:'2026-05-10', issued:'2026-04-19', escalated:false, docType:'invoice', po:'PO-88599', terms:'Net 45' },
  { id:'INV-2026-0416', vendor:'Northwind Power Utilities', amount:2_104.77, currency:'USD', conf:0.99, status:'exported', lang:'en', due:'2026-04-26', issued:'2026-04-12', escalated:false, docType:'utility', po:null, terms:'Net 14' },
  { id:'INV-2026-0417', vendor:'Polaris Cloud Services', amount:31_500.00, currency:'USD', conf:0.78, status:'review', lang:'en', due:'2026-05-15', issued:'2026-04-16', escalated:false, docType:'service', po:'PO-88602', terms:'Net 30' },
  { id:'INV-2026-0418', vendor:'Moreau Équipement SAS', amount:14_680.40, currency:'EUR', conf:0.86, status:'ready', lang:'fr', due:'2026-05-04', issued:'2026-04-17', escalated:false, docType:'invoice', po:'PO-88611', terms:'Net 30' },
  { id:'INV-2026-0419', vendor:'Aldridge Construction LLC', amount:87_200.00, currency:'USD', conf:0.55, status:'escalated', lang:'en', due:'2026-04-24', issued:'2026-04-10', escalated:true, escalationReasons:['Amount exceeds $40k threshold','Confidence below 0.70'], docType:'invoice', po:'PO-88440', terms:'Net 30' },
  { id:'INV-2026-0420', vendor:'Brightfield Stationery Co', amount:318.22, currency:'USD', conf:0.95, status:'ready', lang:'en', due:'2026-05-01', issued:'2026-04-19', escalated:false, docType:'invoice', po:null, terms:'Net 30' },
  { id:'INV-2026-0421', vendor:'Orbital Telecom', amount:5_710.00, currency:'USD', conf:0.91, status:'ready', lang:'en', due:'2026-04-30', issued:'2026-04-15', escalated:false, docType:'utility', po:null, terms:'Net 15' },
];

// Dispatches for Money
const DISPATCHES = [
  { id:'DSP-2418', lead:'Martha Chen', phone:'(512) 555-0174', issue:'AC not cooling, unit 7y old', priority:'P2', tech:'Jorge Villanueva', eta:'14:30', status:'dispatched', urgencyScore:0.42, revenue:820, source:'Inbound SMS', summary:'Customer reports AC blowing warm air since morning. No error codes. Outdoor unit running.', createdAt:mins(14), confidence:0.93 },
  { id:'DSP-2419', lead:'Ryan O\'Hare', phone:'(512) 555-0188', issue:'Smell of gas near furnace', priority:'P0-LIFE', tech:'911 DIRECTED', eta:'—', status:'life-safety', urgencyScore:1.0, revenue:0, source:'Inbound Call', summary:'SAFETY: Gas odor detected near furnace. Customer directed to evacuate and call 911.', createdAt:mins(3), confidence:0.99, lifeSafety:true, keywords:['gas','smell','furnace'] },
  { id:'DSP-2420', lead:'Priya Ramanathan', phone:'(512) 555-0121', issue:'Annual maintenance — filter + coil clean', priority:'P4', tech:'Unassigned', eta:'Tomorrow 10:00', status:'scheduled', urgencyScore:0.12, revenue:340, source:'Web Form', summary:'Routine annual maintenance. Customer available tomorrow morning.', createdAt:mins(42), confidence:0.97 },
  { id:'DSP-2421', lead:'Aurora Santos-Cruz', phone:'(512) 555-0193', issue:'Thermostat offline after storm', priority:'P2', tech:'Dana Okafor', eta:'15:45', status:'en-route', urgencyScore:0.58, revenue:480, source:'Inbound Call', summary:'Nest thermostat not responding after power flicker. Internet works, Wi-Fi works.', createdAt:mins(22), confidence:0.91 },
  { id:'DSP-2422', lead:'Bernard Kowalski', phone:'(512) 555-0210', issue:'Water heater leaking', priority:'P1', tech:'Jorge Villanueva', eta:'13:00', status:'on-site', urgencyScore:0.81, revenue:1_240, source:'Inbound SMS', summary:'Active leak from water heater base. Customer placed bucket. Flow ongoing.', createdAt:mins(6), confidence:0.94 },
];

const APEX_DECISIONS = [
  { id:'DEC-9417', workflow:'contract-review', stage:'risk-clause', uncertainty:0.78, confidence:0.42, model:'claude-sonnet-4.5', waitingSince:mins(7), reason:'Liability cap exceeds template by 3.2x', evidence:['§4.2 liability $5M (template: $1.5M)','No indemnification carve-out for data breach','Termination clause 180-day notice (template: 60)'] },
  { id:'DEC-9418', workflow:'expense-approval', stage:'policy-check', uncertainty:0.45, confidence:0.71, model:'gpt-4.1', waitingSince:mins(12), reason:'T&E policy edge case — client-gifted airfare', evidence:['Amount: $3,420 airfare','Vendor: Sable Client Services','Policy §12 unclear on 3rd-party gifts'] },
  { id:'DEC-9419', workflow:'invoice-approval', stage:'fraud-check', uncertainty:0.62, confidence:0.56, model:'claude-sonnet-4.5', waitingSince:mins(4), reason:'Vendor bank account changed since last invoice', evidence:['Prior ACH: Chase ****4419','New ACH: BofA ****8802','Vendor onboarded 2024-03-14'] },
];

const EVENTS = [
  { t:mins(0.1), src:'cleardesk.ingest', kind:'info', msg:'Parsed INV-2026-0421 · 0.91 conf · 340ms' },
  { t:mins(0.3), src:'money.dispatch', kind:'warn', msg:'DSP-2418 SLA window closing in 14m' },
  { t:mins(0.5), src:'apex.hitl', kind:'info', msg:'DEC-9419 escalated to human queue' },
  { t:mins(0.8), src:'bap.pipeline', kind:'success', msg:'daily.snapshot completed · 2.1M rows' },
  { t:mins(1.1), src:'money.dispatch', kind:'critical', msg:'DSP-2419 LIFE-SAFETY: 911 directive issued' },
  { t:mins(1.4), src:'cleardesk.ingest', kind:'info', msg:'Batch commit · 12 documents · 4.3s' },
  { t:mins(1.9), src:'integration.bus', kind:'info', msg:'webhook.delivered stripe.com · 200' },
  { t:mins(2.3), src:'apex.langfuse', kind:'info', msg:'Trace TRC-8841 · 7 spans · $0.023' },
  { t:mins(2.8), src:'cleardesk.ingest', kind:'warn', msg:'INV-2026-0419 conf 0.55 → human queue' },
  { t:mins(3.2), src:'bap.pipeline', kind:'info', msg:'dim.customers refreshed · 418k rows' },
];

// Price tiers
const PLANS = [
  { id:'reliance', name:'Reliance', tagline:'One product. Human-gated.', price:1200, seats:5, best:false, features:['1 of: ClearDesk, Money, APEX, or B-A-P','Up to 5 seats','10k docs/mo or 500 dispatches/mo','Human-in-loop required','Email support'] },
  { id:'conduit', name:'Conduit', tagline:'Multi-product. Integration layer.', price:3800, seats:25, best:true, features:['Up to 3 products','25 seats · 50k docs/mo','Cross-service event bus','Langfuse observability','99.9% SLA · Priority support'] },
  { id:'sovereign', name:'Sovereign', tagline:'All four. Your infra.', price:12400, seats:'unlimited', best:false, features:['All four products','Unlimited seats','Self-hosted option','Custom models · fine-tune','24/7 on-call · dedicated CSM'] },
];

// Generate time-series
const genTS = (n, base, vol=0.1) => {
  let v = base;
  return Array.from({length:n}, () => { v = v * (1 + (Math.random()-0.45)*vol); return v; });
};

Object.assign(window, { INVOICES, DISPATCHES, APEX_DECISIONS, EVENTS, PLANS, genTS, mins, fmtAgo, fmtTime });
