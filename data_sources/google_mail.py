import os
import base64
import re
import csv
import json
from datetime import datetime
import io
from supabase import create_client, Client 


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MAX_EMAILS = 100   # adjust if you want more / fewer

SUPABASE_URL = f"https://{os.environ['SUPABASE_ID']}.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_KEY"]

SUPABASE_BUCKET_NAME = "earnings"  # the bucket you created

_supabase_client = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_client



def get_service():
    """Authenticate and return a Gmail API service."""
    creds = None
    if os.path.exists("secrets/token.json"):
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

def list_fiverr_emails(service):
    """
    List Uber weekly fare breakdown emails (most recent first).
    """
    query = 'from:noreply@e.fiverr.com "received an order from"'
    # query = 'from:wdeva22@gmail.com "received an order from"'
    results = service.users().messages().list(
        userId="me", q=query, maxResults=MAX_EMAILS
    ).execute()
    return results.get("messages", [])

def list_upwork_emails(service):
    """
    List Uber weekly fare breakdown emails (most recent first).
    """
    query = 'from:donotreply@upwork.com "Your payment has been processed"'
    # query = 'from:wdeva22@gmail.com "Your payment has been processed"'
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


# def extract_earnings_amount(body_text):
    """
    Extract the earnings amount (e.g. '£829.30') from the mail body.
    Returns (amount_string_with_pound, numeric_value)
    """
    body_text = re.sub(r"\s+", " ", body_text)

    # Limit search window around "Your earnings"
    m = re.search(r"Your earnings(.{0,400})", body_text, re.IGNORECASE)
    around = m.group(1) if m else body_text

    # Find a £-prefixed amount
    m_amt = re.search(r"£\s*\d[\d,]*\.?\d*", around)
    if not m_amt:
        return None, None

    amount_str = m_amt.group(0).strip()  # This keeps the £ symbol

    # Extract digits only for numeric conversion
    digits = re.sub(r"[^\d.,]", "", amount_str).replace(",", "")

    try:
        value = float(digits)
    except ValueError:
        value = None

    return amount_str, value

def upload_with_versioning(bucket, base_name, file_bytes, content_type="application/json"):
    """
    Uploads file to Supabase Storage.
    Always appends _1, _2, _3... (no plain filename).
    Returns the final filename used.
    """
    supabase = get_supabase_client()

    # Split filename + extension
    if "." in base_name:
        name_without_ext, ext = base_name.rsplit(".", 1)
    else:
        name_without_ext, ext = base_name, ""

    attempt = 1  # start from 1 so first file gets _1

    while True:
        candidate = f"{name_without_ext}_{attempt}.{ext}" if ext else f"{name_without_ext}_{attempt}"

        try:
            supabase.storage.from_(bucket).upload(
                candidate,
                file_bytes,
                {"content-type": content_type}
            )
            return candidate  # upload succeeded

        except Exception as e:
            if "exists" in str(e) or "Duplicate" in str(e):
                attempt += 1  # try next suffix
            else:
                raise


def extract_currency_amount(body_text, context_pattern=None):
    """
    Generic currency extractor.

    Returns (amount_str, symbol, value_float) or (None, None, None) on failure.

    - amount_str: e.g. '£829.30', '$39.51'
    - symbol: e.g. '£', '$'
    - value_float: e.g. 829.30
    """
    if not body_text:
        return None, None, None

    # collapse whitespace
    body_text = re.sub(r"\s+", " ", body_text)

    search_region = body_text

    # If a context pattern is provided, look near that first
    if context_pattern:
        m = re.search(context_pattern, body_text, re.IGNORECASE)
        if m:
            # if the pattern has a capture group, use it;
            # otherwise just use the whole match
            if m.lastindex:
                search_region = m.group(1)
            else:
                search_region = m.group(0)

    # Look for currency symbol + amount
    m_amt = re.search(r"([£$€])\s*\d[\d,]*\.?\d*", search_region)
    if not m_amt:
        # fallback: try anywhere in the email
        m_amt = re.search(r"([£$€])\s*\d[\d,]*\.?\d*", body_text)
        if not m_amt:
            return None, None, None

    amount_str = m_amt.group(0).strip()
    symbol = m_amt.group(1)

    # Normalize numeric part for float
    digits = re.sub(r"[^\d.,]", "", amount_str).replace(",", "")
    try:
        value = float(digits)
    except ValueError:
        value = None

    return amount_str, symbol, value

