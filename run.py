#!/usr/bin/env python3
import argparse
import glob
import importlib
import os
import smtplib
import sqlite3
import ssl
import sys
import time
from datetime import date, datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

CHECKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checks")
FAILURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failures")
EXECUTIONS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "executions.db")

SMTP_KEYS = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "ALERT_TO", "ALERT_FROM"]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def discover_checks():
    return sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(CHECKS_DIR, "*.py"))
        if not os.path.basename(p).startswith("_")
    )


def init_db():
    con = sqlite3.connect(EXECUTIONS_DB)
    con.execute(
        "CREATE TABLE IF NOT EXISTS executions ("
        "site TEXT, day TEXT, status TEXT, duration_s REAL, error TEXT, started_at TEXT, "
        "PRIMARY KEY(site, day))"
    )
    con.commit()
    return con


def today_iso():
    return date.today().isoformat()


def ran_today(con, site, today):
    return (
        con.execute("SELECT 1 FROM executions WHERE site = ? AND day = ?", (site, today)).fetchone()
        is not None
    )


def record(con, site, day, status, duration, error, started_at):
    con.execute(
        "INSERT INTO executions (site, day, status, duration_s, error, started_at)"
        " VALUES (?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(site, day) DO UPDATE SET"
        " status = excluded.status, duration_s = excluded.duration_s,"
        " error = excluded.error, started_at = excluded.started_at",
        (site, day, status, duration, error, started_at),
    )
    con.commit()


def pick(sites, con, today, ignore_guard=False):
    """Return (name, remaining) for the single check to run, oldest first.

    `remaining` is how many other sites are still due after this one.
    Returns (None, 0) when nothing is due.
    """
    if not sites:
        return None, 0
    placeholders = ",".join("?" for _ in sites)
    hist = {}
    for site, day, last in con.execute(
        "SELECT site, day, MAX(started_at) FROM executions"
        f" WHERE site IN ({placeholders}) GROUP BY site, day",
        tuple(sites),
    ):
        hist.setdefault(site, []).append((day, last))

    def last_any(s):
        return max((last for _, last in hist.get(s, []) if last is not None), default=None)

    def ran(s):
        return any(day == today for day, _ in hist.get(s, []))

    normal_due = [s for s in sites if not ran(s)]
    candidates = sites if ignore_guard else normal_due
    if not candidates:
        return None, 0
    ranked = sorted(candidates, key=lambda s: (last_any(s) is not None, last_any(s) or "", s))
    name = ranked[0]
    return name, sum(1 for s in normal_due if s != name)


def send_alert(failures):
    missing = [k for k in SMTP_KEYS if not os.getenv(k)]
    if missing:
        log(f"Cannot send alert email, missing env keys: {', '.join(missing)} (see .env.example).")
        return
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])

    text_body = "Failed contact form checks:\n\n" + "\n\n".join(
        f"- {name}: {err}\n  screenshot: {shot}" for name, err, shot in failures
    )
    html_parts = []
    for name, err, shot in failures:
        img = f'<img src="cid:{name}" alt="{name} screenshot" style="max-width:100%;border:1px solid #ccc">' if shot and os.path.exists(shot) else "<em>no screenshot</em>"
        html_parts.append(f"<h3>{name}</h3><pre>{err}</pre>{img}")
    html_body = "<html><body>" + "".join(html_parts) + "</body></html>"

    root = MIMEMultipart("mixed")
    root["Subject"] = f"Contact form check failed: {', '.join(n for n, _, _ in failures)}"
    root["From"] = os.environ["ALERT_FROM"]
    root["To"] = os.environ["ALERT_TO"]

    related = MIMEMultipart("related")
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(text_body, "plain", "utf-8"))
    alt.attach(MIMEText(html_body, "html", "utf-8"))
    related.attach(alt)
    for name, _, shot in failures:
        if shot and os.path.exists(shot):
            with open(shot, "rb") as f:
                data = f.read()
            inline = MIMEImage(data, "png")
            inline.add_header("Content-ID", f"<{name}>")
            inline.add_header("Content-Disposition", "inline", filename=os.path.basename(shot))
            related.attach(inline)
    root.attach(related)

    for _, _, shot in failures:
        if shot and os.path.exists(shot):
            with open(shot, "rb") as f:
                att = MIMEImage(f.read(), "png")
            att.add_header("Content-Disposition", "attachment", filename=os.path.basename(shot))
            root.attach(att)

    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
            if os.environ["SMTP_USER"]:
                s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(root)
    else:
        with smtplib.SMTP(host, port) as s:
            if port == 587:
                s.starttls(context=ssl.create_default_context())
            if os.environ["SMTP_USER"]:
                s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(root)
    log(f"Alert sent to {os.environ['ALERT_TO']}.")


