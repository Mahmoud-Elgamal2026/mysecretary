def delete_all_tasks():
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        sheet_id = None
        for sheet in sheet_metadata['sheets']:
            if sheet['properties']['title'] == TASKS_SHEET:
                sheet_id = sheet['properties']['sheetId']
                break
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f'{TASKS_SHEET}!A:A'
        ).execute()
        rows = result.get('values', [])
        if len(rows) <= 1:
            return "مفيش مهام تتحذف"
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={
                'requests': [{
                    'deleteDimension': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'ROWS',
                            'startIndex': 1,
                            'endIndex': len(rows)
                        }
                    }
                }]
            }
        ).execute()
        return f"✅ تم حذف كل المهام!"
    except Exception as e:
        return f"مش قادر أحذف: {e}"
