from groq import Groq
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, JobQueue
import requests
from datetime import datetime
import pytz
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TELEGRAM_TOKEN = "8569606909:AAEdLS1E5aruUZW60EPDThrWyGIsCUQlBNs"
GROQ_KEY = "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"
WEATHER_KEY = "4878e67a8ae538cb3737137a422ccdc9"
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"
MAHMOUD_CHAT_ID = None

client = Groq(api_key=GROQ_KEY)
conversation_history = []

def get_google_creds():
    token_data = json.loads(os.environ.get('GOOGLE_TOKEN', '{}'))
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes')
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def get_tasks():
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='A:C'
        ).execute()
        rows = result.get('values', [])
        if len(rows) <= 1:
            return "مفيش مهام دلوقتي"
        tasks = ""
        for i, row in enumerate(rows[1:], 1):
            task = row[0] if len(row) > 0 else ""
            status = row[1] if len(row) > 1 else "جديدة"
            date = row[2] if len(row) > 2 else ""
            tasks += f"{i}. {task} | {status} | {date}\n"
        return tasks
    except Exception as e:
        return f"مش قادر اوصل للمهام: {e}"

def add_task(task, date=""):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range='A:C',
            valueInputOption='RAW',
            body={'values': [[task, 'جديدة', date]]}
        ).execute()
        return f"✅ تمت إضافة المهمة: {task}"
    except Exception as e:
        return f"مش قادر أضيف: {e}"

def complete_task(task_num):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f'B{task_num+1}',
            valueInputOption='RAW',
            body={'values': [['✅ منتهية']]}
        ).execute()
        return f"✅ تم إنهاء المهمة رقم {task_num}"
    except Exception as e:
        return f"مش قادر أحدث: {e}"

def delete_task(task_num):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={
                'requests': [{
                    'deleteDimension': {
                        'range': {
                            'sheetId': 0,
                            'dimension': 'ROWS',
                            'startIndex': task_num,
                            'endIndex': task_num + 1
                        }
                    }
                }]
            }
        ).execute()
        return f"✅ تم حذف المهمة رقم {task_num}"
    except Exception as e:
        return f"مش قادر أحذف: {e}"

def get_gmail_summary():
    try:
        creds = get_google_creds()
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=5
        ).execute()
        messages = results.get('messages', [])
        if not messages:
            return "مفيش إيميلات جديدة"
        return f"عندك {len(messages)} إيميل جديد"
    except Exception as e:
        return f"مش قادر اوصل للإيميل: {e}"

def get_calendar
