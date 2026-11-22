#!/usr/bin/env sh
set -eu
# Run from the system directory; encrypt with an existing recipient public key.
: "${BACKUP_RECIPIENT:?Set BACKUP_RECIPIENT to the backup operator GPG identity}"
mkdir -p backups
stamp=$(date -u +%Y%m%dT%H%M%SZ)
docker compose exec -T mysql sh -c 'exec mysqldump --single-transaction --routines -u root -p"$MYSQL_ROOT_PASSWORD" instrumenthub' | gpg --batch --yes --encrypt --recipient "$BACKUP_RECIPIENT" --output "backups/database-$stamp.sql.gpg"
docker compose exec -T minio tar -C /data -cf - . | gpg --batch --yes --encrypt --recipient "$BACKUP_RECIPIENT" --output "backups/reports-$stamp.tar.gpg"
printf 'Backup created: %s\n' "$stamp"
