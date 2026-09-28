## Context

`run.py` currently discovers `checks/*.py` and submits every contact form on each invocation — correct for manual runs, unsafe for an hourly cron (24 real submissions per site per day). The user confirmed via exploration: hourly cron (external, out of scope), exactly one check per tick, each site at most once per local-calendar day, failures consume the slot, stdlib-only persistence, minimal row, `--force` escape hatch. No active changes exist; affected specs are `central-runner` (behavior change) and new `execution-tracking`.

## Goals / Non-Goals

**Goals:**
- Hourly cron is safe: at most one real form submission per site per local day.
- Every execution (pass/fail) is durably recorded and queryable.
- Same-day debugging stays possible via an explicit override.
- Zero new dependencies; existing alerting/screenshot/exit-code behavior preserved.

**Non-Goals:**
- Cron setup itself (external).
- Retries, backoff, or alerting changes — failure path is untouched.
- History viewer/UI, retention pruning, multi-process locking.
- Changes to the `check(page)` contract.

## Decisions

### 1. stdlib `sqlite3`, one file, one table — over JSON state or marker files
`executions.db` (gitignored, next to `failures/`) with a single table:
`executions(site TEXT, day TEXT /* YYYY-MM-DD local */, status TEXT /* pass|fail */, duration_s REAL, error TEXT, started_at TEXT /* ISO local */, PRIMARY KEY(site, day))`.
Alternatives: a JSON state file (corrupts on crashed writes, hand-rolled queries) and `state/<site>-<date>` marker files (a directory listing as a database, `stat` per site for ordering). SQLite is stdlib, crash-safe, and answers "who is due, oldest first" in one query. Absence of today's row *is* the due signal — `skipped` is never stored.

### 2. Enforce once-per-day in the schema — over app-level `if` checks
`PRIMARY KEY(site, day)` makes doubles structurally impossible (upsert via `INSERT ... ON CONFLICT(site, day) DO UPDATE`). The guard is a property of the data, not of a code path that a future edit could bypass.

### 3. Selection = one query: due sites ordered by last run, `LIMIT 1`
Due = discovered sites with no row for `date.today().isoformat()` (local). Order by `MAX(started_at)` ascending, `NULLS FIRST` so never-run and newly added sites go first — this self-heals after missed cron ticks. `--force <site>` bypasses the guard for that site and overwrites today's row; bare `--force` ignores the date guard on the normal pick (least-recently-run overall).

### 4. Fail consumes the slot — over retry-next-tick
Retrying a failed form hourly re-submits to a known-broken endpoint and duplicates alerts. The failure email already fires on the failing tick; the site goes quiet until tomorrow. Keeps the schema attempt-free.

### 5. None-due ticks are silent successes — over special exit codes
No due sites → log line, no email, exit `0`. Cron stays green; monitoring distinguishes "checked OK" from "nothing due" via the log line and the DB, not via exit codes that would need new alerting rules. Single executed check keeps today's semantics: exit `1` + failure email on fail.

### 6. No locking, no viewer, no pruning — over building for scale that doesn't exist
One ~30s check per hourly tick cannot overlap itself; `sqlite3` CLI is the viewer; one row/site/day (~365 rows/site/year) needs no retention policy. Each gets a one-line re-entry point if pain appears.

## Risks / Trade-offs

- [Starvation past 24 sites] → 24 hourly slots bound daily capacity; adding a 25th site means some site waits a day. Mitigation: log remaining due count each tick so the shortfall is visible; revisit tick fan-out only then.
- [Clock/DST edge] → local-date boundary shifts under DST or server moves; a site could get 0 or 2 slots on that day. Mitigation: accepted as negligible for daily form checks; UTC was offered and rejected.
- [Browser-launch failure records nothing] → if Chromium itself fails before the check starts, no row is written and the site stays due (retried next hour). Mitigation: this is the desired behavior — only a started check consumes the slot; log the launch error.
- [Manual runs consume cron slots] → a daytime debug run without `--force` eats that site's daily slot. Mitigation: documented in README; `--force` exists precisely for debugging.

## Migration Plan

1. Deploy new `run.py`; `executions.db` is created on first run (no migration — greenfield file).
2. Point hourly cron at `python run.py`; the first ticks backfill one row per site (one per tick), then settle into steady state.
3. Rollback: revert `run.py`, delete `executions.db`; behavior returns to run-all with no residue.
