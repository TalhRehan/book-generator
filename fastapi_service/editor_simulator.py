"""Editor simulator that auto-reviews outlines, chapters, and final readiness."""

import time
from fastapi_service.db.supabase_client import fetch_one, fetch_many, update, get_client


def check_and_approve_outline(book_id: str):
    """Check and approve outline."""
    book = fetch_one("books", {"id": book_id})

    if not book:
        return

    if book.get("status_outline_notes") == "no_notes_needed":
        return

    if not book.get("outline"):
        return

    outline = book["outline"]
    word_count = len(outline.split())

    # approve only if outline has enough content
    if word_count < 100:
        print(f"  Outline too short ({word_count} words) requesting revision")
        update("books", {"id": book_id}, {
            "notes_on_outline_after": "Please expand the outline with more detailed chapter descriptions.",
            "status_outline_notes": "yes",
        })
        return

    print(f"  Outline looks good ({word_count} words) approving")
    update("books", {"id": book_id}, {
        "status_outline_notes": "no_notes_needed",
    })


def check_and_approve_chapters(book_id: str):
    """Check and approve chapters."""
    chapters = fetch_many("chapters", {"book_id": book_id}, order_by="chapter_number")

    if not chapters:
        return

    for chapter in chapters:
        if chapter.get("status") == "approved":
            continue

        if chapter.get("status") != "draft":
            continue

        content = chapter.get("content", "")
        word_count = len(content.split())

        # approve only if chapter has enough content
        if word_count < 300:
            print(f"  Chapter {chapter['chapter_number']} too short ({word_count} words) requesting revision")
            update("chapters", {"id": chapter["id"]}, {
                "chapter_notes": "This chapter needs more depth. Please expand with examples and details.",
                "chapter_notes_status": "yes",
                "status": "review",
            })
            continue

        print(f"  Chapter {chapter['chapter_number']} approved ({word_count} words)")
        update("chapters", {"id": chapter["id"]}, {
            "status": "approved",
            "chapter_notes_status": "no_notes_needed",
        })


def check_and_approve_final(book_id: str):
    """Check and approve final."""
    book = fetch_one("books", {"id": book_id})

    if not book:
        return

    if book.get("final_review_notes_status") == "no_notes_needed":
        return

    chapters = fetch_many("chapters", {"book_id": book_id})

    if not chapters:
        return

    all_approved = all(ch.get("status") == "approved" for ch in chapters)

    if not all_approved:
        return

    print(f"  All chapters approved clearing for final compilation")
    update("books", {"id": book_id}, {
        "final_review_notes_status": "no_notes_needed",
    })


def run_editor_cycle():
    """Run editor cycle."""
    client = get_client()

    # find all active books
    books = (
        client.table("books")
        .select("*")
        .in_("book_output_status", ["pending", "in_progress"])
        .execute()
        .data
    )

    if not books:
        return

    for book in books:
        book_id = book["id"]
        print(f"Editor reviewing: {book['title']}")

        check_and_approve_outline(book_id)
        check_and_approve_chapters(book_id)
        check_and_approve_final(book_id)


def run_loop():
    """Run loop."""
    print("Editor simulator running...")
    while True:
        try:
            run_editor_cycle()
        except Exception as e:
            print(f"Editor error: {e}")
        time.sleep(45)


if __name__ == "__main__":
    run_loop()