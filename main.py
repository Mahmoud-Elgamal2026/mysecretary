import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- الإعدادات ---
SHEET_ID = "18uJrVBBjOOg51sReKhXdxmZdWnBsuAhZlEBda6K8JG8"

class SuperSecretary:
    def __init__(self):
        path = 'credentials.json'
        creds = service_account.Credentials.from_service_account_file(
            path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        self.service = build('sheets', 'v4', credentials=creds).spreadsheets()

    # 1. دالة إنشاء الصفحات وتنسيقها تلقائياً
    def auto_setup_sheets(self):
        metadata = self.service.get(spreadsheetId=SHEET_ID).execute()
        existing_sheets = [s['properties']['title'] for s in metadata['sheets']]
        
        # الصفحات اللي السكرتير محتاجها مع العناوين بتاعتها
        required_sheets = {
            "Tasks": ["ID", "المهمة", "الحالة", "التاريخ", "ملاحظات"],
            "Expenses": ["التاريخ", "المبلغ", "البند", "ملاحظات"],
            "Diet": ["اليوم", "فطار", "غداء", "عشاء", "سناك", "سعرات"],
            "Gym": ["اليوم", "التمرين", "المجموعات", "العدات", "الوزن"]
        }

        requests = []
        for name, headers in required_sheets.items():
            if name not in existing_sheets:
                # أمر إنشاء الصفحة
                requests.append({
                    'addSheet': {'properties': {'title': name}}
                })
        
        if requests:
            self.service.batchUpdate(spreadsheetId=SHEET_ID, body={'requests': requests}).execute()
            print(f"✅ تم إنشاء الصفحات الناقصة: {list(required_sheets.keys())}")

        # وضع العناوين (Headers) وتنسيقها
        for name, headers in required_sheets.items():
            self.service.values().update(
                spreadsheetId=SHEET_ID, range=f'{name}!A1:F1',
                valueInputOption='RAW', body={'values': [headers]}
            ).execute()
            # هنا ممكن أضيف كود لتلوين الصف الأول باللون الأزرق أو الأخضر تلقائياً

    # 2. دالة المسح الكامل لأي صفحة
    def clear_sheet(self, sheet_name):
        self.service.values().clear(spreadsheetId=SHEET_ID, range=f'{sheet_name}!A2:Z100').execute()
        return f"🧹 تم تنظيف صفحة {sheet_name} بالكامل يا حودة."

# تشغيل المحرك
secretary_engine = SuperSecretary()
secretary_engine.auto_setup_sheets() # دي هتظبطلك كل حاجة في الشيت أول ما تشغل الكود
