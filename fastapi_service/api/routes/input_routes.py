from fastapi import APIRouter, HTTPException
from fastapi_service.services.input_parser import parse_excel
from fastapi_service.db.supabase_client import insert, fetch_one

router = APIRouter()


@router.post("/parse-input")
def parse_and_store(file_path: str = "input/books_input.xlsx"):
    try:
        rows = parse_excel(file_path)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    inserted = []

    for row in rows:
        # skip if book with same title already exists
        existing = fetch_one("books", {"title": row.title})
        if existing:
            inserted.append({"title": row.title, "id": existing["id"], "skipped": True})
            continue

        record = insert("books", {
            "title": row.title,
            "notes_on_outline_before": row.notes_on_outline_before,
            "notes_on_outline_after": row.notes_on_outline_after,
            "status_outline_notes": row.status_outline_notes,
            "final_review_notes_status": row.final_review_notes_status,
            "book_output_status": "pending",
        })

        inserted.append({"title": row.title, "id": record["id"], "skipped": False})

    return {"parsed": len(rows), "results": inserted}