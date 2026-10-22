#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:3000}"
SCENARIO="${1:-allow}"

case "$SCENARIO" in
  allow)
    curl -sS -X POST "${BASE_URL}/payments/start" \
      -H "Content-Type: application/json" \
      -d '{"fraudDecision":"allow","amount":1500}'
    ;;
  deny)
    curl -sS -X POST "${BASE_URL}/payments/start" \
      -H "Content-Type: application/json" \
      -d '{"fraudDecision":"deny","amount":1500}'
    ;;
  manual)
    curl -sS -X POST "${BASE_URL}/payments/start" \
      -H "Content-Type: application/json" \
      -d '{"fraudDecision":"manual","manualDecision":"approved","amount":1500}'
    ;;
  manual-deny)
    curl -sS -X POST "${BASE_URL}/payments/start" \
      -H "Content-Type: application/json" \
      -d '{"fraudDecision":"manual","manualDecision":"denied","amount":1500}'
    ;;
  *)
    echo "Usage: $0 [allow|deny|manual|manual-deny]"
    exit 1
    ;;
esac

echo
