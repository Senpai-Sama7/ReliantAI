# Database Infrastructure Inventory

**Generated:** 2026-03-05T21:48:37.258521

## Summary

- **Total Databases Found:** 8
- **Connected:** 8 ✅
- **Errors:** 0 ❌
- **Not Running:** 0 ⚠️

## By Type

- **sqlite:** 4
- **postgresql:** 2
- **redis:** 2

## By Status

- ✅ **connected:** 8

## By Project

### Acropolis

✅ **sqlite**: `history.sqlite`
   - Path: `Acropolis/.ipython/profile_default/history.sqlite`
   - Version: 3.46.1 (WAL: delete)
   - Tables: sessions, sqlite_sequence, history, output_history

### Citadel

✅ **redis**: `0`
   - Path: `Citadel/.env`
   - Host: `localhost:6379`
   - Version: 7.4.8
   - Tables: keys: 10

### Gen-H

✅ **postgresql**: `hvac_templates`
   - Path: `Gen-H/hvac-template-library/.env`
   - Host: `localhost:5432`
   - Version: 15.17

✅ **redis**: `0`
   - Path: `Gen-H/hvac-template-library/.env`
   - Host: `localhost:6379`
   - Version: 7.4.8
   - Tables: keys: 10

✅ **postgresql**: `hvac_templates`
   - Path: `Gen-H/hvac-lead-generator/.env`
   - Host: `localhost:5432`
   - Version: 15.17

### Money

✅ **sqlite**: `audit_test.db`
   - Path: `Money/audit_test.db`
   - Version: 3.46.1 (WAL: delete)

✅ **sqlite**: `dispatch.db`
   - Path: `Money/dispatch.db`
   - Version: 3.46.1 (WAL: wal)
   - Tables: dispatches, messages, sqlite_sequence, dispatch_events, dispatch_current_state, db_version, agent_logs

### citadel_ultimate_a_plus

✅ **sqlite**: `lead_queue.db`
   - Path: `citadel_ultimate_a_plus/workspace/state/lead_queue.db`
   - Version: 3.46.1 (WAL: wal)
   - Tables: leads, sqlite_sequence, lead_events, builds, deployments, outreach, replies, webhook_receipts, db_version

