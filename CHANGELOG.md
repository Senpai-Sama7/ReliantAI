# Changelog

All notable changes to the ReliantAI Platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Interactive template showcase (`/showcase`) with 4 view modes (Preview, Grid, Prompt, Compare)
  - Premium device frames: Desktop (macOS chrome), Tablet, Mobile (notch + home indicator)
  - Real-time live data editing (business name, phone, location, headline)
  - Keyboard navigation: `↑↓` cycle templates, `\` toggle sidebar
  - CodeBlock component with syntax highlighting, line numbers, copy-to-clipboard
- Template preview page (`/preview`) with JSON data viewer
- Rich template metadata system (`lib/template-meta.ts`) with personality, best-for, differentiators
- Complete mock data (`lib/mock-data.ts`) for all 6 trades with realistic content
- Generation prompts for every template (color system, layout, animations, unique features)
- `lib/api.ts` and `lib/trade-copy.ts` now tracked in repo (were gitignored by root `lib/` pattern)

### Changed
- Root `/` now redirects to `/showcase` instead of default Next.js page
- `app/globals.css` fixed `@import` order (font before Tailwind) to suppress CSS warning
- `app/layout.tsx` metadata updated to "ReliantAI — Client Sites"
- Documentation updated: README with new routes, showcase guide, file structure, template table

### Fixed
- Root `.gitignore` `lib/` pattern was incorrectly ignoring `reliantai-client-sites/lib/` source files
- Added force-tracking for client-sites library files (`api.ts`, `trade-copy.ts`, `mock-data.ts`, `template-meta.ts`)

---

## [2.1.0] - 2026-04-24

### Added
- `CLAUDE.md` v2.1 with Section 8: Codebase Health Status & Technical Debt
- Service activity matrix documenting commit frequency across all 20+ services
- Technical debt inventory with priority levels and remediation guidance

### Changed
- Documentation consolidated from 19 → 7 essential root-level files
- `README.md` navigation guide updated with audience-based routing

### Removed
- 12 redundant/completed documentation files cleaned up:
  - Audit reports superseded by completed remediation (`AUDIT_REPORT.md`, `MASTER_AUDIT_CONSOLIDATED.md`)
  - Completed checklists and status reports (`Bug-Report.md`, `CHECKLIST.md`, `COMPLETION_SUMMARY.md`)
  - Redundant guides covered by `CLAUDE.md`/`README.md` (`PLATFORM_GUIDE.md`, `QUICK_REFERENCE.md`)
  - Completed infrastructure summary (`INFRASTRUCTURE_ADDITIONS.md`)
  - Miscellaneous (`BLACKBOX.md`, `PRODUCTION_CHECKLIST.md`, `REMEDIATION_PLAN.md`, `RELIANT_OS_LAUNCH.md`)

---

## [2.0.0] - 2026-04-23

### Added
- **Reliant JIT OS** — Zero-configuration AI operations system (port 8085)
  - AES-256 vault encryption, no `.env` files required
  - Multi-role AI assistant (Auto, Support, Engineer, Sales modes)
  - Setup wizard with secure credential management
- **GrowthEngine** — Autonomous lead generation via Google Places API (port 8003)
- Full production infrastructure: nginx TLS termination, HashiCorp Vault, monitoring stack
- Prometheus + Grafana + Loki + Alertmanager observability stack
- Saga orchestrator with Kafka + Redis for distributed transactions
- Metacognitive Layer (APEX L5) — self-reflective AI engine
- A2A protocol bridge for cross-system agent communication
- `scripts/setup_wizard.py` with unattended mode and secret validation
- Pre-commit hooks for code quality and secret detection
- CI/CD pipeline with security scanning (Trivy, bandit, gitleaks)

### Changed
- Platform upgraded to federated microservices architecture (20+ services)
- All services wired through shared auth layer and event bus
- Orchestrator upgraded with Holt-Winters forecasting for auto-scaling

### Fixed — Security (All 90+ audit findings resolved across 2 rounds)
- Hardcoded absolute paths removed from all services
- CORS wildcard + credentials misconfiguration in `integration/main.py`
- RCE via `exec()` in `Citadel/desktop_gui.py` — sandboxed with timeout + blacklist
- Fail-open auth → fail-closed in all services (returns 503 when secrets missing)
- Rate limiter thread safety fixed (`threading.Lock` added to local fallback)
- JWT revocation cache unbounded growth fixed
- psycopg2 dict crash fixed with `cursor_factory=RealDictCursor` across all services
- SSE client race conditions, dispatch ID collisions, async/sync context mismatches
- Saga idempotency key now deterministic (hash-based from correlation_id)

### Security
- All 104 bugs in Bug-Report.md resolved (100% completion)
- Secrets no longer echoed to terminal; `.env.production`/`.env.staging` removed from tracking
- gitleaks configuration with enhanced secret pattern detection

---

## Guidelines for This Changelog

When making changes, add entries to the `[Unreleased]` section under appropriate categories:

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Features soon to be removed
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related fixes

Use past tense ("Added", "Changed") for clarity.

### Release Process

When releasing a new version:

1. Update all instances of version number
2. Replace `[Unreleased]` section with new version and date:
   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD
   ```
3. Add a link at the bottom:
   ```markdown
   [Unreleased]: https://github.com/Senpai-Sama7/ReliantAI/compare/vX.Y.Z...HEAD
   [X.Y.Z]: https://github.com/Senpai-Sama7/ReliantAI/releases/tag/vX.Y.Z
   ```
4. Tag the release in git:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```
