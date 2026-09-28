# Forms Checkers

Playwright checks that verify contact forms on client websites are working. Each run really submits every form and asserts the success message. One summary email is sent only when something fails. Pure automation scripts — no tests, no lint, no typecheck.

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
python run.py
```

- Discovers every `checks/*.py` (except `__init__.py` and `_*.py` helpers) and runs them sequentially, one browser, fresh 1280×720 context per site.
- Continues past failures; prints `PASS`/`FAIL` per site plus a `N passed, M failed` summary.
- Exit code is `0` when all pass, `1` when any fail.
- Every run sends real test messages to the checked sites. Runs are manual, so you control the frequency.
- Set `HEADLESS=false` to watch a run headed while debugging selectors.

## Failure alerts and screenshots

- No email is sent when all checks pass.
- When at least one check fails, exactly one summary email goes to `ALERT_TO` listing each failed site with its error; each site's `failures/<site>.png` screenshot is shown inline in the email body and also attached as a downloadable file.
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
3. Run `python run.py` to verify. No runner edits needed — discovery picks the file up automatically.
