# project-hygiene Specification

## Purpose
TBD - created by archiving change forms-checker-suite. Update Purpose after archive.
## Requirements
### Requirement: Env template
The repo SHALL provide `.env.example` documenting `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `ALERT_TO`, `ALERT_FROM`, and `HEADLESS`, and `.env` SHALL be gitignored.

#### Scenario: New operator setup
- **WHEN** an operator copies `.env.example` to `.env` and fills the values
- **THEN** `run.py` picks up SMTP, alert addresses, and headless flag without code changes

### Requirement: Minimal dependencies and ignores
`requirements.txt` SHALL contain only `playwright` and `python-dotenv`, and `.gitignore` SHALL ignore `.env`, `failures/`, `venv/`, `__pycache__/`, and `*.pyc`, preserve the `openspec/changes/*` + `!openspec/changes/archive/` rules, and SHALL NOT reference `clients.yaml`, `docs/`, or a blanket `.*/` rule.

#### Scenario: Clean install and status
- **WHEN** installing from `requirements.txt` or running `git status`
- **THEN** no SAT/client artifacts (`pyyaml`, `clients.yaml`) are required and no secrets or failure screenshots appear as untracked noise

### Requirement: README and AGENTS.md documentation
The repo SHALL include `README.md` (setup, env table, `python run.py`, add-a-site recipe, failure-email and screenshot behavior) and `AGENTS.md` (structure, `check(page)` contract, headless default, browser rules) with a rule that README stays in sync with behavior changes, and SHALL contain zero references to the SAT invoice portal, SAT credentials/e.firma, or `clients.yaml` SAT client config (generic English "client sites" is allowed).

#### Scenario: Docs stay accurate
- **WHEN** runner flags, env keys, or the check contract change
- **THEN** README and AGENTS.md are updated in the same change with no SAT/invoice/client mentions remaining

