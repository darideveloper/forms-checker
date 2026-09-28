## 1. Implement inline + attached screenshots

- [x] 1.1 Rewrite `send_alert` in `run.py` to build `multipart/mixed` → `multipart/related` → `multipart/alternative` with an HTML body using `cid:` inline images and the same PNGs as attachments
- [x] 1.2 Verify in-memory message structure (mixed/related/alternative, `cid` inline part, attachment part)
- [x] 1.3 Live failing run: confirm inline rendering + attachment in the received email

## 2. Docs

- [x] 2.1 Update `README.md` failure-alerts section and `AGENTS.md` alerting line to "inline + attached"
