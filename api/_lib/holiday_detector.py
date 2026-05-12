from datetime import datetime
JAPANESE_HOLIDAYS = [
    {"name": "ゴールデンウィーク", "start": "04-29", "end": "05-06"},
    {"name": "お盆", "start": "08-13", "end": "08-15"},
    {"name": "年末年始", "start": "12-29", "end": "01-03"}
]
def detect_holiday(date):
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")
    
    year = date.year
    if date.month == 1:
            year -= 1
    for holiday in JAPANESE_HOLIDAYS:
        start_date = datetime.strptime(f"{year}-{holiday['start']}", "%Y-%m-%d")
        end_date = datetime.strptime(f"{year}-{holiday['end']}", "%Y-%m-%d")
        
        if end_date.month < start_date.month:
            end_date = end_date.replace(year=year + 1)
        
        if start_date <= date <= end_date:
            return holiday
    return None