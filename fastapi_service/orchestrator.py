"""Polling orchestrator that drives the end-to-end book generation pipeline."""

import time
from fastapi_service.db.supabase_client import fetch_many, fetch_one, update, get_client
from fastapi_service.services.input_parser import parse_excel
from fastapi_service.services.outline_service import generate_outline, regenerate_outline
from fastapi_service.services.chapter_service import generate_all_chapters, regenerate_chapter
from fastapi_service.services.compilation_service import compile_book
from fastapi_service.services.notification_service import notify
from fastapi_service.db.supabase_client import insert


EXCEL_PATH = "input/books_input.xlsx"
POLL_INTERVAL = 60


def load_books_from_excel():
    """Load books from excel."""
    rows = parse_excel(EXCEL_PATH)
    new_count = 0

    for row in rows:
        existing = fetch_one("books", {"title": row.title})
        if existing:
            continue

        insert("books", {
            "title": row.title,
            "notes_on_outline_before": row.notes_on_outline_before,
            "notes_on_outline_after": row.notes_on_outline_after,
            "status_outline_notes": row.status_outline_notes,
            "final_review_notes_status": row.final_review_notes_status,
            "book_output_status": "pending",
        })
        new_count += 1

    if new_count > 0:
        print(f"[+] {new_count} new book(s) queued from Excel.")


def process_pending_books():
    """Process pending books."""
    client = get_client()
    books = (
        client.table("books")
        .select("*")
        .eq("book_output_status", "pending")
        .execute()
        .data
    )

    for book in books:
        book_id = book["id"]
        print(f"\n[OUTLINE] Starting → \"{book['title']}\"")

        try:
            update("books", {"id": book_id}, {"book_output_status": "in_progress"})
            generate_outline(book_id)
            print(f"[OUTLINE] Done ✓")
        except ValueError as e:
            print(f"[OUTLINE] Blocked — {e}")
            notify(book_id, "pipeline_error", {"reason": str(e)})
            update("books", {"id": book_id}, {"book_output_status": "paused"})


def process_outline_approved_books():
    """Process outline approved books."""
    client = get_client()
    books = (
        client.table("books")
        .select("*")
        .eq("book_output_status", "in_progress")
        .eq("status_outline_notes", "no_notes_needed")
        .execute()
        .data
    )

    for book in books:
        book_id = book["id"]

        if book.get("notes_on_outline_after"):
            try:
                print(f"\n[OUTLINE] Editor requested revision → regenerating...")
                regenerate_outline(book_id)
                print(f"[OUTLINE] Regenerated ✓")
            except ValueError as e:
                print(f"[OUTLINE] Regen blocked — {e}")
            continue

        existing_chapters = fetch_many("chapters", {"book_id": book_id})
        all_approved = existing_chapters and all(
            ch.get("status") == "approved" for ch in existing_chapters
        )

        if all_approved:
            return

        try:
            print(f"\n[CHAPTERS] Outline approved — beginning chapter generation...")
            result = generate_all_chapters(book_id)
            for ch in result["chapters"]:
                status_icon = "✓" if ch["status"] == "generated" else "⏸"
                print(f"  {status_icon}  Chapter {ch['chapter_number']} — {ch['status']}")
        except ValueError as e:
            print(f"[CHAPTERS] Failed — {e}")
            notify(book_id, "pipeline_error", {"reason": str(e)})


def process_chapters_with_notes():
    """Process chapters with notes."""
    client = get_client()
    chapters = (
        client.table("chapters")
        .select("*")
        .eq("chapter_notes_status", "yes")
        .execute()
        .data
    )

    for chapter in chapters:
        if not chapter.get("chapter_notes"):
            continue
        try:
            print(f"\n[CHAPTERS] Editor notes found → revising Chapter {chapter['chapter_number']}...")
            regenerate_chapter(chapter["book_id"], chapter["id"])
            print(f"[CHAPTERS] Chapter {chapter['chapter_number']} revised ✓")
        except ValueError as e:
            print(f"[CHAPTERS] Revision failed — {e}")


def process_ready_for_compilation():
    """Process ready for compilation."""
    client = get_client()
    books = (
        client.table("books")
        .select("*")
        .eq("final_review_notes_status", "no_notes_needed")
        .eq("book_output_status", "in_progress")
        .execute()
        .data
    )

    for book in books:
        book_id = book["id"]
        chapters = fetch_many("chapters", {"book_id": book_id})

        if not chapters:
            continue

        unapproved = [ch for ch in chapters if ch.get("status") != "approved"]
        if unapproved:
            print(f"[COMPILE] Waiting — {len(unapproved)} chapter(s) still pending review.")
            continue

        try:
            print(f"\n[COMPILE] All chapters approved — compiling final book...")
            compile_book(book_id)
            print(f"[COMPILE] \"{book['title']}\" is ready. DOCX + PDF generated ✓")
        except ValueError as e:
            print(f"[COMPILE] Failed — {e}")
            notify(book_id, "pipeline_error", {"reason": str(e)})


def _countdown(seconds: int):
    """Countdown."""
    for remaining in range(seconds, 0, -1):
        print(f"\r  Next cycle in {remaining}s...", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 30 + "\r", end="")


def run_once():
    """Run once."""
    load_books_from_excel()
    process_pending_books()
    process_outline_approved_books()
    process_chapters_with_notes()
    process_ready_for_compilation()


def run_loop():
    """Run loop."""
    print("=" * 50)
    print("   Book Generation Orchestrator — Started")
    print("=" * 50)

    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[ERROR] Orchestrator — {e}")
        _countdown(POLL_INTERVAL)


if __name__ == "__main__":
    run_loop()
