#!/usr/bin/env node
import fs from "node:fs/promises";
import fss from "node:fs";
import path from "node:path";
import process from "node:process";
import Ajv from "ajv";
import addFormats from "ajv-formats";
import yargs from "yargs/yargs";
import { hideBin } from "yargs/helpers";

if (!globalThis.fetch) {
  const { fetch, Request, Response, Headers } = await import("undici");
  globalThis.fetch = fetch; globalThis.Request = Request; globalThis.Response = Response; globalThis.Headers = Headers;
}

const __dirname = path.dirname(new URL(import.meta.url).pathname);
const schemaPath = path.resolve(__dirname, "../packages/schemas/brand-brief.schema.json");
const brandBriefSchema = JSON.parse(await fs.readFile(schemaPath, "utf8"));
const ajv = new Ajv({ allErrors: true, strict: true }); addFormats(ajv);
const validate = ajv.compile(brandBriefSchema);

function sortedStringify(obj) {
  if (obj === null || typeof obj !== "object") return JSON.stringify(obj);
  if (Array.isArray(obj)) return `[${obj.map(v => JSON.parse(sortedStringify(v))).map(v => JSON.stringify(v)).join(",")}]`;
  const keys = Object.keys(obj).sort();
  const out = {};
  for (const k of keys) out[k] = JSON.parse(sortedStringify(obj[k]));
  return JSON.stringify(out);
}

function fontLink(identity){
  const fams = [];
  if (identity?.typography?.display?.family) fams.push(identity.typography.display.family);
  if (identity?.typography?.text?.family && identity.typography.text.family !== identity.typography.display?.family) fams.push(identity.typography.text.family);
  if (!fams.length) return "";
  const families = fams.map(f => f.replace(/\s+/g, "+") + ":wght@300;400;600;700").join("&family=");
  return `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=${families}&display=swap" rel="stylesheet">`;
}

export async function requestGemini({ model, prompt, timeout = 30000 }){
  const key = process.env.GEMINI_API_KEY;
  if (!key) { console.error("GEMINI_API_KEY is required"); process.exit(1); }
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`;
  const body = { contents: [{ parts: [{ text: prompt }]}], generationConfig: { temperature: 0, topK: 1, topP: 0.9 } };
  const retries = [500, 1000, 2000];
  let lastErr = null;
  for (let i=0;i<retries.length+1;i++){
    const controller = new AbortController();
    try {
      const t = setTimeout(() => controller.abort(), timeout);
      const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: controller.signal });
      clearTimeout(t);
      if (res.status === 429 || res.status >= 500) throw new Error(`HTTP ${res.status}`);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      const text = data?.candidates?.[0]?.content?.parts?.map(p => p.text).filter(Boolean).join("\n");
      if (!text) throw new Error("empty");
      return text.trim();
    } catch (e){
      lastErr = e; if (i < retries.length) await new Promise(r => setTimeout(r, retries[i]));
    }
  }
  throw lastErr;
}

export async function synthesizeWebsite(brief, { model = "gemini-2.5-flash-preview-0514", timeout = 30000 }={}){
  const spacing = brief?.identity?.density === "compact" ? 8 : brief?.identity?.density === "spacious" ? 16 : 12;
  const prompt = [
    "Return a single complete valid responsive HTML5 document only.",
    "No placeholders. Use provided payloads.",
    "Accessibility: skip link, landmarks, visible focus, WCAG 2.2 AA contrast.",
    "Mobile-first CSS in <style>. Use CSS custom properties:",
    `--color-bg:${brief.identity.colors.bg};--color-fg:${brief.identity.colors.fg};--color-accent:${brief.identity.colors.accent};--color-muted:${brief.identity.colors.muted};--space:${spacing}px;`,
    "Link motion.css in <head>. Defer scripts. Use Google Fonts if specified.",
    "Add IntersectionObserver to toggle .in-view on .fade-in; skip if prefers-reduced-motion.",
    "Map intents: hero-><header>, feature-grid-><section role=list>, scrollytelling-><section>, testimonial-><section><figure><blockquote><cite>, cta-><section>.",
    "Brief JSON (sorted):",
    sortedStringify(brief)
  ].join("\n");
  let html = await requestGemini({ model, prompt, timeout });
  if (!/fonts\.googleapis\.com/i.test(html)) {
    html = html.replace(/<head[^>]*>/i, m => m + "\n" + fontLink(brief.identity));
  }
  return html;
}

export async function synthesizeMotion(brief, { model = "gemini-2.5-flash-preview-0514", timeout = 30000 }={}){
  const prompt = [
    "Return CSS only. No comments.",
    "Define motion vars: --duration-fast, --duration-medium, --duration-slow, --ease-standard based on brand voice.",
    "Provide .fade-in and .fade-in.in-view transitions; body page-load keyframes; interactive focus/hover styles;",
    "@media (prefers-reduced-motion: reduce){ *,*::before,*::after { animation-duration:0.01ms!important; animation-iteration-count:1!important; transition-duration:0.01ms!important; transform:none!important; scroll-behavior:auto!important; } }",
    "Voice:",
    JSON.stringify({ voice: brief.brand.voice, personality: brief.motion.personality })
  ].join("\n");
  return await requestGemini({ model, prompt, timeout });
}

async function main(){
  const argv = yargs(hideBin(process.argv))
    .option('brief', { type: 'string', demandOption: true, describe: 'Path to brand brief JSON' })
    .option('outputDir', { type: 'string', demandOption: true, describe: 'Output directory' })
    .option('model', { type: 'string', default: 'gemini-2.5-flash-preview-0514' })
    .option('force', { type: 'boolean', default: false })
    .option('dry-run', { type: 'boolean', default: false })
    .help()
    .parse();
  const briefPath = argv.brief;
  const outputDir = argv.outputDir;
  const model = argv.model;
  const dry = argv['dry-run'];
  const force = argv.force;
  let brief;
  try{
    brief = JSON.parse(await fs.readFile(path.resolve(briefPath), "utf8"));
  } catch(e){
    console.error("Failed to read brief:", e.message); process.exit(1);
  }
  const valid = validate(brief);
  if (!valid){
    console.error("Brand brief validation errors:");
    for (const [i, err] of (validate.errors||[]).entries()){
      console.error(`${i+1}. ${err.instancePath || "/"} ${err.message}`);
    }
    process.exit(1);
  }

  const html = await synthesizeWebsite(brief, { model });
  const css = await synthesizeMotion(brief, { model });
  const out = path.resolve(outputDir);
  const indexPath = path.join(out, "index.html");
  const motionPath = path.join(out, "motion.css");
  if (dry){
    console.log("DRY RUN");
    console.log(indexPath, Buffer.byteLength(html, "utf8"), "bytes");
    console.log(motionPath, Buffer.byteLength(css, "utf8"), "bytes");
    process.exit(0);
  }
  await fs.mkdir(out, { recursive: true });
  if (!force){
    if (fss.existsSync(indexPath) || fss.existsSync(motionPath)){
      console.error("Output exists. Use --force to overwrite.");
      process.exit(1);
    }
  }
  await fs.writeFile(indexPath, html, "utf8");
  await fs.writeFile(motionPath, css, "utf8");
  console.log(indexPath);
  console.log(motionPath);
}

if (import.meta.url === `file://${process.argv[1]}`){
  main().catch(e => { console.error(e); process.exit(1); });
}
