# Family Library Project Progress

_Last updated: 2026-04-19 (UTC)_

## 1) What has been implemented

### Core app structure
- FastAPI backend with endpoints for health, books list/detail/update, ingestion/upload, recommendations, and Obsidian sync/import.
- SQLAlchemy + SQLite database layer with `Book`, `IngestionRun`, and `SyncRun` models.
- Streamlit dashboard with:
  - overview metrics,
  - ingestion controls,
  - upload-first flow,
  - editable book detail panel,
  - Obsidian sync trigger.

### Ingestion pipeline
- Folder scan and upload-first ingestion.
- Upload handling for image files + zip extraction.
- Image hash (`SHA-256`) support for dedupe reliability.
- OCR extraction with graceful fallback behavior.
- Metadata normalization and dedupe save/update logic.
- `upload_new_books()` implemented for repeated incremental ingestion.

### Recommendation and enrichment
- Rule-based recommendation engine implemented with student-type categories.
- Subject tag and reading-level inference helper functions.
- Placeholder deterministic enrichment module (`llm_enrichment.py`) for future LLM integration.

### Obsidian sync
- One markdown note per book with YAML frontmatter including stable `book_id`.
- Single-book and bulk sync functions.
- Import-back implemented with allowlisted editable fields only.

### Tests and docs
- Tests for ingestion helpers, recommendation logic, and Obsidian note generation.
- README includes setup/run commands and usage flow.

---

## 2) Key fixes made during debugging

1. **Streamlit upload filename compatibility fix**
   - Problem: Streamlit uses `UploadedFile.name`, not always `filename`.
   - Fix: ingestion now supports both attributes.

2. **One-pass iterable consumption fix in `upload_new_books()`**
   - Problem: debug iteration could consume uploaded-file iterables before actual ingestion.
   - Fix: convert uploads to a list once and reuse.

3. **Dashboard refresh/feedback improvements**
   - Added visible upload metadata, last-run summaries, and rerun behavior after actions.

4. **Streamlit crash fix for invalid preview images**
   - Problem: `st.image()` crashed with `PIL.UnidentifiedImageError` for invalid/stale image paths.
   - Fix: added image validation helper and safe preview fallback warning.

5. **Test stability fix**
   - Updated Obsidian test to use unique temp image path to avoid unique-constraint collisions.

---

## 3) Current known state from latest user logs

- Ingestion is now running and scanning uploaded files (example log showed `files_scanned=4`).
- Dashboard previously crashed in Book Detail due to invalid image preview; code now guards against this.
- Remaining oddity to monitor: low `records_created` vs `files_scanned` can happen due to dedupe/partial extraction behavior and should be reviewed with real dataset validation.

---

## 4) How to run locally

```bash
python -m venv .venv
# Windows PowerShell:
# .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

uvicorn app.main:app --reload
streamlit run app/dashboard/streamlit_app.py
```

---

## 5) Suggested next steps for next session

1. **Data cleanup utility (recommended)**
   - Add a maintenance script/endpoint to identify and optionally purge rows whose `image_path` is missing or non-loadable.

2. **Improve OCR extraction quality**
   - Integrate stronger OCR fallback parsing and optional external metadata enrichment.

3. **Dedupe quality pass**
   - Tune title/author fuzzy thresholds and add test fixtures with near-duplicate covers.

4. **Dashboard UX polish**
   - Add explicit success/failure counters for each run and better table pagination/sorting.

5. **Integration test pass with real sample batches**
   - Validate:
     - repeated upload dedupe,
     - zip upload flow,
     - Obsidian export/import roundtrip,
     - manual edit persistence.

---

## 6) Useful commands used recently

```bash
pytest -q
pytest -q tests/test_ingestion.py
python -m compileall app/dashboard/streamlit_app.py
```

---

## 7) Quick handoff note

If you start a new session, ask the next agent to:
- read this `PROGRESS.md` first,
- focus on real-image validation + cleanup utilities,
- keep SQLite as source of truth and Obsidian as synced secondary layer.
