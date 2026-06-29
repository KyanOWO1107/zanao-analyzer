#!/usr/bin/env bash
set -euo pipefail

LIMIT="${LIMIT:-20}"
SEND_LIMIT="${SEND_LIMIT:-1}"
STATE="${STATE:-data/monitor_state.db}"
ENV_FILE="${ENV_FILE:-.env}"
WATCH="${WATCH:-0}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-600}"
MAX_CYCLES="${MAX_CYCLES:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/monitor.log"

mkdir -p "$LOG_DIR"

cd "$PROJECT_ROOT"
{
  printf '[%s] start\n' "$(date '+%Y-%m-%d %H:%M:%S')"
  if [[ "$WATCH" == "1" ]]; then
    if [[ "$MAX_CYCLES" != "0" ]]; then
      python -m zanao_monitor.cli watch-mini-monitor --env "$ENV_FILE" --limit "$LIMIT" --interval-seconds "$INTERVAL_SECONDS" --send-limit "$SEND_LIMIT" --state "$STATE" --max-cycles "$MAX_CYCLES"
    else
      python -m zanao_monitor.cli watch-mini-monitor --env "$ENV_FILE" --limit "$LIMIT" --interval-seconds "$INTERVAL_SECONDS" --send-limit "$SEND_LIMIT" --state "$STATE"
    fi
  else
    python -m zanao_monitor.cli run-mini-monitor --env "$ENV_FILE" --limit "$LIMIT" --send --send-limit "$SEND_LIMIT" --state "$STATE"
  fi
  printf '[%s] end\n' "$(date '+%Y-%m-%d %H:%M:%S')"
} >> "$LOG_FILE" 2>&1
