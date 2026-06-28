#!/bin/bash
set -e

# Production restore script for UPSC OS
if [ -z "$1" ]; then
  echo "Usage: $0 <backup-archive.tar.gz>"
  exit 1
fi

BACKUP_ARCHIVE="$1"
TEMP_DIR="./restore_temp"

if [ ! -f "$BACKUP_ARCHIVE" ]; then
  echo "Error: Backup file $BACKUP_ARCHIVE not found."
  exit 1
fi

mkdir -p "$TEMP_DIR"
echo "=== Starting UPSC OS Production Restore: $BACKUP_ARCHIVE ==="

# Decompress backup file
echo "Extracting backup archive contents..."
tar -xzf "$BACKUP_ARCHIVE" -C "$TEMP_DIR"
SUBDIR=$(ls "$TEMP_DIR")

RUN_DIR="$TEMP_DIR/$SUBDIR"

# 1. Restore PostgreSQL
if [ -f "$RUN_DIR/db.dump" ]; then
  echo "Restoring PostgreSQL database..."
  if [ -n "$POSTGRES_PASSWORD" ]; then
    PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -h "${POSTGRES_SERVER:-localhost}" -U "${POSTGRES_USER:-upscos}" -d "${POSTGRES_DB:-upscos}" -p "${POSTGRES_PORT:-5432}" -c -v "$RUN_DIR/db.dump"
  else
    echo "WARNING: POSTGRES_PASSWORD not set. Skipping DB restore."
  fi
fi

# 2. Restore Redis
if [ -f "$RUN_DIR/redis_dump.rdb" ]; then
  echo "Restoring Redis dump file..."
  if docker ps | grep upscos-redis >/dev/null; then
    docker cp "$RUN_DIR/redis_dump.rdb" upscos-redis:/data/dump.rdb
    docker restart upscos-redis
  fi
fi

# 3. Restore MinIO
if [ -d "$RUN_DIR/minio_assets" ]; then
  echo "Restoring MinIO assets..."
  if command -v mc >/dev/null 2>&1; then
    mc alias set myminio "http://${MINIO_ENDPOINT:-localhost:9000}" "${MINIO_ACCESS_KEY:-minioadmin}" "${MINIO_SECRET_KEY:-minioadmin-password}"
    mc mirror --overwrite "$RUN_DIR/minio_assets" myminio/"${MINIO_BUCKET:-upscos-assets}"
  fi
elif [ -f "$RUN_DIR/minio_assets.tar.gz" ]; then
  echo "Restoring MinIO assets from tar.gz volume dump..."
  if docker ps | grep upscos-minio >/dev/null; then
    docker cp "$RUN_DIR/minio_assets.tar.gz" upscos-minio:/tmp/minio_assets.tar.gz
    docker exec upscos-minio tar -xzf /tmp/minio_assets.tar.gz -C /
  fi
fi

# Cleanup
rm -rf "$TEMP_DIR"
echo "=== UPSC OS Production Restore Completed Successfully ==="
