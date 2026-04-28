# BibleHome Safe Alternative Plan

## Purpose

This document records the safer execution path after inspecting the current `bible_databases` repository and the BibleHome project memory.

The current repository should be treated as a source-data repository, not as the main BibleHome application repository.

## Current Repository State

- Current branch: `feat/clear-all-button`
- Tracked file changes: none at time of inspection
- Untracked project-memory folder: `.codexdocs/`
- Repository content:
  - static Bible data in `formats/json`, `formats/csv`, `formats/sql`, `formats/psql`, `formats/sqlite`, `formats/yaml`, `formats/txt`, `formats/md`
  - documentation under `docs/`
  - simple static browser files: `index.html`, `script.js`, `style.css`
- Existing database format in this repository:
  - `<translation>_books`
  - `<translation>_verses`
  - `translations`
  - `cross_references`

This differs from the BibleHome target architecture, which requires separate dynamic schemas such as `core`, `annotation`, `community`, and `ai`.

## Accepted Architecture To Preserve

- `verse_id` is the canonical semantic key.
- `ref` is the localized/version-specific display key.
- Primary Bible reading data should be static JSON distributed through CDN.
- Dynamic data belongs in PostgreSQL.
- PostgreSQL must support pgvector and PostGIS.
- Embeddings should be generated locally when possible.
- A production vector store must not mix embedding models, quantization variants, or preprocessing rules.

## Main Risk

Directly implementing BibleHome migrations, APIs, annotation logic, or RAG pipelines inside this repository would mix two different responsibilities:

1. upstream Bible source data
2. BibleHome application and dynamic platform data

That would make upgrades, rollback, data regeneration, and future upstream sync harder.

There is also a practical SQL risk: many existing SQL export files in `formats/sql` and `formats/psql` include destructive setup statements such as `DROP TABLE IF EXISTS`. These files are useful as export artifacts, but should not be treated as production BibleHome migrations.

## Safer Alternative

Keep this repository as a read-only data source for BibleHome.

Create a separate BibleHome workspace, preferably one of:

- `biblehome-platform`
- `biblehome-ingestion`
- `biblehome`

That separate workspace should own:

- PostgreSQL migrations
- application API code
- annotation logic
- RAG query logic
- embedding jobs
- static chapter JSON generation for CDN
- staging and validation scripts

This repository should only be read by ingestion tools.

## Proposed Repository Boundary

### This Repository: `bible_databases`

Responsibilities:

- source Bible translations
- source cross references
- original export formats
- upstream data history

Avoid adding:

- BibleHome production DB migrations
- API routes
- application auth/session code
- vector backfill jobs
- deployment configuration for the BibleHome app

### BibleHome Platform Repository

Responsibilities:

- `core.users`
- `core.sessions`
- `annotation.annotations`
- `annotation.tags`
- `annotation.tag_translations`
- `community.posts`
- `community.groups`
- `community.memberships`
- `community.churches`
- `ai.chunks`
- static JSON build pipeline
- RAG and embedding pipeline
- application API

## First Safe Validation Target

Use a very small ingestion sample before full migration.

Recommended sample:

- source file: `formats/json/KJV.json`
- range: John chapter 3
- target output:
  - one static chapter JSON file
  - one staging table load or staging SQL file
  - generated `verse_id`
  - generated `ref`

Expected identity rules:

```text
verse_id = book-chapter-verse
ref = lang-version-book-chapter-verse
```

Example:

```text
verse_id = 43-3-16
ref = en-KJV-43-3-16
```

## Next 3 Safest Implementation Steps

1. Commit `.codexdocs/` as project memory only.

   This preserves accepted decisions without touching source Bible data.

2. Create a separate BibleHome workspace skeleton.

   Start with folders such as:

   ```text
   biblehome-platform/
     docs/
     migrations/
     ingestion/
     static-data/
     api/
     rag/
   ```

3. Build the smallest ingestion proof of concept.

   Read `formats/json/KJV.json`, extract John 3, generate:

   - `static-data/en/KJV/john/3.json`
   - a staging CSV or staging SQL file
   - a validation report confirming `verse_id` and `ref`

Only after this small proof passes should the project add broader migrations, chunking, embedding, and API implementation.

## Migration Safety Rules

- Do not run existing `formats/sql` or `formats/psql` exports against the BibleHome production database.
- Do not add vector columns until the final embedding dimension has been verified.
- Do not drop or rewrite vector columns directly; add new columns, backfill, validate, then switch.
- Do not make Bible primary reading depend on runtime DB or API calls.
- Do not use `ref` as the cross-language semantic key.
- Do not mix embedding models or quantization variants in the same production vector space.

## Decision

Proceed with the separate-platform approach.

The `bible_databases` repository remains the source-data repository. BibleHome implementation should live in a separate workspace and consume this repository through explicit ingestion scripts.
