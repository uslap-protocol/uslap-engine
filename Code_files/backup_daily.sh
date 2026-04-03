#!/bin/bash
# USLaP Daily Backup — 7 daily + 4 weekly rotation + integrity check
# Run: bash Code_files/backup_daily.sh
# Automate: crontab -e → 0 3 * * * cd "/Users/mmsetubal/Documents/USLaP workplace" && bash Code_files/backup_daily.sh >> backups/backup.log 2>&1

DB="/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"
DIR="/Users/mmsetubal/Documents/USLaP workplace/backups"
DATE=$(date +%Y-%m-%d)
DOW=$(date +%u)  # 1=Mon, 7=Sun

mkdir -p "$DIR"

# Pre-backup integrity check
INTEGRITY=$(sqlite3 "$DB" "PRAGMA integrity_check;" 2>&1)
if [ "$INTEGRITY" != "ok" ]; then
    echo "$(date): INTEGRITY FAIL — $INTEGRITY" >> "$DIR/backup.log"
    echo "⛔ DB INTEGRITY CHECK FAILED. Backup aborted."
    exit 1
fi

# Count rows as sanity check (entries should never drop)
ENTRY_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM entries;" 2>&1)
TRIGGER_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger';" 2>&1)

# Daily backup (use sqlite3 .backup for consistency — avoids partial copy)
sqlite3 "$DB" ".backup '$DIR/v3_daily_${DATE}.db'"

# Verify backup is not empty
BACKUP_SIZE=$(stat -f%z "$DIR/v3_daily_${DATE}.db" 2>/dev/null || stat --printf="%s" "$DIR/v3_daily_${DATE}.db" 2>/dev/null)
if [ "${BACKUP_SIZE:-0}" -lt 1000000 ]; then
    echo "$(date): BACKUP TOO SMALL (${BACKUP_SIZE} bytes). Possible corruption." >> "$DIR/backup.log"
    exit 1
fi

# Weekly backup on Sundays
if [ "$DOW" -eq 7 ]; then
    cp "$DIR/v3_daily_${DATE}.db" "$DIR/v3_weekly_${DATE}.db"
fi

# Rotate: keep 7 daily
ls -t "$DIR"/v3_daily_*.db 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null

# Rotate: keep 4 weekly
ls -t "$DIR"/v3_weekly_*.db 2>/dev/null | tail -n +5 | xargs rm -f 2>/dev/null

echo "$(date): OK — entries=${ENTRY_COUNT} triggers=${TRIGGER_COUNT} size=$(du -h "$DIR/v3_daily_${DATE}.db" | cut -f1)"
