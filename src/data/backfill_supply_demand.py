#!/usr/bin/env python3
"""수급 환경 데이터(외국인 매매, USD/KRW 환율, 외국인 보유비율)를 백필하는 스크립트."""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import (
    get_latest_exchange_rate_date,
    get_latest_foreign_ownership_date,
    get_latest_foreign_trading_date,
    init_db,
    upsert_exchange_rate_bulk,
    upsert_foreign_ownership,
    upsert_foreign_trading_bulk,
)
from src.data.exchange_rate_fetcher import fetch_usdkrw_ohlc
from src.data.supply_demand import fetch_foreign_trading_all_pages


def backfill_foreign_data() -> None:
    """외국인 매매 + 보유비율 데이터를 한 번에 백필한다."""
    print("\n[1/2] 외국인 매매 + 보유비율 데이터 백필...")
    today = datetime.now().strftime("%Y-%m-%d")
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    latest_trading = get_latest_foreign_trading_date()
    latest_ownership = get_latest_foreign_ownership_date()

    # 두 테이블 중 더 오래된 날짜 기준으로 조회
    if latest_trading and latest_ownership:
        from_date = min(latest_trading, latest_ownership)
    elif latest_trading:
        from_date = latest_trading
    elif latest_ownership:
        from_date = latest_ownership
    else:
        from_date = one_year_ago

    if from_date >= today:
        print("  이미 최신 상태입니다.")
        return

    print(f"  조회 기간: {from_date} ~ {today}")
    trading_rows, ownership_rows = fetch_foreign_trading_all_pages(from_date, today)

    # 이미 저장된 날짜 이후 데이터만 필터링
    if latest_trading:
        trading_rows = [r for r in trading_rows if r["date"] > latest_trading]
    if latest_ownership:
        ownership_rows = [r for r in ownership_rows if r["date"] > latest_ownership]

    if trading_rows:
        upsert_foreign_trading_bulk(trading_rows)
        print(f"  외국인 매매: {len(trading_rows)}건 저장 ({trading_rows[0]['date']} ~ {trading_rows[-1]['date']})")
    else:
        print("  외국인 매매: 새로운 데이터 없음")

    if ownership_rows:
        for row in ownership_rows:
            upsert_foreign_ownership(row)
        print(f"  보유비율: {len(ownership_rows)}건 저장 ({ownership_rows[0]['date']} ~ {ownership_rows[-1]['date']})")
    else:
        print("  보유비율: 새로운 데이터 없음")


def backfill_exchange_rate() -> None:
    """USD/KRW 환율 데이터를 백필한다."""
    print("\n[2/2] USD/KRW 환율 데이터 백필...")
    today = datetime.now().strftime("%Y-%m-%d")
    latest = get_latest_exchange_rate_date()

    if latest:
        last_date = datetime.strptime(latest, "%Y-%m-%d")
        days_diff = (datetime.now() - last_date).days
        if days_diff <= 1:
            print("  이미 최신 상태입니다.")
            return
        from_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    print(f"  조회 기간: {from_date} ~ {today}")
    rows = fetch_usdkrw_ohlc(from_date=from_date, to_date=today)

    if not rows:
        print("  새로운 데이터가 없습니다.")
        return

    upsert_exchange_rate_bulk(rows)
    print(f"  {len(rows)}건 저장 완료 ({rows[0]['date']} ~ {rows[-1]['date']})")


def main():
    init_db()

    for task in [backfill_foreign_data, backfill_exchange_rate]:
        try:
            task()
        except Exception as e:
            print(f"  오류 발생: {e}")

    print("\n백필 완료.")


if __name__ == "__main__":
    main()
