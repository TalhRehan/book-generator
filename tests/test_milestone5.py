"""Test script for test milestone5."""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi_service.services.chapter_service import generate_all_chapters, regenerate_chapter
from fastapi_service.db.supabase_client import fetch_many, update

BOOK_ID = "5a2d3c05-e2c5-4280-94ca-1fa1c10cd6ff"


def test_generate_chapters():
    """Test generate chapters."""
    result = generate_all_chapters(BOOK_ID)
    print(f"Chapters processed: {len(result['chapters'])}")
    for ch in result["chapters"]:
        print(f"  Chapter {ch['chapter_number']}: {ch['status']}")


def test_regenerate_chapter():
    """Test regenerate chapter."""
    chapters = fetch_many("chapters", {"book_id": BOOK_ID}, order_by="chapter_number")

    if not chapters:
        print("No chapters found. Run test_generate_chapters first.")
        return

    first = chapters[0]

    update("chapters", {"id": first["id"]}, {
        "chapter_notes": "Make this chapter more concise and add a real world example.",
        "chapter_notes_status": "yes",
    })

    result = regenerate_chapter(BOOK_ID, first["id"])
    print(f"\nRegenerated chapter {result['chapter_number']} — status: {result['status']}")


if __name__ == "__main__":
    test_generate_chapters()
    test_regenerate_chapter()