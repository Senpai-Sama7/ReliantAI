#!/usr/bin/env node
const fs = require('fs').promises;
const path = require('path');

function transformTokens(tokens, prefix = '') {
  const cssVars = {};
  const tsConstants = {};
  for (const [key, value] of Object.entries(tokens)) {
    const current = prefix ? `${prefix}-${key}` : key;
    if (value && value.$type && value.$value !== undefined) {
      let cssValue = value.$value;
      switch (value.$type) {
        case 'dimension':
          if (typeof cssValue === 'string' && cssValue.endsWith('px')) {
            const px = parseInt(cssValue, 10);
            if (px >= 4) cssValue = `${px/16}rem`;
          }
          break;
        case 'fontFamily':
          if (Array.isArray(cssValue)) cssValue = cssValue.map(f => f.includes(' ') ? `"${f}"` : f).join(', ');
          break;
        case 'shadow':
          if (typeof cssValue === 'object') {
            const { offsetX, offsetY, blur, spread = '0px', color } = cssValue;
            cssValue = `${offsetX} ${offsetY} ${blur} ${spread} ${color}`;
          }
          break;
      }
      cssVars[`--${current}`] = cssValue;
      tsConstants[current.replace(/-/g,'_').toUpperCase()] = value.$value;
    } else if (typeof value === 'object' && !Array.isArray(value)) {
      const nested = transformTokens(value, current);
      Object.assign(cssVars, nested.cssVars);
      Object.assign(tsConstants, nested.tsConstants);
    }
  }
  return { cssVars, tsConstants };
}

async function build(){
  const tokensPath = path.join(__dirname, 'src', 'tokens.json');
  const tokens = JSON.parse(await fs.readFile(tokensPath, 'utf8'));
  const { cssVars, tsConstants } = transformTokens(tokens);
  const css = `:root {\n${Object.entries(cssVars).map(([k,v]) => `  ${k}: ${v};`).join('\n')}\n}`;
  const ts = `export const tokens = ${JSON.stringify(tsConstants, null, 2)} as const;\n`;
  const js = `export const tokens = ${JSON.stringify(tsConstants, null, 2)};\n`;
  const dist = path.join(__dirname, 'dist');
  await fs.mkdir(dist, { recursive: true });
  await fs.writeFile(path.join(dist, 'tokens.css'), css, 'utf8');
  await fs.writeFile(path.join(dist, 'tokens.ts'), ts, 'utf8');
  await fs.writeFile(path.join(dist, 'tokens.d.ts'), ts, 'utf8');
  await fs.writeFile(path.join(dist, 'tokens.js'), js, 'utf8');
  console.log('built', Object.keys(cssVars).length, 'vars');
}
build().catch(e => { console.error(e); process.exit(1); });
