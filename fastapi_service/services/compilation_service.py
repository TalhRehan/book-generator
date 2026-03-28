"""Service-layer business logic for the book generation workflow."""

import os
from fastapi_service.db.supabase_client import fetch_one, fetch_many, update, get_client
from fastapi_service.utils.docx_builder import build_docx
from fastapi_service.utils.pdf_builder import build_pdf
from fastapi_service.services.notification_service import notify

OUTPUT_DIR = "output"


def compile_book(book_id: str) -> dict:
    """Compile book."""
    book = fetch_one("books", {"id": book_id})

    if not book:
        raise ValueError(f"Book not found: {book_id}")

    final_status = book.get("final_review_notes_status", "no")
    if final_status not in ("no_notes_needed", "yes"):
        raise ValueError("Book is not cleared for compilation. Set final_review_notes_status to no_notes_needed.")

    chapters = fetch_many("chapters", {"book_id": book_id}, order_by="chapter_number")

    if not chapters:
        raise ValueError("No chapters found for this book.")

    unapproved = [ch for ch in chapters if ch.get("status") != "approved"]
    if unapproved:
        chapter_nums = [str(ch["chapter_number"]) for ch in unapproved]
        raise ValueError(f"Chapters not yet approved: {', '.join(chapter_nums)}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    safe_title = book["title"].replace(" ", "_").lower()
    docx_path = os.path.join(OUTPUT_DIR, f"{safe_title}.docx")
    pdf_path = os.path.join(OUTPUT_DIR, f"{safe_title}.pdf")

    chapter_data = [
        {
            "chapter_number": ch["chapter_number"],
            "title": ch["title"],
            "content": ch["content"],
        }
        for ch in chapters
    ]

    build_docx(book["title"], chapter_data, docx_path)
    build_pdf(book["title"], chapter_data, pdf_path)

    docx_url = _upload_to_supabase(book_id, docx_path, f"{safe_title}.docx")
    pdf_url = _upload_to_supabase(book_id, pdf_path, f"{safe_title}.pdf")

    update("books", {"id": book_id}, {"book_output_status": "complete"})

    notify(book_id, "final_draft_ready", {
        "title": book["title"],
        "docx": docx_url or docx_path,
        "pdf": pdf_url or pdf_path,
    })

    return {
        "book_id": book_id,
        "title": book["title"],
        "docx": docx_url or docx_path,
        "pdf": pdf_url or pdf_path,
        "status": "complete",
    }


def _upload_to_supabase(book_id: str, file_path: str, file_name: str) -> str | None:
    """Upload to supabase."""
    try:
        client = get_client()
        bucket = "book-outputs"

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        storage_path = f"{book_id}/{file_name}"

        client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": _get_content_type(file_name), "upsert": "true"},
        )

        result = client.storage.from_(bucket).get_public_url(storage_path)
        return result

    except Exception as e:
        print(f"Supabase Storage upload failed: {e}")
        return None


def _get_content_type(file_name: str) -> str:
    """Get content type."""
    if file_name.endswith(".pdf"):
        return "application/pdf"
    if file_name.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "application/octet-stream"