#!/bin/bash
# Backup diario de la BD del CRM CarbonBox. Guarda dump comprimido, retiene 14 dias.
set -e
DIR=/root/backups
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="$DIR/carbonbox-db-$STAMP.dump"
docker exec twenty-db-1 pg_dump -U postgres -d default -Fc > "$OUT"
# retencion: borrar dumps de mas de 14 dias
find "$DIR" -name 'carbonbox-db-*.dump' -mtime +14 -delete
echo "$(date): backup OK -> $OUT ($(du -h "$OUT" | cut -f1))"
