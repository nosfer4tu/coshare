"""
seed_verified_checks.py — verified_checks_data.json の照合記録を Neon の verified_checks に登録する

使い方:
  python3 seed_verified_checks.py --dry-run   # 検証と登録予定の表示のみ(DBには接続しない)
  python3 seed_verified_checks.py             # 実際に登録

動作:
  - "example": true のエントリは無視する
  - 全レコードを validate_check で検証し、1件でも不正なら何も登録せず終了する
  - 登録前に (route, flight_date, carrier_checked, sandbox_source, check_date) で
    SELECT し、既存なら skip する(再実行しても重複しない)
  - INSERT は1トランザクション。途中で失敗したら全件ロールバックする
  - --dry-run は DB に接続しないため、既存行との重複は判定できない
    (ファイル内の重複のみ検出する)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "api" / "_lib"))

from verified_checks import validate_check  # noqa: E402

DATA_FILE = ROOT / "verified_checks_data.json"

DUPLICATE_KEY_FIELDS = ("route", "flight_date", "carrier_checked", "sandbox_source", "check_date")
INSERT_FIELDS = (
    "route", "check_date", "flight_date", "carrier_checked", "sandbox_source",
    "sandbox_price_jpy", "real_price_jpy", "real_source_url", "verdict", "notes",
)


def load_records(path=DATA_FILE):
    """Return the records to seed: the 'checks' list without example entries."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    checks = data.get("checks", [])
    return [c for c in checks if not (isinstance(c, dict) and c.get("example") is True)]


def duplicate_key(record):
    return tuple(record.get(f) for f in DUPLICATE_KEY_FIELDS)


def main():
    parser = argparse.ArgumentParser(description="Seed the verified_checks table from verified_checks_data.json")
    parser.add_argument("--dry-run", action="store_true", help="print what would be inserted; do not touch the database")
    args = parser.parse_args()

    records = load_records()
    if not records:
        print("No records to seed (only example entries or an empty 'checks' list).")
        return 0

    failed = False
    for i, record in enumerate(records, start=1):
        errors = validate_check(record)
        if errors:
            failed = True
            print(f"[invalid] record #{i}:")
            for e in errors:
                print(f"    - {e}")
    if failed:
        print("Nothing was inserted: fix the invalid records above.")
        return 1

    if args.dry_run:
        seen = set()
        for record in records:
            key = duplicate_key(record)
            if key in seen:
                print(f"[dry-run] would skip (duplicate within file): {key}")
                continue
            seen.add(key)
            print(f"[dry-run] would insert: {json.dumps({f: record.get(f) for f in INSERT_FIELDS}, ensure_ascii=False)}")
        print("[dry-run] database not contacted; existing rows were not checked.")
        return 0

    from db import get_db  # imported here so --dry-run never loads DB config

    select_sql = (
        "SELECT 1 FROM verified_checks "
        "WHERE route = %s AND flight_date = %s AND carrier_checked = %s "
        "AND sandbox_source = %s AND check_date = %s"
    )
    insert_sql = (
        f"INSERT INTO verified_checks ({', '.join(INSERT_FIELDS)}) "
        f"VALUES ({', '.join(['%s'] * len(INSERT_FIELDS))})"
    )

    inserted = skipped = 0
    with get_db() as (conn, cursor):
        for record in records:
            cursor.execute(select_sql, duplicate_key(record))
            if cursor.fetchone():
                skipped += 1
                print(f"[skip] already exists: {duplicate_key(record)}")
                continue
            cursor.execute(insert_sql, tuple(record.get(f) for f in INSERT_FIELDS))
            inserted += 1
            print(f"[insert] {duplicate_key(record)}")
        conn.commit()
    print(f"Done: {inserted} inserted, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
