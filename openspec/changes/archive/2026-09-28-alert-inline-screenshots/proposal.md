## Why

Failure alert emails currently attach the `failures/<site>.png` screenshot as a bare file. Recipients must download it to see what went wrong. Rendering the screenshot inline in the email body (while still attaching it) makes failures readable at a glance.

## What Changes

- `send_alert` builds a `multipart/mixed` → `multipart/related` → `multipart/alternative` message: `text/plain` fallback plus an HTML body that shows each failed site's screenshot inline via `cid:`.
- Each PNG is included both inline (`Content-ID`, `Content-Disposition: inline`) and as a downloadable attachment (`Content-Disposition: attachment`).
- No new dependencies (stdlib `email.mime.*` + `smtplib`); subject/from/to and the failure-only trigger are unchanged.
- Update `README.md` and `AGENTS.md` alert-wording to describe inline + attached screenshots.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `failure-alerting`: the summary email now also renders screenshots inline in an HTML body, not just as attachments.

## Impact

- `run.py` `send_alert` only. Duplicated PNG bytes roughly double message size (a 691 KB screenshot → ~1.4 MB email), acceptable under normal SMTP limits.
- Still stdlib-only, one email on failure, silence on full pass.
