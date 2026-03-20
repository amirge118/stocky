#!/usr/bin/env bash
# Usage: ./scripts/restore.sh <backup_file>
# Restores a .sql.gz backup to the stock_insight database.
#
# NOTE: Run `chmod +x scripts/restore.sh` to make this script executable.
set -euo pipefail

BACKUP_FILE="${1:?Usage: $0 <backup_file.sql.gz>}"
[[ -f "$BACKUP_FILE" ]] || { echo "File not found: $BACKUP_FILE"; exit 1; }

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-stock_insight}"
DB_USER="${DB_USER:-stocky}"

echo "Restoring $DB_NAME from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="${DB_PASSWORD:-stocky_dev}" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  "$DB_NAME"
echo "Restore complete."
