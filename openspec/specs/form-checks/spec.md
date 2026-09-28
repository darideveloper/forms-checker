# form-checks Specification

## Purpose
TBD - created by archiving change forms-checker-suite. Update Purpose after archive.
## Requirements
### Requirement: Per-site check module contract
Each file in `checks/` (except `__init__.py` and `_*.py` helpers) SHALL expose `check(page)` which fills the site's contact form with the script's own sender data, performs a real submit, and asserts the visible success message, raising on any failure.

#### Scenario: Check passes on working form
- **WHEN** the runner calls `check(page)` against a working contact form
- **THEN** the form is submitted and the success assertion passes without raising

#### Scenario: Check raises on broken form
- **WHEN** the success message does not become visible within the timeout
- **THEN** `check` raises (assertion/timeout error) and performs no browser lifecycle calls itself

### Requirement: Per-site sender data
Each check SHALL hardcode its own sender name, email, and message (marked as an automated check) instead of reading shared identity from the environment, so each site can carry appropriate test data.

#### Scenario: Sender data lives in the check
- **WHEN** a check runs
- **THEN** the submitted name/email/message fields contain the values defined in that check module and no `TEST_*` env keys are required

### Requirement: Granadago migration
`checks/granadago.py` SHALL replicate the current `test_script.py` flow (Contacto → Nombre/Correo/Mensaje → Enviar) under the new contract with an explicit `expect` on the success message.

#### Scenario: Migrated granadago check
- **WHEN** `check(page)` runs against granadago.com with a working form
- **THEN** it navigates, submits with its own sender values, and the success locator becomes visible

