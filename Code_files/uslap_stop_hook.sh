#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# USLaP STOP HOOK — al-Ikhlāṣ
# Fires AFTER every Claude response. Reads last_assistant_message.
# If contamination found → BLOCKS Claude from stopping → forces re-derive.
# Claude cannot finish its turn until output is clean.
# ═══════════════════════════════════════════════════════════════════════════════

# Read the hook input (JSON with last_assistant_message)
INPUT=$(cat)

# Extract last_assistant_message
MSG=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('last_assistant_message', ''))
except:
    print('')
" 2>/dev/null)

# If empty, allow stop
if [ -z "$MSG" ]; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Run selfaudit scan on the message
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULT=$(echo "$MSG" | python3 "$SCRIPT_DIR/uslap_stop_scan.py" 2>"$SCRIPT_DIR/.stop_hook_errors.log")
EXIT_CODE=$?

# FAIL-SAFE: if the scan CRASHED (exit code > 1, or no result when exit != 0),
# BLOCK by default. A crashed scan = unknown state = not safe to allow.
if [ $EXIT_CODE -ne 0 ]; then
    if [ -n "$RESULT" ]; then
        ESCAPED=$(echo "$RESULT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null)
        echo "{\"decision\": \"block\", \"reason\": $ESCAPED}"
    else
        echo "{\"decision\": \"block\", \"reason\": \"Stop scan CRASHED (exit $EXIT_CODE). Blocking by default. Check $SCRIPT_DIR/.stop_hook_errors.log\"}"
    fi
    exit 0
fi

# Exit 0 + no result = clean
echo '{"decision": "allow"}'
exit 0
