## What this PR does

<!-- One sentence. What changed and why. -->

## Increment / Phase

- [ ] Phase 3 — Build
- [ ] Phase 4 — Polish
- [ ] Phase 5 — Handoff
- [ ] Hotfix
- [ ] Docs / Config only

## Verification checklist

<!-- Check every box you actually ran. Do not check items you skipped. -->

- [ ] `docker compose up --build` runs without errors
- [ ] `/health` returns `ok` on all modified services
- [ ] No secrets hardcoded (run `git grep -E -i 'api_key|secret|password' -- ':!*.example'`)
- [ ] `.env.example` updated if new env vars were added
- [ ] Langfuse traces appear for any new LLM-calling code
- [ ] If a new LangGraph node was added: error path tested, fallback returns non-null
- [ ] Audit log rule verified append-only if any audit_log changes

## Breaking changes

<!-- Does this change the A2A message schema, any API contract, or the DB schema?
If yes: describe migration path or why it is backwards-compatible. -->

None / Description:

## Notes for reviewer

<!-- Anything that needs context, known limitations, or follow-up issues. -->
