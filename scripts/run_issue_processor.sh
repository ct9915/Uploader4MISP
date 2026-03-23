#!/usr/bin/env bash
# run_issue_processor.sh — wrapper called by cron
# Loads .env, activates the Python venv, then runs issue_processor.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$REPO_DIR/logs/issue_processor.log"

mkdir -p "$REPO_DIR/logs"

# ── Load environment variables from .env ─────────────────────────────────────
ENV_FILE="$REPO_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

# ANTHROPIC_API_KEY must be present
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: ANTHROPIC_API_KEY is not set." | tee -a "$LOG_FILE"
    exit 1
fi

# ── Activate virtual environment ──────────────────────────────────────────────
if [[ -f "$REPO_DIR/venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$REPO_DIR/venv/bin/activate"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') WARNING: venv not found, using system Python." | tee -a "$LOG_FILE"
fi

# ── Run the processor, append output to log ───────────────────────────────────
echo "$(date '+%Y-%m-%d %H:%M:%S') === Starting issue_processor ===" >> "$LOG_FILE"
python "$SCRIPT_DIR/issue_processor.py" 2>&1 | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') === Done ===" >> "$LOG_FILE"
