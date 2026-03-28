import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi_service.services.notification_service import notify
from fastapi_service.db.supabase_client import fetch_many

BOOK_ID = "5a2d3c05-e2c5-4280-94ca-1fa1c10cd6ff"


def test_notify():
    notify(BOOK_ID, "outline_ready", {"version": 1, "title": "Test Book"})
    notify(BOOK_ID, "waiting_for_notes", {"stage": "Chapter", "chapter_number": 2})
    print("Notifications sent.")


def test_log():
    logs = fetch_many("notifications_log", {"book_id": BOOK_ID})
    print(f"Notification logs in DB: {len(logs)}")
    for log in logs:
        print(f"  [{log['event_type']}] — {log['sent_at']}")


if __name__ == "__main__":
    test_notify()
    test_log()