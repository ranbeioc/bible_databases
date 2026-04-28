# Codex First Prompt (Full)

You are taking over an active long-term project named BibleHome.

Your first priority is to preserve architectural consistency and avoid introducing design drift.
Do not rush into implementation before aligning with the project memory and current accepted decisions.

## Project Identity

BibleHome is not just a Bible reader.

It is a long-term platform with these layers:
1. multilingual, multi-version Bible browsing and comparison
2. user annotations, highlights, bookmarks, notes, tags
3. Bible-centered RAG and future psychology/philosophy tutoring RAG
4. multilingual public/community interaction around the same scripture
5. church-centered LBS/community features
6. future AI extensions including speech and image generation

The system must be designed for long-term compatibility, not short-term hacks.

## Required First Read

1. architecture/PROJECT_BOOTSTRAP.md
2. architecture/biblehome_project_memory.yaml
3. database/DATABASE_MIGRATION_PLAN.md
4. architecture/decisions/ADR-001-dual-reference-system.md
5. architecture/decisions/ADR-002-static-bible-delivery.md
6. architecture/decisions/ADR-003-postgresql-pgvector-postgis.md
7. architecture/decisions/ADR-004-local-embedding-strategy.md

If any generated implementation conflicts with these documents, the documents win.

## Hard Architectural Rules

### Dual reference system is mandatory
Use:
- verse_id = canonical semantic scripture id (book-chapter-verse)
- ref = localized/version-specific display id (lang-version-book-chapter-verse)

Rules:
- all semantic cross-language association must use verse_id
- ref is display-layer only

### Bible primary reading path must be static
Bible reading data must be delivered as static JSON via CDN.

### Dynamic data is separate from Bible static data
Dynamic data includes annotations, accounts, community, vectors, LBS.

### Database baseline
Primary database is PostgreSQL with pgvector + PostGIS.

### Embedding consistency is mandatory
Use one model, one quantization, one preprocessing strategy.

### Preferred embedding strategy
Local GPU:
- multilingual-e5-large-instruct
- q8_0 preferred

## Working Style Required

1. inspect existing files and schema first
2. identify what already exists
3. propose minimal compatible changes
4. avoid destructive refactors
5. preserve future compatibility

## First Task Behavior

Start by producing:
1. architecture alignment summary
2. current assets/schema to verify
3. next 3 concrete implementation steps
4. then code

## Immediate Priority Suggestions

1. verify current DB schema
2. add missing core/community tables
3. finalize embedding dimension
4. implement annotation API
5. implement import pipeline
6. implement RAG API

## Safety Against Design Drift

Never without approval:
- collapse verse_id and ref
- move Bible reading path to runtime DB/API
- replace PostgreSQL
- mix production embedding models
