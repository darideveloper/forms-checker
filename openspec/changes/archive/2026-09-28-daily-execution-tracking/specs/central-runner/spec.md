## MODIFIED Requirements

### Requirement: Auto-discovery of checks
`run.py` SHALL discover check modules by globbing `checks/*.py` (excluding `__init__.py` and `_*.py`) and invoking the selected module's `check(page)` function. Discovery defines the candidate set; the execution-tracking selection rules decide which single candidate runs in a given invocation.

#### Scenario: New site picked up without runner edits
- **WHEN** a new `checks/acme.py` with a `check` function is added
- **THEN** the next `python run.py` considers it alongside existing checks and, having never run, selects it first

#### Scenario: Missing check function is a site failure
- **WHEN** the selected module has no `check` attribute
- **THEN** that site is recorded as failed with a clear missing-contract error and the execution is logged as `fail` for today

### Requirement: Browser lifecycle and isolation
The runner SHALL launch one Chromium (`channel="chrome"`, headless per `HEADLESS`, default true) only when a check is selected for execution, and execute that single check in a fresh `new_context(viewport 1280x720)` + `new_page`, closing the context afterwards. When no check is due, the runner SHALL NOT launch a browser.

#### Scenario: Single isolated run
- **WHEN** one check is selected in an invocation
- **THEN** it runs in its own fresh context and the context is closed even on failure

#### Scenario: No browser when nothing is due
- **WHEN** every discovered site already ran today
- **THEN** the invocation exits `0` without launching Chromium

### Requirement: Continue-on-error with screenshots and exit code
The runner SHALL save `failures/<site>.png` when the executed check fails, print a per-run pass/fail summary, and exit non-zero when the executed check failed (zero when it passed or when nothing was due). Screenshots keep overwriting that site's file each run.

#### Scenario: Failure produces screenshot, alert, and non-zero exit
- **WHEN** the selected site fails
- **THEN** its screenshot is saved, a failure email is sent per the failure-alerting rules, the failure is logged as today's execution, and the exit code is non-zero

#### Scenario: Skipped run stays silent and green
- **WHEN** no site is due
- **THEN** no email is sent and the exit code is zero
