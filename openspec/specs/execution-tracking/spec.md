# execution-tracking Specification

## Requirements
### Requirement: Persistent execution log
The runner SHALL record every executed check in a stdlib-`sqlite3` database file (`executions.db`, gitignored, stored next to `run.py`) with one row per site per local-calendar day containing site, day (`YYYY-MM-DD` local), status (`pass`|`fail`), duration in seconds, error text (empty on pass), and start timestamp (local ISO). The table SHALL enforce `PRIMARY KEY(site, day)` so a double execution for the same site and day is structurally impossible, and recording SHALL use upsert semantics (a forced rerun overwrites today's row).

#### Scenario: Passing check is recorded
- **WHEN** site `granadago` passes on 2026-09-28
- **THEN** `executions` contains one row `('granadago', '2026-09-28', 'pass', <duration>, '', <started_at>)`

#### Scenario: Failing check is recorded with error
- **WHEN** site `granadago` fails on 2026-09-28 with a timeout error
- **THEN** `executions` contains one row with status `fail` and the error text naming the failure

#### Scenario: Database is created on first run
- **WHEN** `run.py` starts and `executions.db` does not exist
- **THEN** the runner creates it (including the table) before selecting a check

### Requirement: Once-per-day skip guard
The runner SHALL skip any discovered site that already has an execution row dated today (local calendar date), regardless of whether that row's status is `pass` or `fail`. A failed execution consumes the day's slot exactly like a passed one — there are no same-day retries through the normal path.

#### Scenario: Already-run site is skipped
- **WHEN** `granadago` has a row dated today and `run.py` starts without flags
- **THEN** `granadago` is not executed in this invocation

#### Scenario: Failure does not reopen the slot
- **WHEN** `granadago` failed earlier today and `run.py` starts again without flags
- **THEN** `granadago` remains skipped until the next local-calendar day

#### Scenario: Day rollover reopens all slots
- **WHEN** the local calendar date advances and `run.py` starts
- **THEN** every discovered site is due again

### Requirement: Least-recently-run single selection
The runner SHALL execute exactly one check per invocation: among due sites (no row dated today), it SHALL pick the one with the oldest last execution, with never-executed sites first. Discovery of new sites requires no runner edits — a new `checks/<site>.py` is due immediately and wins selection until it has run.

#### Scenario: Oldest due site runs
- **WHEN** sites A (last ran 3 days ago) and B (last ran yesterday) are both due
- **THEN** only A executes in this invocation

#### Scenario: New site runs first
- **WHEN** a new `checks/acme.py` is added and existing sites already ran today
- **THEN** the next invocation executes `acme`

#### Scenario: Nothing due means silent success
- **WHEN** every discovered site has a row dated today
- **THEN** the runner executes nothing, logs that all sites already ran today, sends no email, and exits `0`

### Requirement: Force override for debugging
The runner SHALL accept a `--force [site]` flag that bypasses the once-per-day guard: with a site name it executes that discovered site regardless of today's row; bare `--force` executes the normal least-recently-run pick ignoring the date guard. The forced execution SHALL overwrite today's row for that site, and a forced failure SHALL follow the standard failure path (screenshot, failure email, non-zero exit).

#### Scenario: Forced rerun of an already-run site
- **WHEN** `granadago` already ran today and the operator runs `python run.py --force granadago`
- **THEN** `granadago` executes again and today's row is replaced with the new result

#### Scenario: Forced run of an unknown site fails clearly
- **WHEN** the operator runs `python run.py --force nosuchsite`
- **THEN** the runner exits non-zero with an error naming the unknown site and records nothing
