## 1. Hygiene and config foundation

- [x] 1.1 Rewrite `requirements.txt` to `playwright` + `python-dotenv` (drop `pyyaml`)
- [x] 1.2 Rewrite `.gitignore` (keep `.env` + `openspec/changes/*` with `!openspec/changes/archive/`; add `failures/`, `venv/`; remove `clients.yaml`, `docs/`, `.*/`; keep `__pycache__/`, `*.pyc`)
- [x] 1.3 Add `.env.example` with `SMTP_HOST/PORT/USER/PASS`, `ALERT_TO/FROM`, `TEST_NAME/EMAIL/MESSAGE`, `HEADLESS`
- [x] 1.4 Verify no SAT-invoice references remain (`rg -i "sat|factura|clients\.yaml|sat_invoice"` clean in repo files; generic "client sites" allowed)

## 2. Checks package

- [x] 2.1 Create `checks/__init__.py` and `checks/granadago.py` with `check(page, identity)` migrated from `test_script.py` (real submit + `expect` on success message)
- [x] 2.2 Delete `test_script.py` after migration verified

## 3. Central runner

- [x] 3.1 Implement `run.py`: load `.env`, validate required keys
- [x] 3.2 Implement glob discovery of `checks/*.py` (skip `_*.py`/`__init__.py`) with missing-`check` reported as site failure
- [x] 3.3 Implement one-browser lifecycle (`channel="chrome"`, `HEADLESS` default true), fresh 1280x720 context per site, sequential continue-on-error
- [x] 3.4 Implement `failures/<site>.png` screenshots, console summary, non-zero exit on any failure

## 4. Failure alerting

- [x] 4.1 Implement stdlib `smtplib` single-summary email (failed site, error, attach `failures/<site>.png`), failures-only, auto security by port (465 SSL / 587 STARTTLS / else plain)
- [x] 4.2 Handle missing SMTP keys with a clear fail-fast error naming the keys

## 5. Docs and verification

- [x] 5.1 Write `README.md` (setup, env table, `python run.py`, add-a-site recipe, email/screenshot behavior)
- [x] 5.2 Write `AGENTS.md` (structure, `check(page, identity)` contract, headless/browser rules, README-sync rule)
- [x] 5.3 Dry-verify: `python -m py_compile run.py checks/*.py`, `git status` shows no secrets/screenshots, `rg -i "sat|factura|clients\.yaml|sat_invoice"` clean in repo files

## 6. Scope amendment: per-site sender data (supersedes shared identity)

- [x] 6.1 Move sender data into each check (`check(page)` contract, `NAME`/`EMAIL`/`MESSAGE` constants in `checks/granadago.py`)
- [x] 6.2 Strip identity plumbing from `run.py` (`load_identity`, `TEST_*` validation, `check(page)` calls) and `TEST_*` keys from `.env.example`
- [x] 6.3 Update `README.md` / `AGENTS.md` (env table, add-a-site recipe, contract) and amend proposal/design/specs to the `check(page)` contract
