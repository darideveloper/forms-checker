# Forms Checkers

Playwright-based contact-form monitoring for client websites.

## Project Structure

- `run.py` — entrypoint: loads `.env`, discovers `checks/*.py`, launches one headless Chrome, runs each check in a fresh context sequentially, sends one failure-only email, exits non-zero on failure
- `checks/` — one module per site exposing `check(page)` with its own sender data; `checks/granadago.py` is the reference implementation
- `.env` / `.env.example` — SMTP settings, alert addresses, `HEADLESS` flag (gitignored `.env`)
- `failures/` — per-site failure screenshots, overwritten each run (gitignored)
- `README.md` — project documentation (setup, env table, run, add-a-site recipe, alert/screenshot behavior). **Must be kept in sync with the codebase**: whenever the runner flags, env keys, or the check contract change, update the README in the same change.

## Key facts

- **Check contract**: `check(page)` — fills with the script's own sender data, really submits, asserts the visible success message with `expect(...).to_be_visible(timeout=15000)`. Checks never launch browsers or read env themselves; they raise on failure.
- **Browser**: Chromium via `playwright.chromium.launch(channel="chrome", headless=HEADLESS)` — requires Chrome installed; `HEADLESS` defaults to `true`, set `false` for headed debugging.
- **Discovery**: glob `checks/*.py`, skip `__init__.py` and `_*.py`; a module without `check` is recorded as that site's failure.
- **Alerting**: stdlib `smtplib` only; one email on failure (failed sites + errors + screenshots shown inline via `cid:` and attached as files), silence on full pass; security auto-selected by port (465 SSL / 587 STARTTLS / else plain).
- **No tests, no lint, no typecheck** — pure automation scripts.

## OpenSpec workflow

Change management via OpenSpec experimental workflow:

- `/opsx-propose <name>` — create change with proposal/design/tasks
- `/opsx-apply` — implement tasks from a change
- `/opsx-verify` — verify implementation matches artifacts
- `/opsx-archive` — archive completed change
- `/opsx-explore` — explore mode for thinking

Skills in `.opencode/skills/`, commands in `.opencode/commands/`.
