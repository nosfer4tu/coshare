JAPANESE_HOLIDAYS = [
    {"name": "ゴールデンウィーク", "start": "04-29", "end": "05-06"},
    {"name": "お盆", "start": "08-13", "end": "08-15"},
    {"name": "年末年始", "start": "12-29", "end": "01-03"}
]

def detect_holiday(date):
    for holiday in JAPANESE_HOLIDAYS:
        if holiday["start"] <= date[5:] <= holiday["end"]:
            return holiday["name"]
        pass
    return None