def main():
    parser = argparse.ArgumentParser(description="Run one due contact-form check (at most once per site per day).")
    parser.add_argument(
        "--force",
        nargs="?",
        const=True,
        default=False,
        metavar="SITE",
        help="bypass the once-per-day guard: with SITE rerun that site, bare rerun the normal pick",
    )
    args = parser.parse_args()

    headless = os.getenv("HEADLESS", "true").lower() not in ("0", "false", "no")
    os.makedirs(FAILURES_DIR, exist_ok=True)
    con = init_db()
    today = today_iso()
    sites = discover_checks()
    log(f"Starting contact form checks ({len(sites)} site{'s' if len(sites) != 1 else ''} found).")

    if isinstance(args.force, str):
        if args.force not in sites:
            log(f"Unknown site '{args.force}' (discovered: {', '.join(sites) or 'none'}).")
            con.close()
            sys.exit(2)
        name = args.force
        remaining = sum(1 for s in sites if s != name and not ran_today(con, s, today))
        log(f"--force: running {name} (guard bypassed).")
    else:
        name, remaining = pick(sites, con, today, ignore_guard=args.force is True)
        if name is None:
            log(f"All {len(sites)} site(s) already ran today ({today}) — nothing to do.")
            con.close()
            return

    log(f"Checking {name}... ({remaining} other site(s) still due after this.)")
    started = time.monotonic()
    site_started = time.monotonic()
    started_at = datetime.now().isoformat(timespec="seconds")
    shot = os.path.join(FAILURES_DIR, f"{name}.png")

    try:
        module = importlib.import_module(f"checks.{name}")
        check = getattr(module, "check", None)
        if check is None:
            raise AttributeError(f"checks/{name}.py has no 'check(page)' function")
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        record(con, name, today, "fail", time.monotonic() - site_started, err, started_at)
        con.close()
        log(f"  FAIL {name}: {err}")
        send_alert([(name, err, "")])
        sys.exit(1)

    log(f"Launching Chrome (headless={headless})...")
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(channel="chrome", headless=headless)
                context = browser.new_context(viewport={"width": 1280, "height": 720})
                page = context.new_page()
            except Exception as e:
                # Launch failure: alert but record nothing, the site stays due.
                err = f"{type(e).__name__}: {e}"
                con.close()
                log(f"  ERROR {name} before check started: {err} (stays due)")
                send_alert([(name, err, "")])
                sys.exit(1)
            try:
                check(page)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
                try:
                    page.screenshot(path=shot)
                except Exception as shot_e:
                    log(f"  Could not save screenshot: {type(shot_e).__name__}: {shot_e}")
                    shot = ""
                if not (shot and os.path.exists(shot)):
                    shot = ""
                record(con, name, today, "fail", time.monotonic() - site_started, err, started_at)
                con.close()
                log(f"  FAIL {name} ({time.monotonic() - site_started:.1f}s): {err}")
                if shot:
                    log(f"  Screenshot saved: {shot}")
                log(f"Sending failure alert to {os.getenv('ALERT_TO', '(no ALERT_TO set)')}...")
                send_alert([(name, err, shot)])
                sys.exit(1)
            finally:
                context.close()
            browser.close()
    except SystemExit:
        raise
    except Exception as e:
        # playwright startup failure: record nothing, the site stays due.
        err = f"{type(e).__name__}: {e}"
        con.close()
        log(f"  ERROR {name} before check started: {err} (stays due)")
        sys.exit(1)

    record(con, name, today, "pass", time.monotonic() - site_started, "", started_at)
    con.close()
    log(f"  PASS {name} ({time.monotonic() - site_started:.1f}s)")
    log(f"1 passed, 0 failed in {time.monotonic() - started:.1f}s.")


if __name__ == "__main__":
    main()
