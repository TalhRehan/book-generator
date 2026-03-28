import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi_service.services.outline_service import generate_outline, regenerate_outline
from fastapi_service.db.supabase_client import fetch_one, update


# paste your book ID from Supabase here
BOOK_ID = "5a2d3c05-e2c5-4280-94ca-1fa1c10cd6ff"


def test_generate():
    result = generate_outline(BOOK_ID)
    assert result["outline"]
    assert result["version"] == 1
    print(f"Outline generated. Version: {result['version']}")
    print(result["outline"][:400])


def test_regenerate():
    # simulate editor adding revision notes
    update("books", {"id": BOOK_ID}, {
        "notes_on_outline_after": "Add a chapter specifically about time-blocking techniques."
    })

    result = regenerate_outline(BOOK_ID)
    assert result["version"] == 2
    print(f"\nOutline regenerated. Version: {result['version']}")
    print(result["outline"][:400])


if __name__ == "__main__":
    test_generate()
    test_regenerate()