def main():
    print("service started")
    service = get_service()
    uber_messages = list_uber_emails(service)

    rows = []

    for msg in uber_messages:
        body, full_msg = get_email_body(service, msg)

        # amount_str, value = extract_earnings_amount(body)
        amount_str, symbol, value = extract_currency_amount(
            body, context_pattern=r"Your earnings(.{0,400})"
        )
        if value is None:
            # skip emails where we can't find the earnings
            continue

        # internalDate is ms since epoch (string)
        internal_ms = int(full_msg.get("internalDate", "0"))
        dt = datetime.fromtimestamp(internal_ms / 1000.0)

        # format like 11-14-2025
        date_str = dt.strftime("%m-%d-%Y")
        company = "Uber"
        rows.append((dt, date_str, company, amount_str))

    fiverr_messages = list_fiverr_emails(service)

    for msg in fiverr_messages:
        body, full_msg = get_email_body(service, msg)

        # amount_str, value = extract_earnings_amount(body)
        amount_str, symbol, value = extract_currency_amount(
            body, context_pattern=r"Total(.{0,120})"
        )
        if value is None:
            # skip emails where we can't find the earnings
            continue

        # internalDate is ms since epoch (string)
        internal_ms = int(full_msg.get("internalDate", "0"))
        dt = datetime.fromtimestamp(internal_ms / 1000.0)

        # format like 11-14-2025
        date_str = dt.strftime("%m-%d-%Y")
        company = "Fiverr"
        rows.append((dt, date_str, company, amount_str))

    upwork_messages = list_upwork_emails(service)

    for msg in upwork_messages:
        body, full_msg = get_email_body(service, msg)

        # amount_str, value = extract_earnings_amount(body)
        amount_str, symbol, value = extract_currency_amount(
            body, context_pattern=r"Amount paid(.{0,120})"
        )
        if value is None:
            # skip emails where we can't find the earnings
            continue

        # internalDate is ms since epoch (string)
        internal_ms = int(full_msg.get("internalDate", "0"))
        dt = datetime.fromtimestamp(internal_ms / 1000.0)

        # format like 11-14-2025
        date_str = dt.strftime("%m-%d-%Y")
        company = "Upwork"
        rows.append((dt, date_str, company, amount_str))


    # sort by date descending (most recent first)
        # sort by date descending (most recent first)
    rows.sort(key=lambda r: r[0], reverse=True)

        # ---------------------------------------------
    # Build filename {hash}_earnings_{YYYYMMDD}.json
    # ---------------------------------------------
    hash_value = "dummy"  # later get from API
    today_str = datetime.today().strftime("%Y%m%d")
    filename = f"{hash_value}_earnings_{today_str}.json"

    # ---------------------------------------------
    # Convert rows into JSON-serializable list
    # ---------------------------------------------
    json_rows = []
    for _, date_str, company, amount_str in rows:
        json_rows.append({
            "date": date_str,
            "company": company,
            "earnings": amount_str
        })

    json_bytes = json.dumps(json_rows, indent=2, ensure_ascii=False).encode("utf-8")


    # ---------------------------------------------
    # Upload JSON to Supabase Storage
    # ---------------------------------------------

    final_path = upload_with_versioning(
        SUPABASE_BUCKET_NAME,
        filename,
        json_bytes,
        content_type="application/json"
    )

    print("File saved to:", final_path)


    # Optional: still print to console
    for row in json_rows:
        print(f"{row['date']} {row['company']} {row['earnings']}")


    # # ---------------------------------------------
    # # Build filename: {hash}_earnings_{YYYYMMDD}.csv
    # # ---------------------------------------------
    # hash_value = "dummy"  # later this can come from your API
    # today_str = datetime.today().strftime("%Y%m%d")
    # filename = f"{hash_value}_earnings_{today_str}.csv"

    # # ---------------------------------------------
    # # Write CSV to an in-memory buffer
    # # ---------------------------------------------
    # csv_buffer = io.StringIO()
    # writer = csv.writer(csv_buffer)
    # writer.writerow(["date", "company", "earnings"])
    # for _, date_str, company, amount_str in rows:
    #     writer.writerow([date_str, company, amount_str])

    # csv_bytes = csv_buffer.getvalue().encode("utf-8")

    # # ---------------------------------------------
    # # Upload CSV to Supabase Storage
    # # ---------------------------------------------
    # supabase = get_supabase_client()
    # storage_path = filename  # or e.g. f"{hash_value}/{filename}" if you want folders

    # # Note: if a file with same name exists, .upload will error;
    # # you can handle that or use .update() depending on your needs.
    # supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
    #     storage_path,
    #     csv_bytes,
    #     {"content-type": "text/csv"}
    # )
    #     # After the upload succeeds:
    # supabase.table("earnings_exports").insert({
    #     "hash": hash_value,
    #     "filename": filename,
    #     "storage_path": storage_path
    # }).execute()

    # # ---------------------------------------------
    # # (Optional) also write locally if you still want a local copy
    # # ---------------------------------------------
    # csv_path = os.path.join("secrets", filename)
    # with open(csv_path, "wb") as f:
    #     f.write(csv_bytes)

    # # print to console in your requested format
    # for _, date_str, company, amount_str in rows:
    #     print(f"{date_str} {company} {amount_str}")



# if __name__ == "__main__":
#     main()
