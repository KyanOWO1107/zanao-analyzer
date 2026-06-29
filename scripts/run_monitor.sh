#!/usr/bin/env bash
set -euo pipefail

LIMIT="${LIMIT:-20}"
SEND_LIMIT="${SEND_LIMIT:-1}"
STATE="${STATE:-data/monitor_state.db}"
ENV_FILE="${ENV_FILE:-.env}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/monitor.log"

mkdir -p "$LOG_DIR"

cd "$PROJECT_ROOT"
{
  printf '[%s] start\n' "$(date '+%Y-%m-%d %H:%M:%S')"
  python -m zanao_monitor.cli run-mini-monitor --env "$ENV_FILE" --limit "$LIMIT" --send --send-limit "$SEND_LIMIT" --state "$STATE"
  printf '[%s] end\n' "$(date '+%Y-%m-%d %H:%M:%S')"
} >> "$LOG_FILE" 2>&1
