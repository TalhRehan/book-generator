"""Test script for test full pipeline."""

import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi_service.services.input_parser import parse_excel
from fastapi_service.services.outline_service import generate_outline, regenerate_outline
from fastapi_service.services.chapter_service import generate_all_chapters, regenerate_chapter
from fastapi_service.services.compilation_service import compile_book
from fastapi_service.db.supabase_client import insert, fetch_one, fetch_many, update


EXCEL_PATH = "input/books_input.xlsx"


def step(msg):
    """Step."""
    print(f"\n{'─' * 50}")
    print(f"  {msg}")
    print(f"{'─' * 50}")


def run():
    """Run."""
    step("Stage 1 — Parsing Excel input")
    rows = parse_excel(EXCEL_PATH)
    assert rows, "No rows parsed from Excel"

    row = rows[0]
    existing = fetch_one("books", {"title": row.title})

    if existing:
        book_id = existing["id"]
        print(f"Book already exists: {book_id}")
    else:
        record = insert("books", {
            "title": row.title,
            "notes_on_outline_before": row.notes_on_outline_before,
            "notes_on_outline_after": row.notes_on_outline_after,
            "status_outline_notes": row.status_outline_notes,
            "final_review_notes_status": row.final_review_notes_status,
            "book_output_status": "pending",
        })
        book_id = record["id"]
        print(f"Book inserted: {book_id}")

    step("Stage 2 — Generating outline")
    outline_result = generate_outline(book_id)
    print(f"Outline version {outline_result['version']} generated")
    print(outline_result["outline"][:300])

    step("Stage 3 — Regenerating outline with editor notes")
    update("books", {"id": book_id}, {
        "notes_on_outline_after": "Add a chapter on building deep work habits in a remote work environment."
    })
    regen_result = regenerate_outline(book_id)
    print(f"Outline regenerated — version {regen_result['version']}")

    step("Stage 4 — Generating all chapters")
    chapter_result = generate_all_chapters(book_id)
    for ch in chapter_result["chapters"]:
        print(f"  Chapter {ch['chapter_number']}: {ch['status']}")

    step("Stage 5 — Regenerating chapter 1 with editor notes")
    chapters = fetch_many("chapters", {"book_id": book_id}, order_by="chapter_number")
    first = chapters[0]

    update("chapters", {"id": first["id"]}, {
        "chapter_notes": "Add more real world examples and make the opening more compelling.",
        "chapter_notes_status": "yes",
    })

    regen_ch = regenerate_chapter(book_id, first["id"])
    print(f"Chapter {regen_ch['chapter_number']} regenerated — {regen_ch['status']}")

    step("Stage 6 — Approving all chapters for compilation")
    for ch in chapters:
        update("chapters", {"id": ch["id"]}, {"status": "approved"})
    update("books", {"id": book_id}, {"final_review_notes_status": "no_notes_needed"})
    print("All chapters approved")

    step("Stage 7 — Compiling final book")
    compile_result = compile_book(book_id)
    print(f"Status : {compile_result['status']}")
    print(f"Docx   : {compile_result['docx']}")
    print(f"PDF    : {compile_result['pdf']}")

    step("Pipeline complete")
    print(f"Book '{compile_result['title']}' successfully generated.")


if __name__ == "__main__":
    run()