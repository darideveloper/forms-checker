#!/usr/bin/env bash
# Show the last N executions from executions.db (default 10).
# Usage: ./last-runs.sh [N]
set -euo pipefail

N="${1:-10}"
if ! [[ "$N" =~ ^[0-9]+$ ]]; then
  echo "Usage: $0 [N]  (N = number of rows, default 10)" >&2
  exit 2
fi

DB="$(cd "$(dirname "$0")" && pwd)/executions.db"
command -v sqlite3 >/dev/null || { echo "sqlite3 not found. Install it: sudo apt install sqlite3" >&2; exit 1; }
[[ -f "$DB" ]] || { echo "No database yet: $DB (run ./run.py first)" >&2; exit 1; }

sqlite3 -header -box -readonly "$DB" \
  "SELECT site, day, status, printf('%.1fs', duration_s) AS duration, substr(replace(error, char(10), ' '), 1, 70) AS error, started_at FROM executions ORDER BY started_at DESC LIMIT $N;"
