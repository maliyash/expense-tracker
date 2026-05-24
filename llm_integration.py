import os
import time
import random
from email.utils import parsedate_to_datetime
from typing import Literal

import psycopg2
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google import genai
from google.genai import types
from google.genai.errors import APIError
from datetime import datetime, timedelta

# Load environment variables (Supabase URL and Gemini Key)
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

BANK_CONFIGS = [
    {
        "name": "HDFC",
        "email": "alerts@hdfcbank.bank.in",
        "keywords": ["debited", '"UPI txn"', '"payment was made"', '"charge just happened"']
    },
    {
        "name": "IndusInd",
        "email": "transactionalert@indusind.com",
        "keywords": ['"transaction on your"', '"Approved"', '"for INR"']
    }
]


class TransactionDetails(BaseModel):
    # Notice: date_time is removed so the LLM cannot hallucinate years!
    amount: float = Field(description="The transaction amount as a float number.")
    merchant: str = Field(description="The clean name of the merchant or business paid.")
    category: str = Field(default="Uncategorized",
                          description="Spending category (e.g., Dining, Groceries, Utilities, Shopping).")
    payment_method: Literal['HDFC UPI', 'HDFC Credit Card', 'IndusInd Credit Card', 'Unknown'] = Field(
        description="You MUST pick exactly one of these options based on the context."
    )


def init_db():
    """Initializes the PostgreSQL database in Supabase."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Create table with Postgres syntax (TIMESTAMP and NUMERIC)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY,
                date_time TIMESTAMP NOT NULL,
                amount NUMERIC NOT NULL,
                merchant TEXT NOT NULL,
                category TEXT DEFAULT 'Uncategorized',
                payment_method TEXT,
                notes TEXT DEFAULT '',
                raw_snippet TEXT
            )
        ''')
        print("✅ Supabase Database verified/initialized.")
    except psycopg2.Error as e:
        print(f"❌ Failed to initialize Supabase DB: {e}")
    finally:
        conn.commit()
        conn.close()


def extract_transaction_info_with_retry(snippet: str, subject: str, bank_hint: str, from_email: str,
                                        max_retries=3) -> TransactionDetails:
    client = genai.Client()

    prompt = f"""
    Analyze this bank transaction notification text and extract the key details.

    Context Information:
    - Target Bank: {bank_hint}
    - Sender Email: {from_email}
    - Email Subject Line: {subject}
    - Message Snippet: {snippet}

    PAYMENT METHOD RULES:
    - If Sender Email contains 'hdfcbank' and the snippet mentions VPA, UPI, account, or paytm, it is 'HDFC UPI'.
    - If Sender Email contains 'hdfcbank' and snippet mentions Credit Card, it is 'HDFC Credit Card'.
    - If Sender Email contains 'indusind', it is 'IndusInd Credit Card'.
    """

    attempt = 0
    while attempt < max_retries:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TransactionDetails,
                    temperature=0.0  # Absolute zero creativity
                ),
            )
            return TransactionDetails.model_validate_json(response.text)

        except APIError as e:
            if e.code in [429, 500, 503]:
                attempt += 1
                if attempt == max_retries: raise e
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ Status ({e.code}). Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            else:
                raise e


def save_structured_expense(expense_id, details: TransactionDetails, raw_snippet, exact_datetime: str):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    try:
        # Postgres uses %s instead of ? and handles conflicts differently
        cursor.execute('''
            INSERT INTO expenses (id, date_time, amount, merchant, category, payment_method, raw_snippet)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', (
            expense_id, exact_datetime, details.amount,
            details.merchant, details.category, details.payment_method, raw_snippet
        ))

        if cursor.rowcount > 0:
            print(
                f"💾 [{exact_datetime}] Saved: {details.merchant:20} | ₹{details.amount:<7} | {details.payment_method}")
            return True
        return False
    except psycopg2.Error as e:
        print(f"❌ SQL Error: {e}")
        return False
    finally:
        conn.commit()
        conn.close()


def get_gmail_service():
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def build_gmail_query(configs, start_date: str, end_date: str) -> str:
    bank_queries = [f'(from:{b["email"]} ({" OR ".join(b["keywords"])}))' for b in configs]
    return f'after:{start_date} before:{end_date} ({" OR ".join(bank_queries)})'


def identify_bank(from_header: str) -> str:
    if "hdfc" in from_header.lower(): return "HDFC"
    if "indusind" in from_header.lower(): return "IndusInd"
    return "Unknown"


def main():
    init_db()
    service = get_gmail_service()

    # Generate dynamic dates: Look back 3 days, look forward 1 day (to ensure today is fully included)
    today = datetime.now()
    start_date_str = (today - timedelta(days=3)).strftime('%Y/%m/%d')
    end_date_str = (today + timedelta(days=1)).strftime('%Y/%m/%d')

    print(f"Searching Gmail from {start_date_str} to {end_date_str}...")

    query = build_gmail_query(BANK_CONFIGS, start_date_str, end_date_str)
    results = service.users().messages().list(userId='me', q=query, maxResults=100).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No recent transactions located.")
        return

    print(f"Syncing {len(messages)} transaction rows to Supabase using Gemini 2.5 Flash...")
    print("=" * 75)

    for message in messages:
        msg_id = message['id']

        msg = service.users().messages().get(userId='me', id=msg_id, format='metadata',
                                             metadataHeaders=['From', 'Subject', 'Date']).execute()
        headers = msg.get('payload', {}).get('headers', [])

        from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        date_header = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')
        snippet = msg.get('snippet', '')

        clean_email = from_header.split('<')[-1].replace('>', '').strip()
        bank_hint = identify_bank(from_header)

        try:
            dt_obj = parsedate_to_datetime(date_header)
            sql_safe_date = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            # Fallback to current time if email date parsing fails
            sql_safe_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            parsed_data = extract_transaction_info_with_retry(snippet, subject, bank_hint, clean_email)
            save_structured_expense(msg_id, parsed_data, snippet, exact_datetime=sql_safe_date)

        except Exception as e:
            print(f"❌ Processing stalled on row {msg_id}: {e}")


if __name__ == '__main__':
    main()