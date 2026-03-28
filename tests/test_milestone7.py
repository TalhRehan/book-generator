"""Test script for test milestone7."""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi_service.services.compilation_service import compile_book

BOOK_ID = "199c4a46-f88c-4ea4-92ec-40f16ed284ea"


def test_compile():
    """Test compile."""
    result = compile_book(BOOK_ID)
    print(f"Status   : {result['status']}")
    print(f"Title    : {result['title']}")
    print(f"Docx     : {result['docx']}")
    print(f"PDF      : {result['pdf']}")


if __name__ == "__main__":
    test_compile()