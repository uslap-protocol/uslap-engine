#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# USLaP PreToolUse HOOK — al-Mīzān
# Fires BEFORE any tool call.
# BLOCKS raw SQL INSERT/UPDATE on protected entry tables.
# All writes MUST go through handler.write_entry() which calls QUF.
# ═══════════════════════════════════════════════════════════════════════════════

INPUT=$(cat)

TOOL=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_name', ''))
except:
    print('')
" 2>/dev/null)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB="$SCRIPT_DIR/uslap_database_v3.db"

# Check init lock
if [ ! -f "$SCRIPT_DIR/.uslap_init_lock" ]; then
    python3 "$SCRIPT_DIR/uslap_handler.py" init > /dev/null 2>&1
fi

# For Bash tool calls: extract the command
TOOL_INPUT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    ti = data.get('tool_input', {})
    print(ti.get('command', '') if isinstance(ti, dict) else '')
except:
    print('')
" 2>/dev/null)

# ═══════════════════════════════════════════════════════════════════════════════
# WRITE GATE — BLOCK raw SQL writes to protected tables
# The compute engine MUST use handler.write_entry() for all DB writes.
# handler.write_entry() calls QUF validate (Q + U + F gates).
# Raw SQL bypasses QUF. Therefore raw SQL writes are BLOCKED.
# ═══════════════════════════════════════════════════════════════════════════════

if [ "$TOOL" = "Bash" ] && [ -n "$TOOL_INPUT" ]; then
    # Check if command contains raw SQL write to protected tables
    VIOLATION=$(echo "$TOOL_INPUT" | python3 -c "
import sys, re

cmd = sys.stdin.read().lower()

# Protected tables — ALL entry tables + supporting tables
PROTECTED = [
    'a1_entries', 'a1_записи', 'european_a1_entries', 'latin_a1_entries',
    'persian_a1_mad_khil', 'bitig_a1_entries',
    'a2_names_of_allah', 'a3_quran_refs', 'a4_derivatives', 'a5_cross_refs',
    'a6_country_names', 'm4_networks',
    'qv_translation_register', 'contamination_blacklist',
    'root_explosion_manifest', 'protocol_immutable',
    'write_gate', 'session_index',
]

# SQL write operations
WRITE_OPS = ['insert into', 'update ', 'delete from', 'replace into']

# Check: does the command contain a write op targeting a protected table?
violations = []
for op in WRITE_OPS:
    if op in cmd:
        for table in PROTECTED:
            if table in cmd:
                violations.append(f'{op.strip()} on {table}')

# Exception: handler.write_entry and uslap_quf.py are allowed
# They are Python scripts that call QUF internally
ALLOWED_CALLERS = ['handler.py', 'uslap_handler', 'uslap_quf', 'write_entry', 'uslap_index']
if any(caller in cmd for caller in ALLOWED_CALLERS):
    violations = []  # Allow — these tools enforce QUF internally

if violations:
    print('|'.join(violations))
else:
    print('')
" 2>/dev/null)

    if [ -n "$VIOLATION" ]; then
        ESCAPED=$(echo "$VIOLATION" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null)
        echo "{\"decision\": \"block\", \"reason\": \"RAW SQL WRITE BLOCKED on protected table(s): $VIOLATION. All DB writes MUST go through handler.write_entry() which enforces QUF (Q+U+F gates). Raw SQL bypasses QUF and is permanently blocked. Use: python3 Code_files/uslap_handler.py write_entry ...\"}"
        exit 0
    fi
fi

echo '{"decision": "allow"}'
exit 0
