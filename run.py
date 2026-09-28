#!/usr/bin/env python3
import glob
import importlib
import os
import smtplib
import ssl
import sys
import time
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

CHECKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checks")
FAILURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failures")

SMTP_KEYS = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "ALERT_TO", "ALERT_FROM"]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def discover_checks():
    return sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(CHECKS_DIR, "*.py"))
        if not os.path.basename(p).startswith("_")
    )


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
    headless = os.getenv("HEADLESS", "true").lower() not in ("0", "false", "no")
    os.makedirs(FAILURES_DIR, exist_ok=True)
    failures = []
    passed = []
    sites = discover_checks()
    total = len(sites)
    log(f"Starting contact form checks ({total} site{'s' if total != 1 else ''} found).")
    started = time.monotonic()
    log(f"Launching Chrome (headless={headless})...")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=headless)
        for i, name in enumerate(sites, 1):
            context = None
            page = None
            log(f"({i}/{total}) Checking {name}...")
            site_started = time.monotonic()
            shot = os.path.join(FAILURES_DIR, f"{name}.png")
            try:
                module = importlib.import_module(f"checks.{name}")
                check = getattr(module, "check", None)
                if check is None:
                    raise AttributeError(f"checks/{name}.py has no 'check(page)' function")
                context = browser.new_context(viewport={"width": 1280, "height": 720})
                page = context.new_page()
                try:
                    check(page)
                except Exception:
                    try:
                        page.screenshot(path=shot)
                    except Exception as shot_e:
                        log(f"  Could not save screenshot: {type(shot_e).__name__}: {shot_e}")
                        shot = ""
                    raise
                finally:
                    context.close()
                    context = None
            except Exception as e:  # continue-on-error
                if not (shot and os.path.exists(shot)):
                    shot = ""
                if context is not None:
                    context.close()
                failures.append((name, f"{type(e).__name__}: {e}", shot if shot and os.path.exists(shot) else ""))
                log(f"  FAIL {name} ({time.monotonic() - site_started:.1f}s): {type(e).__name__}: {e}")
                if shot and os.path.exists(shot):
                    log(f"  Screenshot saved: {shot}")
            else:
                passed.append(name)
                log(f"  PASS {name} ({time.monotonic() - site_started:.1f}s)")
        browser.close()
    log(f"{len(passed)} passed, {len(failures)} failed in {time.monotonic() - started:.1f}s.")
    if failures:
        log(f"Sending failure alert to {os.getenv('ALERT_TO', '(no ALERT_TO set)')}...")
        send_alert(failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
