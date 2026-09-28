# central-runner Specification

## Purpose
TBD - created by archiving change forms-checker-suite. Update Purpose after archive.
## Requirements
### Requirement: Auto-discovery of checks
`run.py` SHALL discover check modules by globbing `checks/*.py` (excluding `__init__.py` and `_*.py`) and invoking each module's `check(page)` function.

#### Scenario: New site picked up without runner edits
- **WHEN** a new `checks/acme.py` with a `check` function is added
- **THEN** the next `python run.py` executes it alongside existing checks

#### Scenario: Missing check function is a site failure
- **WHEN** a discovered module has no `check` attribute
- **THEN** that site is recorded as failed with a clear missing-contract error and the run continues

### Requirement: Browser lifecycle and isolation
The runner SHALL launch one Chromium (`channel="chrome"`, headless per `HEADLESS`, default true) and execute each site in a fresh `new_context(viewport 1280x720)` + `new_page`, closing the context afterwards.

#### Scenario: Sequential isolated runs
- **WHEN** two or more checks run in one invocation
- **THEN** each runs in its own context sequentially and contexts are closed even on failure

### Requirement: Continue-on-error with screenshots and exit code
The runner SHALL run all discovered checks even after failures, save `failures/<site>.png` for each failure, print a per-site pass/fail summary, and exit non-zero when any check failed (zero when all pass).

#### Scenario: One failure does not abort others
- **WHEN** site A fails and site B would pass
- **THEN** site B still runs, site A gets a screenshot, the summary lists both, and the exit code is non-zero

