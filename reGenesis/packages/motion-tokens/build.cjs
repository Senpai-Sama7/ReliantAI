#!/usr/bin/env node
const fs = require('fs').promises;
const path = require('path');

function transform(tokens, prefix=''){
  const cssVars = {}; const ts = {};
  function walk(obj, pre=''){
    for (const [k,v] of Object.entries(obj)){
      const cur = pre ? `${pre}-${k}` : k;
      if (v && v.$type && v.$value !== undefined){
        let cssValue = v.$value;
        if (v.$type === 'duration') cssValue = `${cssValue}ms`;
        if (v.$type === 'cubicBezier' && Array.isArray(cssValue)) cssValue = `cubic-bezier(${cssValue.join(',')})`;
        cssVars[`--motion-${cur}`] = cssValue;
        ts[cur.replace(/-/g,'_').toUpperCase()] = v.$value;
      } else if (typeof v === 'object' && !Array.isArray(v)){
        walk(v, cur);
      }
    }
  }
  walk(tokens);
  return { cssVars, ts };
}

async function build(){
  const src = path.join(__dirname, 'src', 'tokens.json');
  const tokens = JSON.parse(await fs.readFile(src, 'utf8'));
  const { cssVars, ts } = transform(tokens);
  const css = `:root {\n${Object.entries(cssVars).map(([k,v]) => `  ${k}: ${v};`).join('\n')}\n}`;
  const tsOut = `export const motionTokens = ${JSON.stringify(ts, null, 2)} as const;\n`;
  const jsOut = `export const motionTokens = ${JSON.stringify(ts, null, 2)};\n`;
  const dist = path.join(__dirname, 'dist');
  await fs.mkdir(dist, { recursive: true });
  await fs.writeFile(path.join(dist, 'motion.css'), css, 'utf8');
  await fs.writeFile(path.join(dist, 'motion.ts'), tsOut, 'utf8');
  await fs.writeFile(path.join(dist, 'motion.d.ts'), tsOut, 'utf8');
  await fs.writeFile(path.join(dist, 'motion.js'), jsOut, 'utf8');
  console.log('built motion tokens', Object.keys(cssVars).length);
}
build().catch(e => { console.error(e); process.exit(1); });
