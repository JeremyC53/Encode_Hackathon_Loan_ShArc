import os
import base64
import re
import csv
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MAX_EMAILS = 100   # adjust if you want more / fewer


def get_service():
    """Authenticate and return a Gmail API service."""
    creds = None
    if os.path.exists(",,."):
        creds = Credentials.from_authorized_user_file("secrets/token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "secrets/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("secrets/token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def list_uber_emails(service):
    """
    List Uber weekly fare breakdown emails (most recent first).
    """
    # query = 'from:noreply@uber.com "your weekly fare breakdown"'
    query = 'from:seddiqazam@googlemail.com "your weekly fare breakdown"'
    results = service.users().messages().list(
        userId="me", q=query, maxResults=MAX_EMAILS
    ).execute()
    return results.get("messages", [])


def get_email_body(service, msg):
    """Return the email body as text (HTML preferred)."""
    msg_id = msg["id"]
    full_msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()
    payload = full_msg.get("payload", {})

    def _get_body_from_parts(parts):
        html = None
        text = None
        for part in parts:
            mime_type = part.get("mimeType", "")
            body = part.get("body", {})
            data = body.get("data")
            if data:
                decoded = base64.urlsafe_b64decode(data).decode(
                    "utf-8", errors="ignore"
                )
                if mime_type == "text/html":
                    html = (html or "") + decoded
                elif mime_type == "text/plain":
                    text = (text or "") + decoded

            if part.get("parts"):
                h, t = _get_body_from_parts(part["parts"])
                html = (html or "") + (h or "")
                text = (text or "") + (t or "")
        return html, text

    if "parts" not in payload:
        data = payload.get("body", {}).get("data")
        if not data:
            return "", full_msg
        return base64.urlsafe_b64decode(data).decode(
            "utf-8", errors="ignore"
        ), full_msg

    html, text = _get_body_from_parts(payload["parts"])
    return (html or text or ""), full_msg


def extract_earnings_amount(body_text):
    """
    Extract the earnings amount (e.g. '£829.30') from the mail body.
    """
    body_text = re.sub(r"\s+", " ", body_text)

    around = body_text
    m = re.search(r"Your earnings(.{0,400})", body_text, re.IGNORECASE)
    if m:
        around = m.group(1)

    m_amt = re.search(r"£\s*\d[\d,]*\.?\d*", around)
    if not m_amt:
        return None, None

    amount_str = m_amt.group(0).strip()
    digits = re.sub(r"[^\d.,]", "", amount_str).replace(",", "")

    try:
        value = float(digits)
    except ValueError:
        value = None

    return amount_str, value


def main():
    service = get_service()
    messages = list_uber_emails(service)

    if not messages:
        print("No Uber weekly fare breakdown emails found.")
        return

    rows = []

    for msg in messages:
        body, full_msg = get_email_body(service, msg)

        amount_str, value = extract_earnings_amount(body)
        if value is None:
            # skip emails where we can't find the earnings
            continue

        # internalDate is ms since epoch (string)
        internal_ms = int(full_msg.get("internalDate", "0"))
        dt = datetime.fromtimestamp(internal_ms / 1000.0)

        # format like 11-14-2025
        date_str = dt.strftime("%m-%d-%Y")

        rows.append((dt, date_str, value))

    # sort by date descending (most recent first)
    rows.sort(key=lambda r: r[0], reverse=True)

    # write CSV
    csv_path = "secrets/uber_earnings.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "earnings_gbp"])
        for _, date_str, value in rows:
            writer.writerow([date_str, value])

    # print to console in your requested format
    for _, date_str, value in rows:
        print(f"{date_str} {value}")


# if __name__ == "__main__":
#     main()
