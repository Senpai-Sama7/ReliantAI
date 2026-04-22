# Task 4.2 Proof Artifacts

- `migrate_output.txt`: migration runner output for the clean SQLite database used during live rate-limit verification.
- `health.json`: auth service health response with Redis and SQLite connected before traffic generation.
- `register_rate_limit_attempts.json`: six `/register` attempts from one client IP, with attempt 6 returning `429` and a `Retry-After` value.
- `register_rate_limit_zcard.txt`: Redis sorted-set cardinality for the `/register` limiter key, showing 5 retained requests in the active window.
- `register_rate_limit_zrange.txt`: Redis sorted-set members and scores for the `/register` limiter key, proving sliding-window state is stored in Redis.
- `token_rate_limit_setup_register.json`: setup registration for the user used in token-limit verification.
- `token_rate_limit_attempts.json`: eleven `/token` attempts from one client IP, with attempt 11 returning `429` and a `Retry-After` value.
- `token_rate_limit_zcard.txt`: Redis sorted-set cardinality for the `/token` limiter key, showing 10 retained requests in the active window.
- `token_rate_limit_zrange.txt`: Redis sorted-set members and scores for the `/token` limiter key, proving sliding-window state is stored in Redis.
