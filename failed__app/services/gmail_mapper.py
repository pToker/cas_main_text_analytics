from failed__app.domain.email import Email
from datetime import datetime


def gmail_to_email(gmail_msg: dict) -> Email:
    headers = {h["name"]: h["value"] for h in gmail_msg["payload"]["headers"]}

    return Email(
        gmail_id=gmail_msg["id"],
        thread_id=gmail_msg["threadId"],
        sender=headers.get("From"),
        recipients=headers.get("To", "").split(", "),
        cc=headers.get("Cc", "").split(", ") if "Cc" in headers else [],
        bcc=headers.get("Bcc", "").split(", ") if "Bcc" in headers else [],
        subject=headers.get("Subject"),
        body_plain=extract_plain_body(gmail_msg),
        body_html=extract_html_body(gmail_msg),
        date_sent=datetime.fromtimestamp(int(gmail_msg["internalDate"]) / 1000),
        labels=gmail_msg.get("labelIds", []),
    )
