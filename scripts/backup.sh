#!/usr/bin/env bash
# Usage: ./scripts/backup.sh [output_dir]
# Backs up the stock_insight database to a .sql.gz file.
# Reads DATABASE_URL or falls back to defaults.
# Keeps last 7 backups in the output directory.
#
# NOTE: Run `chmod +x scripts/backup.sh` to make this script executable.
set -euo pipefail

OUTPUT_DIR="${1:-./backups}"
mkdir -p "$OUTPUT_DIR"

# Parse DB connection from DATABASE_URL env or use defaults
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-stock_insight}"
DB_USER="${DB_USER:-stocky}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$OUTPUT_DIR/stocky_${TIMESTAMP}.sql.gz"

echo "Backing up $DB_NAME to $BACKUP_FILE..."
PGPASSWORD="${DB_PASSWORD:-stocky_dev}" pg_dump \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "Backup complete: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Retain only the 7 most recent backups
ls -t "$OUTPUT_DIR"/stocky_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm --
echo "Cleanup done. Kept last 7 backups."
