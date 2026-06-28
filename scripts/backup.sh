#!/bin/bash
set -e

# Production backup script for UPSC OS
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUN_DIR="$BACKUP_DIR/$TIMESTAMP"

mkdir -p "$RUN_DIR"

echo "=== Starting UPSC OS Production Backup: $TIMESTAMP ==="

# 1. PostgreSQL backup
echo "Backing up PostgreSQL database..."
if [ -n "$POSTGRES_PASSWORD" ]; then
  PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "${POSTGRES_SERVER:-localhost}" -U "${POSTGRES_USER:-upscos}" -d "${POSTGRES_DB:-upscos}" -p "${POSTGRES_PORT:-5432}" -F c -b -v -f "$RUN_DIR/db.dump"
else
  echo "WARNING: POSTGRES_PASSWORD not set. Skipping DB backup or hoping local socket auth works."
fi

# 2. Redis backup
echo "Backing up Redis cache..."
if docker exec upscos-redis redis-cli save >/dev/null 2>&1; then
  docker cp upscos-redis:/data/dump.rdb "$RUN_DIR/redis_dump.rdb"
  echo "Redis RDB snapshot successfully captured."
else
  echo "WARNING: Could not connect to container upscos-redis. Trying local command..."
  if redis-cli save >/dev/null 2>&1; then
    cp /var/lib/redis/dump.rdb "$RUN_DIR/redis_dump.rdb" || cp /data/dump.rdb "$RUN_DIR/redis_dump.rdb" || true
  fi
fi

# 3. Object Storage backup (MinIO assets)
echo "Backing up MinIO object storage assets..."
if command -v mc >/dev/null 2>&1; then
  mc alias set myminio "http://${MINIO_ENDPOINT:-localhost:9000}" "${MINIO_ACCESS_KEY:-minioadmin}" "${MINIO_SECRET_KEY:-minioadmin-password}"
  mc mirror myminio/"${MINIO_BUCKET:-upscos-assets}" "$RUN_DIR/minio_assets"
else
  echo "WARNING: mc command-line client not found. Compressing container volume instead..."
  if docker ps | grep upscos-minio >/dev/null; then
    docker exec upscos-minio tar -czf - /data > "$RUN_DIR/minio_assets.tar.gz" || true
  fi
fi

# 4. Packaging the backup archive
echo "Packaging and compressing all production backup targets..."
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "$TIMESTAMP"
rm -rf "$RUN_DIR"

echo "=== UPSC OS Production Backup Completed: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz ==="
