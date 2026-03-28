import re
from fastapi_service.db.supabase_client import fetch_one, fetch_many, insert, update, get_client
from fastapi_service.services.openai_service import complete
from fastapi_service.utils.prompt_builder import chapter_prompt, chapter_regeneration_prompt, summary_prompt


def parse_chapters_from_outline(outline_text: str) -> list[dict]:
    chapters = []
    lines = outline_text.split("\n")
    current = None

    for line in lines:
        line = line.strip()
        match = re.match(r"^(\d+)\.\s+(.+)$", line)
        if match:
            if current:
                chapters.append(current)
            current = {
                "chapter_number": int(match.group(1)),
                "title": match.group(2).strip(),
                "description": "",
            }
        elif current and line and not re.match(r"^(\d+)\.", line):
            current["description"] += line + " "

    if current:
        chapters.append(current)

    for ch in chapters:
        ch["description"] = ch["description"].strip()

    return chapters


def get_previous_summaries(book_id: str, before_chapter_number: int) -> str:
    chapters = fetch_many("chapters", {"book_id": book_id}, order_by="chapter_number")
    relevant = [
        ch for ch in chapters
        if ch["chapter_number"] < before_chapter_number and ch.get("summary")
    ]

    if not relevant:
        return ""

    summaries = []
    for ch in relevant:
        summaries.append(f"Chapter {ch['chapter_number']} - {ch['title']}:\n{ch['summary']}")

    return "\n\n".join(summaries)


def generate_all_chapters(book_id: str) -> dict:
    book = fetch_one("books", {"id": book_id})

    if not book:
        raise ValueError(f"Book not found: {book_id}")

    if not book.get("outline"):
        raise ValueError("No outline found. Complete the outline stage first.")

    status = book.get("status_outline_notes")
    if status not in ("no_notes_needed", "no"):
        raise ValueError("Outline has not been cleared for chapter generation.")

    chapters_meta = parse_chapters_from_outline(book["outline"])

    if not chapters_meta:
        raise ValueError("Could not parse chapters from outline. Check outline format.")

    results = []

    for meta in chapters_meta:
        existing = _get_existing_chapter(book_id, meta["chapter_number"])
        if existing and existing.get("status") == "approved":
            results.append({
                "chapter_number": meta["chapter_number"],
                "status": "skipped - already approved",
            })
            continue

        chapter_notes_status = existing.get("chapter_notes_status", "no") if existing else "no"

        if chapter_notes_status == "yes":
            results.append({
                "chapter_number": meta["chapter_number"],
                "status": "paused - waiting for editor notes",
            })
            continue

        previous_summaries = get_previous_summaries(book_id, meta["chapter_number"])

        chapter_notes = existing.get("chapter_notes") if existing else None

        prompt = chapter_prompt(
            title=book["title"],
            chapter_number=meta["chapter_number"],
            chapter_title=meta["title"],
            chapter_description=meta["description"],
            previous_summaries=previous_summaries,
            chapter_notes=chapter_notes,
        )

        content = complete(prompt, max_tokens=3000)

        summary_p = summary_prompt(meta["chapter_number"], meta["title"], content)
        summary = complete(summary_p, max_tokens=300)

        if existing:
            update("chapters", {"id": existing["id"]}, {
                "content": content,
                "summary": summary,
                "status": "draft",
                "chapter_notes": None,
            })
            chapter_id = existing["id"]
        else:
            record = insert("chapters", {
                "book_id": book_id,
                "chapter_number": meta["chapter_number"],
                "title": meta["title"],
                "content": content,
                "summary": summary,
                "chapter_notes_status": "no_notes_needed",
                "status": "draft",
            })
            chapter_id = record["id"]

        results.append({
            "chapter_number": meta["chapter_number"],
            "chapter_id": chapter_id,
            "status": "generated",
        })

    return {"book_id": book_id, "chapters": results}


def regenerate_chapter(book_id: str, chapter_id: str) -> dict:
    book = fetch_one("books", {"id": book_id})
    chapter = fetch_one("chapters", {"id": chapter_id})

    if not book:
        raise ValueError(f"Book not found: {book_id}")
    if not chapter:
        raise ValueError(f"Chapter not found: {chapter_id}")

    if not chapter.get("chapter_notes"):
        raise ValueError("No revision notes found for this chapter.")

    previous_summaries = get_previous_summaries(book_id, chapter["chapter_number"])

    prompt = chapter_regeneration_prompt(
        title=book["title"],
        chapter_number=chapter["chapter_number"],
        chapter_title=chapter["title"],
        original_content=chapter["content"],
        revision_notes=chapter["chapter_notes"],
        previous_summaries=previous_summaries,
    )

    content = complete(prompt, max_tokens=3000)

    summary_p = summary_prompt(chapter["chapter_number"], chapter["title"], content)
    summary = complete(summary_p, max_tokens=300)

    update("chapters", {"id": chapter_id}, {
        "content": content,
        "summary": summary,
        "status": "draft",
        "chapter_notes": None,
        "chapter_notes_status": "no_notes_needed",
    })

    return {
        "chapter_id": chapter_id,
        "chapter_number": chapter["chapter_number"],
        "status": "regenerated",
    }


def _get_existing_chapter(book_id: str, chapter_number: int) -> dict | None:
    client = get_client()
    response = (
        client.table("chapters")
        .select("*")
        .eq("book_id", book_id)
        .eq("chapter_number", chapter_number)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None