#!/usr/bin/env node
/**
 * reGenesis deep local audit (static, zero deps)
 * - Workspace + manifests
 * - ESM/CJS alignment
 * - Imports vs declared deps (missing/unused)
 * - Tools (generator/replicator) presence + module type
 * - Schema + example brief presence
 * - Example app sanity (Next.js)
 * - Tests/CI/lint/format + lockfile
 * - Large files + secrets scan
 * Output: Markdown to stdout; with --json also writes AUDIT.json
 * Node >= 20
 */
import fs from "node:fs/promises";
import fss from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import os from "node:os";
const root = path.resolve(process.argv[2] || ".");

const findings = [];
const diag = { root, pkgs: [], apps: [], stats: {} };

const OK=(m)=>findings.push({level:"OK",msg:m});
const WARN=(m)=>findings.push({level:"WARN",msg:m});
const ERR=(m)=>findings.push({level:"ERROR",msg:m});
const ex=async p=>{try{await fs.access(p);return true;}catch{return false;}};
const rj=async p=>JSON.parse(await fs.readFile(p,"utf8"));
const rt=async p=>await fs.readFile(p,"utf8");
const rel=p=>path.relative(root,p)||".";

const SKIP_DIR=new Set(["node_modules",".git",".next","out","dist","build",".turbo",".cache"]);
async function walk(dir,limit=20000){
  const out=[];
  async function w(d){
    const ents=await fs.readdir(d,{withFileTypes:true}).catch(()=>[]);
    for(const e of ents){
      if(out.length>=limit) return;
      const p=path.join(d,e.name);
      if(e.isDirectory()){ if(SKIP_DIR.has(e.name)) continue; await w(p); }
      else out.push(p);
    }
  }
  await w(dir);
  return out;
}
function isRel(s){return s.startsWith("./")||s.startsWith("../")||s.startsWith("/")||s.startsWith("file:");}
function parseImports(txt){
  const set=new Set();
  const r1=/import\s+(?:[^'"]+?\s+from\s+)?["']([^"']+)["']/g;
  const r2=/import\(\s*["']([^"']+)["']\s*\)/g;
  const r3=/require\(\s*["']([^"']+)["']\s*\)/g;
  for(const r of [r1,r2,r3]){ let m; while((m=r.exec(txt))) set.add(m[1]); }
  return [...set].filter(s=>!isRel(s)&&!s.startsWith("node:")).map(s=>s.split("/")[0]);
}

async function collectPackages(){
  const out=[];
  async function scan(d){
    const ents=await fs.readdir(d,{withFileTypes:true}).catch(()=>[]);
    for(const e of ents){
      const p=path.join(d,e.name);
      if(e.isDirectory()){
        if(SKIP_DIR.has(e.name)) continue;
        if(await ex(path.join(p,"package.json"))) out.push(p);
        await scan(p);
      }
    }
  }
  if(await ex(path.join(root,"package.json"))) out.unshift(root);
  await scan(root);
  const uniq=[]; const seen=new Set();
  for(const d of out){ if(!seen.has(d)){uniq.push(d); seen.add(d);} }
  return uniq;
}

async function auditManifests(pkgDirs){
  const rootPkg=path.join(root,"package.json");
  if(!(await ex(rootPkg))) ERR(`Missing root package.json at ${rel(rootPkg)}`);
  else{
    const pj=await rj(rootPkg);
    if(!pj.workspaces) WARN("Root package.json missing workspaces (monorepo expected).");
    if(!pj.engines?.node) WARN('Root package.json missing "engines.node" (set >=20).');
    if(!pj.scripts) WARN("Root package.json missing scripts (build/test/dev).");
  }
  const ws=path.join(root,"pnpm-workspace.yaml");
  if((await ex(ws)) && !(await ex(rootPkg))) WARN("pnpm-workspace.yaml exists but root package.json is missing.");
  if((await ex(ws)) && (await ex(rootPkg))){
    const pj=await rj(rootPkg);
    if(!pj.workspaces) WARN("pnpm-workspace.yaml exists but package.json has no workspaces array.");
  }

  for(const d of pkgDirs){
    const pjPath=path.join(d,"package.json");
    const pj=await rj(pjPath).catch(()=>null);
    if(!pj){ WARN(`package.json unreadable: ${rel(pjPath)}`); continue; }
    diag.pkgs.push({dir:rel(d),name:pj.name||"(unnamed)",type:pjs(pj.type)});
    // entrypoints
    if(d!==root && !pj.exports && !pj.main && !pj.module) WARN(`Package ${pj.name||rel(d)} missing exports/main/module.`);
    if(d!==root && !pj.scripts?.build) WARN(`Package ${pj.name||rel(d)} missing build script.`);

    // imports vs deps
    const files=(await walk(d)).filter(f=>/\.(m?[jt]sx?|cjs|json)$/.test(f));
    const all=new Set();
    for(const f of files){
      if(f.endsWith(".json")) continue;
      const txt=await rt(f).catch(()=>null); if(!txt) continue;
      for(const imp of parseImports(txt)) all.add(imp);
    }
    const declared=new Set([
      ...Object.keys(pj.dependencies||{}),
      ...Object.keys(pj.devDependencies||{}),
      ...Object.keys(pj.peerDependencies||{}),
      ...Object.keys(pj.optionalDependencies||{}),
    ]);
    const builtin=new Set(["fs","path","url","os","crypto","stream","http","https","zlib","events","process","child_process","util","buffer","timers"]);
    const used=[...all].filter(x=>!builtin.has(x));
    const missing=used.filter(x=>!declared.has(x));
    const unused=[...declared].filter(x=>!used.includes(x) && d!==root);
    if(missing.length) ERR(`Missing deps in ${pj.name||rel(d)}: ${missing.join(", ")}`);
    if(unused.length) WARN(`Possibly unused deps in ${pj.name||rel(d)}: ${unused.join(", ")}`);
  }
}
function pjs(t){return t||"(unset)";}

async function auditTools(){
  const gen=path.join(root,"tools","generate.mjs");
  const repJs=path.join(root,"tools","replicator.js");
  const repMjs=path.join(root,"tools","replicator.mjs");
  const hasGen=await ex(gen), hasJs=await ex(repJs), hasMjs=await ex(repMjs);
  if(!hasGen) ERR(`Missing ${rel(gen)} (generator CLI).`);
  if(!hasJs && !hasMjs) ERR(`Missing replicator CLI (tools/replicator.js or tools/replicator.mjs).`);
  if(hasJs && hasMjs) WARN("Both replicator.js and replicator.mjs present. Pick one module system.");
  if(hasGen){
    const t=await rt(gen).catch(()=> "");
    if(!/GEMINI_API_KEY/.test(t)) WARN("generate.mjs lacks explicit GEMINI_API_KEY guard.");
    if(!/ajv/i.test(t)) WARN("generate.mjs may not validate briefs (Ajv not detected).");
  }
}

async function auditSchema(){
  const schema=path.join(root,"packages","schemas","brand-brief.schema.json");
  const example=path.join(root,"packages","schemas","examples","brand-brief.example.json");
  if(!await ex(schema)) WARN(`Missing ${rel(schema)} (brand brief JSON schema).`);
  if(!await ex(example)) WARN(`Missing ${rel(example)} (example brief).`);
}

async function auditApp(){
  const app=path.join(root,"apps","site-example");
  if(!await ex(app)){ WARN("No example app under apps/site-example."); return; }
  const pjPath=path.join(app,"package.json");
  if(!await ex(pjPath)){ WARN("apps/site-example missing package.json."); return; }
  const pj=await rj(pjPath);
  if(!pj.scripts?.dev) WARN("apps/site-example missing dev script.");
  const hasApp=await ex(path.join(app,"app"));
  const hasPages=await ex(path.join(app,"pages"));
  if(!hasApp && !hasPages) WARN("apps/site-example has neither app/ nor pages/ directory.");
  if(!pj.dependencies?.next) WARN("apps/site-example missing Next.js dependency.");
}

async function auditTestsCI(){
  const jest1=path.join(root,"jest.config.cjs");
  const jest2=path.join(root,"jest.config.js");
  const pw=path.join(root,"playwright.config.js");
  const gha=path.join(root,".github","workflows");
  if(!(await ex(jest1)) && !(await ex(jest2))) WARN("Missing Jest config.");
  if(!await ex(pw)) WARN("Missing Playwright config.");
  if(!await ex(gha)) WARN("No GitHub Actions workflows.");
}

async function auditLintFmtLocks(){
  const es=[ ".eslintrc.cjs",".eslintrc.js",".eslintrc.json"].some(n=>fss.existsSync(path.join(root,n)));
  if(!es) WARN("No ESLint config.");
  const pr = fss.existsSync(path.join(root,".prettierrc"))||fss.existsSync(path.join(root,".prettierrc.json"));
  if(!pr) WARN("No Prettier config.");
  const lock=["pnpm-lock.yaml","package-lock.json","yarn.lock"].some(n=>fss.existsSync(path.join(root,n)));
  if(!lock) WARN("No lockfile committed.");
  if(!await ex(path.join(root,"LICENSE"))) WARN("Missing LICENSE.");
  if(!await ex(path.join(root,".nvmrc"))) WARN("Missing .nvmrc (pin Node version).");
}

async function auditLargeAndSecrets(){
  const files=await walk(root,25000);
  const large=[];
  for(const f of files){
    const st=await fs.stat(f);
    if(st.size>25*1024*1024) large.push({file:rel(f),mb:(st.size/1048576).toFixed(1)});
  }
  if(large.length) WARN(`Large files (>25MB):\n  - ${large.map(x=>`${x.file} (${x.mb}MB)`).join("\n  - ")}`);
  const pats=[ {name:"AWS Key",re:/AKIA[0-9A-Z]{16}/},
               {name:"Google API Key",re:/AIza[0-9A-Za-z\-_]{35}/},
               {name:"Private Key",re:/-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----/},
               {name:"Slack Token",re:/xox[baprs]-[0-9A-Za-z-]{10,48}/} ];
  const hits=[];
  for(const f of files){
    if(/\.(png|jpg|jpeg|webp|avif|gif|pdf|zip|gz|br|ico)$/i.test(f)) continue;
    const t=await rt(f).catch(()=>null); if(!t) continue;
    for(const p of pats) if(p.re.test(t)) hits.push({file:rel(f),type:p.name});
  }
  if(hits.length) ERR(`Potential secrets:\n  - ${hits.map(h=>`${h.type}: ${h.file}`).join("\n  - ")}`);
}

async function run(){
  OK(`Scanning ${rel(root)}`);
  const pkgDirs=await collectPackages();
  await auditManifests(pkgDirs);
  await auditTools();
  await auditSchema();
  await auditApp();
  await auditTestsCI();
  await auditLintFmtLocks();
  await auditLargeAndSecrets();

  const counts=findings.reduce((a,f)=>(a[f.level]=(a[f.level]||0)+1,a),{});
  const icon=l=>l==="ERROR"?"❌":l==="WARN"?"⚠️":"✅";
  let md=`# reGenesis — Audit Report\n\n**Root:** \`${rel(root)}\`\n\n## Summary\n- OK: ${counts.OK||0}\n- WARN: ${counts.WARN||0}\n- ERROR: ${counts.ERROR||0}\n\n## Findings\n`;
  for(const f of findings) md+=`- ${icon(f.level)} ${f.msg}\n`;
  md+=`\n---\nGenerated ${new Date().toISOString()} on ${os.platform()} ${os.release()}\n`;
  process.stdout.write(md);

  if(process.argv.includes("--json")){
    await fs.writeFile(path.join(root,"AUDIT.json"), JSON.stringify({ findings, diag }, null, 2));
  }
}
run().catch(e=>{ console.error(e.stack||e); process.exit(2); });

