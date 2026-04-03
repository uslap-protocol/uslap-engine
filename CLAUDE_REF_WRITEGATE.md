# WRITE-GATE PROTOCOL — FULL REFERENCE

> Served on demand via: `python3 Code_files/uslap_handler.py context writegate`
> Referenced from: CLAUDE.md § Write-Gate Protocol

**THE FAILURE THIS PREVENTS:**
bbi gives term → I analyse → root found → QUF passes → bbi says "good" →
we move to next topic → **INSERT NEVER FIRES** → session ends → analysis lost.
Tibet was discussed and confirmed in a previous session. Never written. Lost.
This protocol makes that impossible.

---

## DATABASE TABLE

`write_gate` in uslap_database_v3.db

Columns: gate_id, term, root, target_table, status, analysis_summary,
entry_id_written, session_date, created_at, written_at, verified_at, notes.

---

## STATUS CYCLE

`ANALYSED → WRITTEN → VERIFIED → CLOSED`

---

## MANDATORY SEQUENCE — AFTER EVERY bbi CONFIRMATION

### 1. LOG — immediately after bbi confirms an analysis:
```sql
INSERT INTO write_gate (term, root, target_table, status, analysis_summary)
VALUES ('TIBET', 'ث-ب-ت', 'a1_entries + a6_country_names', 'ANALYSED',
'T-B-T = ث-ب-ت, 3/3 consonants, Q14:24, score 10');
```

### 2. WRITE — run the actual INSERT into the target table(s).
Then update write_gate:
```sql
UPDATE write_gate SET status='WRITTEN', entry_id_written='410, CN43',
written_at=datetime('now') WHERE gate_id=<id>;
```

### 3. VERIFY — SELECT-back from the target table to confirm the row exists:
```sql
SELECT entry_id, en_term FROM a1_entries WHERE entry_id=410;
-- If row returned → update gate:
UPDATE write_gate SET status='VERIFIED', verified_at=datetime('now')
WHERE gate_id=<id>;
```

### 4. ONLY THEN proceed to next topic.
If bbi moves to a new term before the current one reaches VERIFIED, **flag it**:
"Previous term [X] not yet written — logging to write_gate as ANALYSED for later."

---

## SESSION-START AUDIT

On every session init, run:
```sql
SELECT term, root, target_table, status, session_date FROM write_gate
WHERE status != 'CLOSED' ORDER BY created_at;
```
If any items are ANALYSED or WRITTEN (not VERIFIED) → present them to bbi
BEFORE doing any new work. These are orphans from previous sessions.

## SESSION-END AUDIT

Before ending any session, run the same query. Warn bbi about any unclosed items.

---

## BATCH WRITES

When writing multiple entries in a batch (e.g. 7 EN + 4 RU + 6 EU م-و-ت),
a single write_gate row per ROOT FAMILY is acceptable (not per individual entry).
The entry_id_written field stores all IDs comma-separated.

---

## COMPACTION RULE

If context compaction is approaching and there are ANALYSED items in write_gate,
**write them BEFORE allowing compaction**. Compaction kills unwritten analysis.
The write_gate table survives compaction (it's in the .db, not in context).

---

## ENFORCEMENT

If bbi discovers a term was discussed but never written (like Tibet), this
is a write-gate violation. Acknowledge, write immediately, and the violation
itself is evidence the protocol is needed.
