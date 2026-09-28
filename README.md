# Forms Checkers

Playwright checks that verify contact forms on client websites are working. Each run really submits a form and asserts the success message. Safe to run on an hourly cron: each site runs at most once per local-calendar day, one site per invocation. One summary email is sent only when something fails. Pure automation scripts — no tests, no lint, no typecheck.

## Requirements

- Python 3
- Google Chrome installed (the runner launches `channel="chrome"`)

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Fill in `.env`:

| Key | Purpose |
|---|---|
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | SMTP port (465 = implicit SSL, 587 = STARTTLS, else plain) |
| `SMTP_USER` | SMTP login user |
| `SMTP_PASS` | SMTP login password |
| `ALERT_TO` | Where failure alerts go |
| `ALERT_FROM` | Sender address for failure alerts |
| `HEADLESS` | `true` (default) or `false` for headed debugging |

## Running

```bash
python run.py [--force [SITE]]
```

- Discovers every `checks/*.py` (except `__init__.py` and `_*.py` helpers) but runs exactly **one** due check per invocation: sites that already ran today (local date) are skipped, and among the rest the least-recently-run one (never-run first) is picked.
- When nothing is due, the runner logs it, sends no email, launches no browser, and exits `0` — so an hourly cron stays quiet after all sites ran.
- A `FAIL` consumes the day's slot like a `PASS`; there are no same-day retries.
- Exit code is `0` on pass or nothing-due, `1` on failure, `2` for a `--force` site name that matches nothing discovered.
- Every executed run sends a real test message to the checked site. Set `HEADLESS=false` to watch a run headed while debugging selectors.
- `python run.py --force <site>` reruns one site today ignoring the guard (overwrites today's record); bare `--force` applies the guard bypass to the normal pick. Use it for debugging selectors.
- Each execution is recorded in `executions.db` (stdlib SQLite, gitignored, next to `run.py`): one row per site per day with status, duration, and error. Query it with `sqlite3 executions.db "select * from executions order by started_at;"`.

## Failure alerts and screenshots

- No email is sent when the check passes or when nothing is due.
- When the executed check fails, exactly one summary email goes to `ALERT_TO` with its error; the site's `failures/<site>.png` screenshot is shown inline in the email body and also attached as a downloadable file.
- If SMTP keys are missing at alert time, the runner prints the missing key names instead of sending a partial email.
- `failures/` is gitignored; each run overwrites that site's screenshot.

## Adding a site

1. Create `checks/<site>.py` exposing `check(page)` with its own sender data:
   ```python
   from playwright.sync_api import expect

   NAME = "daridev"
   EMAIL = "me@darideveloper.com"
   MESSAGE = "this is a periodic check of the contact form. If you keep getting these messages, let me know asap."

   def check(page):
       page.goto("https://example.com/contact")
       page.get_by_role("textbox", name="Name").fill(NAME)
       page.get_by_role("textbox", name="Email").fill(EMAIL)
       page.get_by_role("textbox", name="Message").fill(MESSAGE)
       page.get_by_role("button", name="Send").click()
       expect(page.get_by_text("Thank you")).to_be_visible(timeout=15000)
   ```
2. Use only the passed `page` — never launch a browser inside a check. Keep the message marked as an automated check. Raise (or let `expect` raise) on failure.
3. Run `python run.py --force <site>` to verify (a plain `python run.py` skips sites that already ran today). No runner edits needed — discovery picks the file up automatically.
