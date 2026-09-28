## MODIFIED Requirements

### Requirement: Failure-only summary email
The runner SHALL send exactly one summary email via stdlib `smtplib` when at least one check fails, and SHALL send no email when all checks pass. Each failed site's `failures/<site>.png` screenshot SHALL be shown inline in the email body and SHALL also be attached as a downloadable file.

#### Scenario: Failures trigger one email
- **WHEN** one or more checks fail
- **THEN** a single email is sent to `ALERT_TO` from `ALERT_FROM` listing each failed site with its error text, showing that site's screenshot inline in the HTML body, and attaching it as a file

#### Scenario: Screenshot renders inline and attaches
- **WHEN** the alert email is built
- **THEN** the message is multipart with an HTML body referencing each screenshot by `cid:`, and the same PNG bytes are present as a `Content-Disposition: attachment` part

#### Scenario: Full pass sends nothing
- **WHEN** all checks pass
- **THEN** no SMTP connection is opened and no email is sent
