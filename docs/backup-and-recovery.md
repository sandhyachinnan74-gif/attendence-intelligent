# AttendAI — Backup & Disaster Recovery Guide

---

## 1. PostgreSQL Database Backups

### Automated Daily Dump (Docker)
```bash
docker exec -t attendai-postgres pg_dump -U attendai -d attendai -F c -b -v -f /var/lib/postgresql/data/attendai_backup_$(date +%Y%m%d).dump
```

### Manual Backup (Standard CLI)
```bash
pg_dump -h localhost -U attendai -d attendai -F p > attendai_backup.sql
```

---

## 2. Restoration Procedures

### Restoring from Custom Format Dump
```bash
docker exec -i attendai-postgres pg_restore -U attendai -d attendai -v /var/lib/postgresql/data/attendai_backup_YYYYMMDD.dump
```

### Restoring Plain SQL
```bash
psql -h localhost -U attendai -d attendai < attendai_backup.sql
```

---

## 3. Uploaded Document Backups
All policy documents uploaded to AttendAI are persisted in the `UPLOAD_DIR` directory (mapped to Docker volume in production). Ensure regular snapshotting or rsync of `./uploads/`.
