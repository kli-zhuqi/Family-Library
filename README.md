# Family Library Management System

A local-first family library app that ingests book-cover photos, stores structured metadata in SQLite, shows a dashboard, generates student-type recommendations, and syncs human-readable notes to Obsidian.

## Architecture

- **SQLite (`data/family_library.db`) is the source of truth** for ingestion state, deduplication, filtering, and APIs.
- **Obsidian markdown notes are a synced layer** for family-friendly browsing and manual enrichment.
- **Codex web upload-first ingestion** is supported: users upload images or zip batches, which are saved in `uploads/raw/` before ingestion.

## Setup

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Or run the Windows setup helper, then activate the environment when it finishes:

```powershell
.\scripts\setup_windows.ps1
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, run this once for your user and then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

> **PowerShell note:** do not run `source .venv/bin/activate` in PowerShell. That command only works in macOS/Linux shells or Git Bash. In PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1`.

### macOS/Linux/Git Bash

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run API

```bash
uvicorn app.main:app --reload
```

Open API docs at `http://127.0.0.1:8000/docs`.

## Run dashboard

```bash
streamlit run app/dashboard/streamlit_app.py
```

## Initial ingestion

### Upload-first (Codex web flow)

Use one of:
- `POST /books/upload-batch` with multiple image files or zip file
- `POST /books/ingest` with file uploads

### Local folder flow (optional local runtime)

```bash
curl -X POST -F 'folder_path=C:\Users\kli\Downloads\Family Library' http://127.0.0.1:8000/books/ingest
```

## Add new books later

Use:
- Dashboard button **Upload New Books**
- `POST /books/upload-new`

This endpoint/function only processes unseen images (by image path), and updates existing books only when better data is available.
Duplicate detection uses both metadata matching and `image_hash` (SHA-256), so re-uploading the same cover photo does not create a second book row.


## DeepTutor local app

This repo can launch the upstream DeepTutor web app locally and export Family Library records as Markdown sources that DeepTutor can import into a Knowledge Base. DeepTutor's current recommended Docker setup maps both the web UI (`3782`) and FastAPI backend (`8001`) ports and persists settings/workspace files under `/app/data`.

### Start DeepTutor with Docker

```bash
docker compose -f docker-compose.deeptutor.yml up
```

Open `http://127.0.0.1:3782`. The compose file mounts `./data/deeptutor` into the container so model settings, API keys, Knowledge Bases, memory, logs, and exported Family Library sources persist across restarts.

If Windows shows `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`, Docker Desktop is not running or is not installed. Start Docker Desktop, wait until it says **Docker Desktop is running**, then retry the compose command. You can check from PowerShell with:

```powershell
.\scripts\check_docker_windows.ps1
```

If you run Ollama, LM Studio, llama.cpp, vLLM, or Lemonade on your host, use `host.docker.internal` in DeepTutor's **Settings → Models** because `localhost` inside Docker points at the container.

### Export this library into DeepTutor

Use the API endpoint:

```bash
curl -X POST http://127.0.0.1:8000/deeptutor/export-library \
  -H 'Content-Type: application/json' \
  -d '{"workspace_path":"data/deeptutor"}'
```

Or run the helper script directly:

```bash
python scripts/export_to_deeptutor.py --workspace data/deeptutor
```

Both flows write Markdown files to `data/deeptutor/knowledge_sources/family_library/`. In DeepTutor, create or update a Knowledge Base from those Markdown files so Chat, Solve, Quiz, Research, and Co-Writer can use your family library metadata and OCR text as learning context.

## Obsidian sync

- Export all notes: `POST /obsidian/sync-all`
- Export one note: `POST /obsidian/sync-book/{book_id}`
- Import selected note edits back: `POST /obsidian/import-edits`

Allowed import-back fields: `title`, `author`, `publisher`, `reading_level`, `subject_tags`, `manual_notes`.

## Manual editing

Use `PUT /books/{book_id}` to correct metadata and tags.

## Testing

```bash
pytest
```

## Local real-image validation checklist

```bash
# 1) create venv + install
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) run API
uvicorn app.main:app --reload

# 3) ingest uploaded files (from Swagger UI or curl multipart)
# 4) re-upload exact same files and confirm duplicate counts do not increase
# 5) upload a zip containing the same files and confirm duplicate handling is still correct
# 6) sync all to Obsidian and verify one note per book_id
# 7) edit note frontmatter title/author/publisher/reading_level/subject_tags/manual notes
#    then import edits and verify disallowed fields (e.g. ocr_text) remain unchanged
```

## Known limitations

- OCR quality depends on image quality and OCR engine availability.
- If Tesseract is not installed, ingestion falls back to filename-based partial extraction.
- Markdown import is intentionally conservative and does not overwrite raw OCR text.
- Duplicate detection in v1 uses exact and fuzzy heuristics; ISBN/barcode support is a future enhancement.
