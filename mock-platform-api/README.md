# Mock Platform API

Public stand-in for `GET /api/v2/generated-sites/{slug}` while `api.reliantai.org` is not hosted.

**Production:** https://reliantai-mock-platform-api.vercel.app

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | `{ "status": "ok" }` |
| GET | `/api/v2/generated-sites/{slug}` | Site content JSON (mirrors FastAPI shape) |

Seeded slugs: `test-hvac-austin`, `preview-hvac-austin`, `bad-template-austin`.

## Deploy

```bash
cd mock-platform-api
vercel link --yes --project reliantai-mock-platform-api
vercel deploy --prod --yes
```

Deploy from this directory only (not the monorepo root).

## Sync fixture data

After editing `reliantai-client-sites/tests/fixtures/site-content.mjs`:

```bash
node scripts/sync-mock-api-fixture.mjs
cd mock-platform-api && vercel deploy --prod --yes
```

## Wire client-sites

Set Vercel production env on `reliantai-client-sites`:

```
API_BASE_URL=https://reliantai-mock-platform-api.vercel.app
```

Redeploy client-sites from the **monorepo root** (`vercel deploy --prod`).

Replace with `https://api.reliantai.org` once the real platform API is hosted and `generated_sites` rows exist.
