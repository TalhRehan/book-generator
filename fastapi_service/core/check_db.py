import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from fastapi_service.db.supabase_client import insert, fetch_one, update
from fastapi_service.core.config import settings

def run():
    print("Checking Supabase connection...")

    record = insert("books", {
        "title": "Connection Test Book",
        "notes_on_outline_before": "This is a test note.",
        "book_output_status": "pending"
    })

    book_id = record["id"]
    print(f"Inserted book: {book_id}")

    fetched = fetch_one("books", {"id": book_id})
    assert fetched["title"] == "Connection Test Book"
    print("Fetch verified.")

    update("books", {"id": book_id}, {"book_output_status": "paused"})
    updated = fetch_one("books", {"id": book_id})
    assert updated["book_output_status"] == "paused"
    print("Update verified.")

    print("All checks passed. Supabase is connected and working.")

if __name__ == "__main__":
    run()