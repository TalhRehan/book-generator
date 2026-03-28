"""Service-layer business logic for the book generation workflow."""

import smtplib
import json
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi_service.core.config import settings
from fastapi_service.db.supabase_client import insert


EVENTS = {
    "outline_ready":        "Outline Ready for Review",
    "outline_regenerated":  "Outline Has Been Regenerated",
    "chapter_ready":        "Chapter Ready for Review",
    "chapter_regenerated":  "Chapter Has Been Regenerated",
    "waiting_for_notes":    "Pipeline Paused - Waiting for Editor Notes",
    "final_draft_ready":    "Final Draft Compiled Successfully",
    "pipeline_error":       "Pipeline Error - Action Required",
}


def notify(book_id: str, event: str, extra: dict = None):
    """Notify."""
    subject = EVENTS.get(event, event)
    body = _build_body(subject, book_id, extra)

    _send_email(subject, body)
    _send_teams(subject, body, book_id)
    _log(book_id, event, extra)


def _build_body(subject: str, book_id: str, extra: dict = None) -> str:
    """Build body."""
    lines = [
        f"Event: {subject}",
        f"Book ID: {book_id}",
    ]

    if extra:
        for key, value in extra.items():
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

    lines.append("\nPlease log in to review and update the status before the pipeline can continue.")
    return "\n".join(lines)


def _send_email(subject: str, body: str):
    """Send email."""
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.smtp_user
        msg["To"] = settings.notify_email
        msg["Subject"] = f"[Book Generator] {subject}"
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.smtp_user, settings.notify_email, msg.as_string())

    except Exception as e:
        print(f"Email notification failed: {e}")


def _send_teams(subject: str, body: str, book_id: str):
    """Send teams."""
    if not settings.teams_webhook_url:
        return

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": subject,
        "sections": [{
            "activityTitle": f"?? Book Generator � {subject}",
            "activityText": body.replace("\n", "<br>"),
            "facts": [
                {"name": "Book ID", "value": book_id},
                {"name": "Event", "value": subject},
            ]
        }]
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            settings.teams_webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)

    except Exception as e:
        print(f"Teams notification failed: {e}")


def _log(book_id: str, event: str, extra: dict = None):
    """Log."""
    try:
        insert("notifications_log", {
            "book_id": book_id,
            "event_type": event,
            "channel": "email",
            "payload": extra or {},
        })
    except Exception as e:
        print(f"Notification log failed: {e}")