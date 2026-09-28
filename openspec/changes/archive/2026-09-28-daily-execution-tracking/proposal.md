## Why

Every `python run.py` invocation currently submits **all** contact forms, so an hourly cron would spam client sites with real test messages 24 times a day. To run safely on a schedule, the runner must execute at most one check per site per day while keeping a queryable record of what ran.

## What Changes

- `run.py` executes **exactly one** due check per invocation instead of all discovered checks.
- A check is due when it has **no recorded execution for the current local calendar day**; otherwise it is skipped.
- Among due checks, the one with the **oldest last execution** (never-run first) is picked.
- A `FAIL` consumes the day's slot like a `PASS` — no same-day retries.
- Each execution is recorded in a gitignored stdlib-`sqlite3` database (`executions.db`) with site, day, status, duration, and error.
- A `--force [site]` flag bypasses the once-per-day guard for same-day debugging reruns (overwrites today's row).
- When nothing is due, the runner logs it, sends no email, and exits `0`.
- Failure alerting, screenshots, and exit-code semantics are otherwise unchanged; the browser launches only when a check is selected.
- `README.md` and `.gitignore` updated for the new behavior and database file.

## Capabilities

### New Capabilities

- `execution-tracking`: persistent per-site execution log (SQLite), once-per-day skip guard on local calendar date, least-recently-run selection of the single check to run, and `--force` manual override.

### Modified Capabilities

- `central-runner`: invocation semantics change from "run all discovered checks" to "run the single oldest-due check (or nothing when all ran today)". Discovery, browser isolation, continue-on-error within the run, and exit codes keep their meaning for the executed subset.

## Impact

- `run.py` — selection flow, new `sqlite3` persistence layer, `--force` CLI arg; no changes to `checks/*` contract.
- New gitignored artifact `executions.db` alongside `failures/`; `.gitignore` and `README.md` updated.
- Cron (external, out of scope) can safely tick hourly: idle ticks exit `0` silently; the project supports up to 24 sites before daily starvation.
