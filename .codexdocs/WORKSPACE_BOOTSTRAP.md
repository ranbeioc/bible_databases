# BibleHome Workspace Bootstrap

## Goal

Create a separate `biblehome-platform` workspace next to this repository, so BibleHome application work does not mix with upstream Bible source data.

## Script

Use:

` .codexdocs/scripts/bootstrap_biblehome_platform.ps1 `

It creates a sibling folder:

`..\biblehome-platform`

with this structure:

```text
biblehome-platform/
  README.md
  .gitignore
  docs/
  migrations/
  ingestion/
  static-data/
  api/
  rag/
```

## Notes

- This script is idempotent for folders.
- Existing files are left untouched.
- `README.md` and `.gitignore` are created only if missing.
- No change is made to existing tracked source-data files in `bible_databases`.
