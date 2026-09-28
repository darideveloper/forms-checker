#!/usr/bin/env python3
import glob
import importlib
import mimetypes
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

CHECKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checks")
FAILURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failures")

SMTP_KEYS = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "ALERT_TO", "ALERT_FROM"]


def discover_checks():
    return sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(CHECKS_DIR, "*.py"))
        if not os.path.basename(p).startswith("_")
    )


def send_alert(failures):
    missing = [k for k in SMTP_KEYS if not os.getenv(k)]
    if missing:
        print(f"Cannot send alert email, missing env keys: {', '.join(missing)} (see .env.example).")
        return
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    msg = EmailMessage()
    msg["Subject"] = f"Contact form check failed: {', '.join(n for n, _, _ in failures)}"
    msg["From"] = os.environ["ALERT_FROM"]
    msg["To"] = os.environ["ALERT_TO"]
    msg.set_content(
        "Failed contact form checks:\n\n"
        + "\n\n".join(f"- {name}: {err}\n  screenshot: {shot}" for name, err, shot in failures)
    )
    for _, _, shot in failures:
        if shot and os.path.exists(shot):
            ctype, _ = mimetypes.guess_type(shot)
            maintype, subtype = (ctype or "image/png").split("/", 1)
            with open(shot, "rb") as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(shot))
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
            if os.environ["SMTP_USER"]:
                s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            if port == 587:
                s.starttls(context=ssl.create_default_context())
            if os.environ["SMTP_USER"]:
                s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)


def main():
    headless = os.getenv("HEADLESS", "true").lower() not in ("0", "false", "no")
    os.makedirs(FAILURES_DIR, exist_ok=True)
    failures = []
    passed = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=headless)
        for name in discover_checks():
            context = None
            page = None
            try:
                module = importlib.import_module(f"checks.{name}")
                check = getattr(module, "check", None)
                if check is None:
                    raise AttributeError(f"checks/{name}.py has no 'check(page)' function")
                context = browser.new_context(viewport={"width": 1280, "height": 720})
                page = context.new_page()
                try:
                    check(page)
                finally:
                    context.close()
                    context = None
            except Exception as e:  # continue-on-error
                shot = os.path.join(FAILURES_DIR, f"{name}.png")
                try:
                    if page is not None:
                        page.screenshot(path=shot)
                    else:
                        shot = ""
                except Exception:
                    shot = ""
                finally:
                    if context is not None:
                        context.close()
                failures.append((name, f"{type(e).__name__}: {e}", shot if shot and os.path.exists(shot) else ""))
                print(f"FAIL {name}: {type(e).__name__}: {e}")
            else:
                passed.append(name)
                print(f"PASS {name}")
        browser.close()
    print(f"\n{len(passed)} passed, {len(failures)} failed.")
    if failures:
        send_alert(failures)
        sys.exit(1)


if __name__ == "__main__":
    main()
