# Task 4.1 Proof Artifacts

- `migrate_output.txt`: migration runner output showing `001_create_users.sql` applied and SQLite in `wal` mode.
- `health_initial.json`: auth service healthy before registration with SQLite connected.
- `register_response.json`: successful registration response for `persistent_user`.
- `token_before_restart.json`: successful login before Redis replacement.
- `redis_user_before_restart.txt`: Redis user hash present before restart.
- `sqlite_verification_before_restart.txt`: direct SQLite verification showing `journal_mode=wal`, `user_rows=1`, and the persisted user row.
- `redis_ping_after_restart.txt`: new Redis instance reachable after replacement.
- `redis_user_after_redis_restart_before_auth_restart.txt`: empty output proving the new Redis instance had no cached user data before auth restarted.
- `health_after_restart.json`: auth service healthy after restart with SQLite still connected and `user_count=1`.
- `redis_user_after_auth_restart.txt`: Redis user hash repopulated after auth restart.
- `token_after_restart.json`: successful login after Redis replacement and auth restart, proving the account survived in SQLite.
