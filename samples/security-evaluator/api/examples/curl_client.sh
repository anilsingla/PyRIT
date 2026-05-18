#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8088}"
PAYLOAD_PATH="${2:-./api/examples/dry_run_payload.json}"
TAIL_LINES="${TAIL_LINES:-200}"
POLL_SECONDS="${POLL_SECONDS:-2}"
MAX_POLLS="${MAX_POLLS:-90}"

if [[ ! -f "$PAYLOAD_PATH" ]]; then
  echo "Payload file not found: $PAYLOAD_PATH" >&2
  exit 1
fi

echo "== Health check =="
curl -sS "$BASE_URL/health"
echo ""

echo "== Supported options =="
curl -sS "$BASE_URL/api/v1/options"
echo ""

echo "== Start dry run =="
START_RESPONSE="$(curl -sS -X POST "$BASE_URL/api/v1/runs/dry-run" \
  -H "Content-Type: application/json" \
  --data-binary "@$PAYLOAD_PATH")"
echo "$START_RESPONSE"

JOB_ID="$(printf '%s' "$START_RESPONSE" | python -c "import json,sys; print(json.load(sys.stdin).get('job_id',''))")"
if [[ -z "$JOB_ID" ]]; then
  echo "Failed to parse job_id from response" >&2
  exit 1
fi

echo "== Poll status ($JOB_ID) =="
STATUS=""
for ((i=1; i<=MAX_POLLS; i++)); do
  STATUS_RESPONSE="$(curl -sS "$BASE_URL/api/v1/runs/$JOB_ID")"
  STATUS="$(printf '%s' "$STATUS_RESPONSE" | python -c "import json,sys; print(json.load(sys.stdin).get('status',''))")"
  echo "Poll #$i status=$STATUS"

  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" || "$STATUS" == "cancelled" ]]; then
    break
  fi

  sleep "$POLL_SECONDS"
done

echo "== Final status =="
curl -sS "$BASE_URL/api/v1/runs/$JOB_ID"
echo ""

echo "== Output tail =="
curl -sS "$BASE_URL/api/v1/runs/$JOB_ID/output?tail_lines=$TAIL_LINES"
echo ""
