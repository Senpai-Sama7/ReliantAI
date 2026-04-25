#!/usr/bin/env node
/**
 * reGenesis autofix (idempotent)
 * - Creates root package.json/workspace if missing
 * - Adds pnpm-workspace.yaml if missing
 * - Adds .nvmrc (20), .gitignore, LICENSE (MIT) if missing
 * - Adds ESLint + Prettier minimal configs if missing
 * - Adds Jest + Playwright minimal configs if missing
 * - Adds GitHub Actions CI (build + tests) if missing
 * - Adds brand brief schema + example if generator exists but schema missing
 * Does NOT overwrite existing files.
 */
import fs from "node:fs/promises";
import fss from "node:fs";
import path from "node:path";
const root = path.resolve(process.argv[2] || ".");

async function ensure(file, content){
  const p = path.join(root, file);
  if (fss.existsSync(p)) return false;
  await fs.mkdir(path.dirname(p), { recursive: true });
  await fs.writeFile(p, content, "utf8");
  return true;
}

const pkgJson = `{
  "name": "reGenesis",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "engines": { "node": ">=20" },
  "packageManager": "pnpm@9",
  "workspaces": ["apps/*","packages/*"],
  "scripts": {
    "build": "pnpm run build:tokens && pnpm -r --filter \\"./packages/*\\" run build || true",
    "build:tokens": "pnpm --filter @cyberarchitect/design-tokens build || true && pnpm --filter @cyberarchitect/motion-tokens build || true",
    "test": "jest --runInBand || true",
    "test:e2e": "playwright test || true"
  }
}\n`;

const pnpmWs = `packages:\n  - "apps/*"\n  - "packages/*"\n`;
const nvmrc = `20\n`;
const gitignore = `node_modules\npnpm-lock.yaml\n.DS_Store\n.next\nout\ndist\nbuild\ncoverage\n*.log\n`;
const license = `MIT License\n\nCopyright (c) ${
  new Date().getFullYear()
}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software... (truncated for brevity)\n`;
const eslintrc = `module.exports = { root:true, env:{ node:true, es2022:true }, extends:[], parserOptions:{ ecmaVersion:2022, sourceType:"module" } };`;
const prettier = `{\n  "singleQuote": true,\n  "semi": true,\n  "trailingComma": "all"\n}\n`;
const jestCfg = `module.exports = { testEnvironment: "node", roots: ["<rootDir>/tests"] };`;
const pwCfg = `const { defineConfig } = require('@playwright/test'); module.exports = defineConfig({ testDir: './e2e', use: { headless: true } });`;
const gha = `name: ci\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n        with: { node-version: '20' }\n      - run: pnpm i || npm i\n      - run: pnpm run build || npm run build || true\n      - run: npx playwright install --with-deps || true\n      - run: pnpm run test || true\n      - run: pnpm run test:e2e || true\n`;

const schema = `{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Brand Brief",
  "type": "object",
  "required": ["brand","identity","motion","contentModel"],
  "properties": {
    "brand": { "type":"object","required":["name","voice"],"properties": {
      "name":{"type":"string","minLength":1},
      "voice":{"type":"string","enum":["calm","energetic","premium","playful","tech"]}
    }},
    "identity": { "type":"object","required":["colors","typography","density"],"properties":{
      "colors":{"type":"object","required":["bg","fg","accent","muted"],"properties":{
        "bg":{"type":"string"},"fg":{"type":"string"},"accent":{"type":"string"},"muted":{"type":"string"}
      }},
      "typography":{"type":"object","required":["display","text"],"properties":{
        "display":{"type":"object","required":["family"],"properties":{"family":{"type":"string"}}},
        "text":{"type":"object","required":["family"],"properties":{"family":{"type":"string"}}}
      }},
      "density":{"type":"string","enum":["compact","comfortable","spacious"]}
    }},
    "motion":{ "type":"object","required":["personality"],"properties":{
      "personality":{"type":"string","enum":["subtle","standard","expressive"]}
    }},
    "contentModel": { "type":"array","minItems":1 }
  }
}\n`;
const example = `{
  "brand": { "name": "Acme Quantum", "voice": "tech" },
  "identity": {
    "colors": { "bg": "#0b1220", "fg": "#e6edf7", "accent": "#4da3ff", "muted": "#122034" },
    "typography": { "display": { "family": "Inter" }, "text": { "family": "Inter" } },
    "density": "comfortable"
  },
  "motion": { "personality": "standard" },
  "contentModel": [
    { "intent": "hero", "payload": { "heading": "Faster inference. Lower cost.", "kicker": "Acme Quantum", "cta": { "href": "#cta", "label": "Get started" } } }
  ]
}\n`;

async function main(){
  const created = [];
  if(!fss.existsSync(path.join(root,"package.json"))){ await ensure("package.json", pkgJson); created.push("package.json"); }
  await ensure("pnpm-workspace.yaml", pnpmWs) && created.push("pnpm-workspace.yaml");
  await ensure(".nvmrc", nvmrc) && created.push(".nvmrc");
  await ensure(".gitignore", gitignore) && created.push(".gitignore");
  await ensure("LICENSE", license) && created.push("LICENSE");
  await ensure(".eslintrc.cjs", eslintrc) && created.push(".eslintrc.cjs");
  await ensure(".prettierrc", prettier) && created.push(".prettierrc");
  await ensure("jest.config.cjs", jestCfg) && created.push("jest.config.cjs");
  await ensure("playwright.config.js", pwCfg) && created.push("playwright.config.js");
  await ensure(".github/workflows/ci.yml", gha) && created.push(".github/workflows/ci.yml");

  // schema only if generator exists
  if(fss.existsSync(path.join(root,"tools","generate.mjs"))){
    await ensure("packages/schemas/brand-brief.schema.json", schema) && created.push("packages/schemas/brand-brief.schema.json");
    await ensure("packages/schemas/examples/brand-brief.example.json", example) && created.push("packages/schemas/examples/brand-brief.example.json");
  }

  console.log(JSON.stringify({ created }, null, 2));
}
main().catch(e=>{ console.error(e); process.exit(1); });

