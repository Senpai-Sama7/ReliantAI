#!/usr/bin/env node
/**
 * Add preview.reliantai.org A record in Cloudflare (76.76.21.21 → Vercel).
 *
 * Required env:
 *   CLOUDFLARE_API_TOKEN — Zone.DNS Edit for reliantai.org
 *
 * Usage:
 *   CLOUDFLARE_API_TOKEN=... node scripts/configure-preview-dns.mjs
 */
const ZONE_NAME = "reliantai.org";
const RECORD_NAME = "preview.reliantai.org";
const RECORD_IP = "76.76.21.21";

const token = process.env.CLOUDFLARE_API_TOKEN;
if (!token) {
  console.error("CLOUDFLARE_API_TOKEN is required");
  process.exit(1);
}

async function cf(path, init = {}) {
  const res = await fetch(`https://api.cloudflare.com/client/v4${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
  });
  const body = await res.json();
  if (!body.success) {
    throw new Error(JSON.stringify(body.errors || body));
  }
  return body.result;
}

async function main() {
  const zones = await cf(`/zones?name=${ZONE_NAME}`);
  const zone = zones[0];
  if (!zone) throw new Error(`Zone not found: ${ZONE_NAME}`);

  const existing = await cf(
    `/zones/${zone.id}/dns_records?name=${RECORD_NAME}&type=A`
  );
  if (existing.length > 0) {
    const rec = existing[0];
    if (rec.content === RECORD_IP && rec.proxied === false) {
      console.log(`OK: ${RECORD_NAME} already points to ${RECORD_IP}`);
      return;
    }
    await cf(`/zones/${zone.id}/dns_records/${rec.id}`, {
      method: "PATCH",
      body: JSON.stringify({ type: "A", name: RECORD_NAME, content: RECORD_IP, proxied: false }),
    });
    console.log(`UPDATED: ${RECORD_NAME} → ${RECORD_IP}`);
    return;
  }

  await cf(`/zones/${zone.id}/dns_records`, {
    method: "POST",
    body: JSON.stringify({
      type: "A",
      name: "preview",
      content: RECORD_IP,
      proxied: false,
      ttl: 1,
    }),
  });
  console.log(`CREATED: ${RECORD_NAME} → ${RECORD_IP}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
