"""Pydantic schemas shared across API and service layers."""

from pydantic import BaseModel
from typing import Optional


class BookInputRow(BaseModel):
    title: str
    notes_on_outline_before: Optional[str] = None
    notes_on_outline_after: Optional[str] = None
    status_outline_notes: Optional[str] = "no"
    final_review_notes_status: Optional[str] = "no"


class BookRecord(BookInputRow):
    id: str
    book_output_status: str