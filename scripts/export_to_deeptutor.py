from __future__ import annotations

import argparse

from app.database import SessionLocal
from app.services.deeptutor_export import export_all_books_to_deeptutor


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Family Library books as DeepTutor Markdown sources.")
    parser.add_argument("--workspace", default="data/deeptutor", help="DeepTutor workspace mounted at /app/data")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = export_all_books_to_deeptutor(db, args.workspace)
    finally:
        db.close()

    print(f"Exported {result['books_processed']} books to {result['sources_dir']}")
    for step in result["next_steps"]:
        print(f"- {step}")


if __name__ == "__main__":
    main()
