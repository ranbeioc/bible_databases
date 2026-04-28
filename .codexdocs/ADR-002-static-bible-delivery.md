# ADR-002 Static Bible Delivery

## Status
Accepted

## Decision
Bible primary reading data is delivered as static JSON via CDN, not runtime DB/API.

## Rationale
- Read-heavy workload
- Lowest latency
- Cache efficiency
- Lower backend cost
