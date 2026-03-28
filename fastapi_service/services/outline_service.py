from fastapi_service.db.supabase_client import fetch_one, insert, update
from fastapi_service.services.openai_service import complete
from fastapi_service.services.notification_service import notify
from fastapi_service.utils.prompt_builder import outline_prompt, outline_regeneration_prompt


def generate_outline(book_id: str) -> dict:
    book = fetch_one("books", {"id": book_id})

    if not book:
        raise ValueError(f"Book not found: {book_id}")

    if not book.get("notes_on_outline_before"):
        notify(book_id, "waiting_for_notes", {"stage": "Outline", "reason": "notes_on_outline_before is empty"})
        raise ValueError("Cannot generate outline without notes_on_outline_before.")

    status = book.get("status_outline_notes", "no")
    if status == "yes":
        notify(book_id, "waiting_for_notes", {"stage": "Outline", "reason": "Awaiting editor review"})
        raise ValueError("Outline is awaiting editor review. Add notes or set status to no_notes_needed.")

    prompt = outline_prompt(book["title"], book["notes_on_outline_before"])
    outline_text = complete(prompt, max_tokens=2000)

    existing_versions = _get_latest_version(book_id)
    new_version = existing_versions + 1

    insert("outlines", {
        "book_id": book_id,
        "version_number": new_version,
        "content": outline_text,
        "notes_used": book["notes_on_outline_before"],
    })

    update("books", {"id": book_id}, {
        "outline": outline_text,
        "book_output_status": "in_progress",
    })

    notify(book_id, "outline_ready", {"version": new_version, "title": book["title"]})

    return {
        "book_id": book_id,
        "version": new_version,
        "outline": outline_text,
    }


def regenerate_outline(book_id: str) -> dict:
    book = fetch_one("books", {"id": book_id})

    if not book:
        raise ValueError(f"Book not found: {book_id}")

    if not book.get("outline"):
        raise ValueError("No existing outline found. Generate the outline first.")

    if not book.get("notes_on_outline_after"):
        raise ValueError("No revision notes found. Add notes_on_outline_after before regenerating.")

    prompt = outline_regeneration_prompt(
        title=book["title"],
        original_outline=book["outline"],
        new_notes=book["notes_on_outline_after"],
    )
    revised_outline = complete(prompt, max_tokens=2000)

    existing_versions = _get_latest_version(book_id)
    new_version = existing_versions + 1

    insert("outlines", {
        "book_id": book_id,
        "version_number": new_version,
        "content": revised_outline,
        "notes_used": book["notes_on_outline_after"],
    })

    update("books", {"id": book_id}, {
        "outline": revised_outline,
        "notes_on_outline_after": None,
    })

    notify(book_id, "outline_regenerated", {"version": new_version, "title": book["title"]})

    return {
        "book_id": book_id,
        "version": new_version,
        "outline": revised_outline,
    }


def _get_latest_version(book_id: str) -> int:
    client = __import__(
        "fastapi_service.db.supabase_client", fromlist=["get_client"]
    ).get_client()

    response = (
        client.table("outlines")
        .select("version_number")
        .eq("book_id", book_id)
        .order("version_number", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["version_number"]
    return 0
