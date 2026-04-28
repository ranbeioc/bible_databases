# ADR-001 Dual Reference System

## Status
Accepted

## Context
Need cross-language semantic linkage while preserving version-specific display references.

## Decision
Use:
- verse_id = semantic canonical id (book-chapter-verse)
- ref = localized/version-specific id (lang-version-book-chapter-verse)

## Consequences
- Cross-language annotations possible
- RAG sources unify across languages
- UI still supports specific versions
