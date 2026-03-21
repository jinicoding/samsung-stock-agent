#!/usr/bin/env python3
"""삼성전자 OHLCV 과거 데이터를 SQLite DB에 백필하는 스크립트."""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import get_latest_date, init_db, upsert_bulk
from src.data.stock_price import fetch_samsung_ohlcv


def main():
    init_db()

    latest = get_latest_date()
    today = datetime.now().strftime("%Y-%m-%d")

    if latest is None:
        print("DB가 비어있습니다. 1년치 데이터를 조회합니다...")
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        rows = fetch_samsung_ohlcv(from_date=one_year_ago, to_date=today)
    else:
        print(f"마지막 저장일: {latest}")
        if latest >= today:
            print("이미 최신 상태입니다.")
            return
        # 당일 장중 데이터도 가져오기 위해 latest 날짜부터 재조회 (upsert로 덮어씀)
        rows = fetch_samsung_ohlcv(from_date=latest, to_date=today)

    if not rows:
        print("새로운 데이터가 없습니다.")
        return

    upsert_bulk(rows)
    print(f"{len(rows)}건 저장 완료 ({rows[0]['date']} ~ {rows[-1]['date']})")


if __name__ == "__main__":
    main()
