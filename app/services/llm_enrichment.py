from __future__ import annotations


def enrich_record(record: dict) -> dict:
    """Deterministic placeholder for LLM-assisted enrichment in local-first mode."""
    if not record.get("language"):
        record["language"] = "English"
    return record
