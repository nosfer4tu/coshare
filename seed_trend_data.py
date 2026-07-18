"""
seed_trend_data.py — TrendPage用の価格履歴データを事前収集するスクリプト

目的:
  デモ路線(例: KIX→TPE)の検索を日付を変えて繰り返し実行し、
  Neon DB に価格履歴を蓄積して TrendPage のチャートを充実させる。

前提:
  - local_server.py (Flask) が起動していること: python3 local_server.py
  - Duffel はテストモード(検索は無料)
  - 各検索はアプリの通常フローを通るので、キャッシュ・価格履歴の
    保存ロジックがそのまま働く

使い方:
  1. 下の CONFIG を自分の環境に合わせて調整
     (特に SEARCH_ENDPOINT のパスとリクエスト形式は
      フロントエンドが呼んでいる実際の /api/ パスに合わせること。
      Chrome DevTools の Network タブで確認できる)
  2. python3 seed_trend_data.py を実行
  3. 完了後、TrendPage を開いてチャートを確認

注意:
  - 日付が違えばキャッシュキーも違うので、全リクエストが
    実際に Duffel まで到達する(=履歴が保存される)はず
  - 再実行しても同じ日付はキャッシュに当たるだけなので安全
"""

import time
import requests
from datetime import date

# ============ CONFIG(自分の環境に合わせて調整)============

BASE_URL = "http://127.0.0.1:8000"
SEARCH_ENDPOINT = "/api/flights/search"

ORIGIN = "KIX"
DESTINATION = "TPE"
CABIN_CLASS = "economy"
PASSENGERS = "adult"

# 何月から何ヶ月分を収集するか
START_YEAR = 2026
START_MONTH = 8
NUM_MONTHS = 12

# 各月の何日を検索するか(月内のばらつきを出すため複数日)
# 祝日効果を見せたいなら、お盆(8/13前後)・年末(12/29前後)・
# GW(5/3前後)が含まれる日付を意識して選ぶとよい
DAYS_OF_MONTH = [5, 13, 21, 28]

# リクエスト間の待機秒数(サーバーと Duffel への礼儀)
DELAY_SECONDS = 2

# ==========================================================


def month_iter(start_year: int, start_month: int, count: int):
    """(year, month) を count ヶ月分順に返す"""
    y, m = start_year, start_month
    for _ in range(count):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def build_dates():
    dates = []
    for y, m in month_iter(START_YEAR, START_MONTH, NUM_MONTHS):
        for d in DAYS_OF_MONTH:
            try:
                dates.append(date(y, m, d).isoformat())
            except ValueError:
                pass  # 例: 2月30日はスキップ
    return dates


def run():
    dates = build_dates()
    total = len(dates)
    ok, failed = 0, 0

    print(f"シード開始: {ORIGIN}→{DESTINATION}, {total}件の検索")
    print("-" * 50)

    for i, dep_date in enumerate(dates, 1):
        params = {
            "origin": ORIGIN,
            "destination": DESTINATION,
            "departureDate": dep_date,
            "passengers": PASSENGERS,
            "cabinClass": CABIN_CLASS,
        }
        try:
            r = requests.get(
                BASE_URL + SEARCH_ENDPOINT,
                params=params,
                timeout=60,
            )
            if r.status_code == 200:
                ok += 1
                print(f"[{i}/{total}] {dep_date}  OK")
            else:
                failed += 1
                print(f"[{i}/{total}] {dep_date}  NG (HTTP {r.status_code})")
                print("   URL :", r.url)
                print("   BODY:", r.text[:200])
        except requests.RequestException as e:
            failed += 1
            print(f"[{i}/{total}] {dep_date}  ERROR: {e}")

        time.sleep(DELAY_SECONDS)

    print("-" * 50)
    print(f"完了: 成功 {ok} / 失敗 {failed}")
    print("TrendPage を開いてチャートを確認してください。")


if __name__ == "__main__":
    run()