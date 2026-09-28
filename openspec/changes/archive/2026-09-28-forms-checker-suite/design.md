## Context

`forms-checkers/` currently holds a single `test_script.py`: it launches headed Chrome, drives granadago.com's contact form, and asserts nothing (bare `.click()` on the success locator, no `expect`). There is no runner, no alerting, no env template, and `requirements.txt` / `.gitignore` carry SAT-template leftovers (`pyyaml`, `clients.yaml`, `docs/`, `.*/`). Decisions locked in explore: manual `python run.py` runs, real submits, failure-only email, success-message assertion, generic custom SMTP, 2–5 sites sequential, shared test identity from `.env`. `sat-invoices/` is out of scope.

## Goals / Non-Goals

**Goals:**
- One manual command runs every site check headlessly and reports pass/fail per site.
- Adding a site = adding one file under `checks/`, no registry edits.
- Exactly one summary email per run, only when something fails.
- Docs (`README.md`, `AGENTS.md`) and `.env.example` let a new operator run within minutes.

**Non-Goals:**
- No scheduling (cron/Actions), no parallel execution, no per-site config files.
- No inbox verification (cannot confirm the site owner received the message).
- No framework (pytest), no new third-party deps beyond `playwright` + `python-dotenv`.

## Decisions

- **Check contract `check(page)` over self-contained scripts.** Runner owns `sync_playwright` + browser lifecycle; checks only drive a given `Page` and raise on failure. Alternative (each script launches its own browser) was rejected: slower, duplicates launch/headless logic, can't share the failure-capture path. Each check hardcodes its own sender data (name/email/message, marked as an automated check) — no shared identity plumbing for 2–5 sites.
- **One browser, fresh context per site, sequential.** Fresh `browser.new_context(viewport=1280x720)` per check gives cookie/storage isolation without the cost of relaunching Chrome. Sequential keeps code trivial for 2–5 sites; parallel (threads + separate contexts) deferred until runtime proves painful.
- **Glob discovery (`checks/*.py`, skip `_*.py`/`__init__.py`), import `check` attribute.** No registry list to rot. A module without `check` fails that site with a clear error rather than silently skipping.
- **Continue-on-error with per-site try/except; single summary email with attachments.** Collect `(site, error)` pairs, screenshot each failure to `failures/<site>.png`, then send one `EmailMessage` via stdlib `smtplib` with the PNGs attached. Rejected per-failure emails (spam) and always-email (noise against the failures-only decision).
- **Generic SMTP over provider-specific API.** `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS` + `ALERT_TO`/`ALERT_FROM`, auto-selecting security by port (465 = implicit SSL, 587 = STARTTLS, else plain). Works with any custom host; Gmail app-password is just one instantiation. No `yagmail`/SendGrid dep.
- **`expect(success_locator).to_be_visible(timeout=15000)` as the pass bar.** Granadago's success node (`#srfm-success-message-page-327`-style id) is brittle, so each check owns its own success selector and the runner treats `TimeoutError`/assertion as failure. Bare `.click()` on the success node is banned.
- **`HEADLESS` env flag (default `true`), `channel="chrome"`.** Headed locally via `HEADLESS=false` for selector debugging; headless in normal runs.
- **Hygiene: delete `test_script.py` after migration; drop `pyyaml`; fix `.gitignore`.** `.*/` ignore would swallow future dot-dirs inconsistently and `clients.yaml`/`docs/` are SAT residue. Replace with explicit `.env`, `failures/`, `__pycache__/`, `*.pyc`.

## Risks / Trade-offs

- [Brittle success selectors] → Mitigation: each check pins its own selector with `expect` + 15s timeout; failure screenshot shows actual state.
- [Real submits spam site owners on every manual run] → Mitigation: each check's message clearly marks automated checks ("periodic check…"); runs are manual so frequency is human-controlled.
- [Custom SMTP misconfig surfaces only at send time] → Mitigation: `send_alert` checks for missing SMTP keys at alert time and reports the missing key names instead of sending a partial email.
- [One bad check can't abort the run, so a broken import helper could fail all sites] → Mitigation: shared helpers (if any) stay in one tiny `checks/_helpers.py` (glob-skipped) or inline; keep shared code near zero.
- [Screenshots accumulate] → Mitigation: `failures/` is gitignored; runner overwrites per-site file each run.
