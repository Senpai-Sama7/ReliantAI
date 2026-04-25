
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function hash(s){ return crypto.createHash('sha256').update(s).digest('hex'); }
const css = fs.readFileSync(path.resolve('packages/design-tokens/dist/tokens.css'), 'utf8');
const ts = fs.readFileSync(path.resolve('packages/design-tokens/dist/tokens.ts'), 'utf8');
console.log('tokens.css', hash(css));
console.log('tokens.ts', hash(ts));
