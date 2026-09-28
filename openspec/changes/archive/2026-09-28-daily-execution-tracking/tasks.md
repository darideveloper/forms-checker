## 1. Persistence layer

- [x] 1.1 Add `sqlite3` execution log to `run.py`: `executions.db` next to `run.py`, `executions` table with `PRIMARY KEY(site, day)`, created on startup
- [x] 1.2 Add upsert helper recording `(site, today-local, status, duration_s, error, started_at-local-ISO)` after each executed check

## 2. Selection and single-run flow

- [x] 2.1 Replace run-all loop with due-selection: sites lacking today's row, ordered least-recently-run first (`NULLS FIRST`), `LIMIT 1`
- [x] 2.2 Handle nothing-due: log that all sites already ran today, skip browser launch, send no email, exit `0`
- [x] 2.3 Run the single selected check in a fresh context with existing screenshot-on-failure and failure-email behavior; log remaining due count
- [x] 2.4 Missing `check` is logged as fail: selected module without `check` is recorded as today's `fail` with the missing-contract error

## 3. Force override

- [x] 3.1 Add `--force [site]` CLI arg: with a name runs that site ignoring the guard; bare reruns the normal pick ignoring the date guard; unknown names exit non-zero with a clear error and record nothing
- [x] 3.2 Forced execution overwrites today's row and follows the standard failure path (screenshot, email, exit code)

## 4. Hygiene and verification

- [x] 4.1 Gitignore `executions.db`; update `README.md` (hourly-cron safety, one-per-day semantics, `--force`, DB file, silent skip behavior)
- [x] 4.2 Verify by dry-running selection logic: first run executes the never-run site, immediate second run exits `0` silently, `--force <site>` reruns and overwrites the row, and a date change reopens the slot
