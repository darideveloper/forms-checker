# failure-alerting Specification

## Purpose
TBD - created by archiving change forms-checker-suite. Update Purpose after archive.
## Requirements
### Requirement: Failure-only summary email
The runner SHALL send exactly one summary email via stdlib `smtplib` when at least one check fails, and SHALL send no email when all checks pass.

#### Scenario: Failures trigger one email
- **WHEN** one or more checks fail
- **THEN** a single email is sent to `ALERT_TO` from `ALERT_FROM` listing each failed site with its error text and attaching that site's `failures/<site>.png` screenshot

#### Scenario: Full pass sends nothing
- **WHEN** all checks pass
- **THEN** no SMTP connection is opened and no email is sent

### Requirement: Generic SMTP configuration
Alerting SHALL read `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `ALERT_TO`, `ALERT_FROM` from the environment (`.env` supported) and auto-select security by port (465 = implicit SSL, 587 = STARTTLS, other ports = plain).

#### Scenario: Custom host delivery
- **WHEN** valid custom SMTP settings are provided and a check fails
- **THEN** the summary email is delivered through that host using the port-appropriate security

#### Scenario: Missing email config fails fast
- **WHEN** a run has failures but required SMTP keys are missing
- **THEN** the runner reports the missing key names clearly instead of sending a partial email

