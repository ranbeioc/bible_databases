# ADR-003 PostgreSQL + pgvector + PostGIS

## Status
Accepted

## Decision
Use one PostgreSQL instance with:
- pgvector
- PostGIS

## Rationale
Avoid split databases and keep joins, filtering, vectors, and geo in one system.
