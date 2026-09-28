## Why

Contact forms on client sites break silently (plugin updates, theme changes, SMTP outages). Today there is only one ad-hoc script (`test_script.py`, headed, single site, no alerting). A small shared suite with one manual entrypoint and failure-only email alerts catches breakage without daily manual checks.

## What Changes

- Add `checks/` package: each site is one module exposing `check(page)` that fills with its own sender data, really submits, and asserts the visible success message.
- Add `run.py` manual entrypoint: auto-discovers `checks/*.py`, launches one headless Chrome (`channel="chrome"`), uses a fresh browser context per site, runs sequentially, continues past failures, saves failure screenshots, sends one summary email only when at least one check fails, exits non-zero on failure.
- Add `.env` / `.env.example` with generic SMTP settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `ALERT_TO`, `ALERT_FROM`) and `HEADLESS` flag.
- Migrate `test_script.py` (granadago.com) into `checks/granadago.py` under the new contract, then delete the old file.
- Hygiene: remove SAT-invoice leftovers — drop `clients.yaml` reference from `.gitignore`, fix `.*/` over-ignore (keep `openspec/changes` archival rules, add `venv/`), drop `pyyaml` from `requirements.txt` (keep `playwright`, `python-dotenv`), ignore `.env` + `failures/` screenshots. "Clients" here means SAT `clients.yaml` config, not generic "client sites".
- Add `README.md` (setup, env table, run, add-a-site recipe, failure-email behavior) and `AGENTS.md` (structure, `check(page)` contract, headless default, README-sync rule).

## Capabilities

### New Capabilities

- `form-checks`: Per-site check contract and `checks/` collection. Covers module layout, `check(page)` signature, per-site sender data, real-submit behavior, success-message assertion via `expect`.
- `central-runner`: Discovery (`checks/*.py` glob), single browser lifecycle, fresh context per site, sequential execution, continue-on-error, `failures/<site>.png` screenshots, non-zero exit on failure, manual `python run.py` invocation.
- `failure-alerting`: Failure-only single summary email via stdlib `smtplib` (auto SSL/STARTTLS by port); generic SMTP `.env` config; contents (failed sites, error text, attached `failures/<site>.png` screenshots); no email on full pass.
- `project-hygiene`: Env template, dependency list, gitignore rules, README + AGENTS.md docs with keep-in-sync rule, removal of SAT/client references.

### Modified Capabilities

- None (greenfield inside `forms-checkers/`; `sat-invoices/` untouched).

## Impact

- Scoped to `forms-checkers/` only. No changes to parent `playwright-automations/` tooling or `sat-invoices/`.
- Runtime deps: `playwright`, `python-dotenv` (Chrome via `channel="chrome"` required). No new third-party email/config deps.
- Operators run `python run.py` manually; on failure they receive one email and the process exits non-zero. Each run sends real test messages to the checked sites.
