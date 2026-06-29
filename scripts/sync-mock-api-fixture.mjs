#!/usr/bin/env node
/**
 * Regenerate mock-platform-api/data/sites.json from the Playwright e2e fixture.
 * Run after editing tests/fixtures/site-content.mjs.
 */
import base from "../reliantai-client-sites/tests/fixtures/site-content.mjs";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const outDir = join(root, "..", "mock-platform-api", "data");
mkdirSync(outDir, { recursive: true });

const sites = {
  "test-hvac-austin": { ...base, slug: "test-hvac-austin", status: "live" },
  "preview-hvac-austin": {
    ...base,
    slug: "preview-hvac-austin",
    status: "preview_live",
  },
  "bad-template-austin": {
    ...base,
    slug: "bad-template-austin",
    status: "live",
    site_config: { ...base.site_config, template_id: "nonexistent-template" },
  },
};

const outPath = join(outDir, "sites.json");
writeFileSync(outPath, `${JSON.stringify(sites, null, 2)}\n`);
console.log(`Wrote ${Object.keys(sites).length} sites → ${outPath}`);
