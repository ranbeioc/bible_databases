# ADR-004 Local Embedding Strategy

## Status
Accepted

## Decision
Primary embedding generation is local GPU-based using multilingual-e5-large-instruct q8_0.

## Preferred Hardware
1. RTX 5070 Ti
2. Tesla P4 (incremental jobs)
3. VPS CPU only for testing

## Rationale
Lower cost, faster batch processing, no vendor lock-in.
