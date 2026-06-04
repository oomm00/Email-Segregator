"""Ingestion service — placeholder.

In Phase 1, this service will own raw email ingestion:
  - Consuming raw.email.received events.
  - Deduplication via checksum.
  - Persisting to raw_emails + dedup_fingerprints.
  - Publishing email.parsed.
"""
