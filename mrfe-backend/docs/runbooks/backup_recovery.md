# Backup and Recovery

## Databases

- PostgreSQL: schedule daily snapshots and WAL retention.
- MongoDB: enable periodic dumps and point-in-time recovery where supported.
- Redis: enable AOF/RDB depending on durability requirements.

## Recovery Drill

1. Restore to isolated environment.
2. Run integrity checks and API smoke tests.
3. Validate RPO/RTO against target objectives.
