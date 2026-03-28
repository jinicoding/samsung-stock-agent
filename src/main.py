"""Samsung Electronics stock analysis agent — daily pipeline.

수집 → 분석 → 리포트 → 발송 파이프라인을 오케스트레이션한다.
--dry-run 옵션으로 발송 없이 리포트만 확인 가능.
"""

import argparse

from src.data.backfill import main as backfill_prices
from src.data.backfill_supply_demand import main as backfill_supply_demand
from src.data.database import (
    get_exchange_rates,
    get_foreign_ownership,
    get_foreign_trading,
    get_prices,
    init_db,
    upsert_signal_history,
)
from src.analysis.technical import compute_technical_indicators
from src.analysis.supply_demand import analyze_supply_demand
from src.analysis.exchange_rate import analyze_exchange_rate
from src.analysis.report import generate_daily_report
from src.analysis.signal import compute_composite_signal
from src.analysis.support_resistance import analyze_support_resistance
from src.analysis.trend_reversal import detect_reversal_signals
from src.analysis.accuracy import evaluate_signals
from src.analysis.relative_strength import compute_relative_strength
from src.analysis.signal_trend import analyze_signal_trend
from src.data.kospi_index import fetch_kospi_ohlcv
from src.delivery.telegram_bot import send_message


def main(dry_run: bool = False):
    """일일 파이프라인: 백필 → 분석 → 리포트 → 발송."""
    # 1) DB 초기화 + 데이터 백필
    init_db()

    try:
        backfill_prices()
    except Exception as e:
        print(f"[경고] 주가 백필 실패: {e}")

    try:
        backfill_supply_demand()
    except Exception as e:
        print(f"[경고] 수급 백필 실패: {e}")

    # 2) DB에서 데이터 조회
    prices = get_prices(60)
    if not prices:
        print("주가 데이터가 없습니다. 리포트를 생성하지 않습니다.")
        return

    trading = get_foreign_trading(20)
    ownership = get_foreign_ownership(20)
    rates = get_exchange_rates(30)

    # 3) 분석 실행
    indicators = compute_technical_indicators(prices)
    sd = analyze_supply_demand(trading, ownership) if trading else None
    er = analyze_exchange_rate(rates, prices) if rates else None

    # 3.5) 지지/저항선 분석
    sr = analyze_support_resistance(prices)

    # 3.6) KOSPI 지수 수집 → 상대강도 분석
    rs = None
    try:
        kospi_data = fetch_kospi_ohlcv()
        if kospi_data:
            samsung_closes = [p["close"] for p in prices]
            kospi_closes = [k["close"] for k in kospi_data]
            # 길이를 짧은 쪽에 맞춤 (날짜 정렬 기준 최근 N일)
            min_len = min(len(samsung_closes), len(kospi_closes))
            rs = compute_relative_strength(
                samsung_closes[-min_len:], kospi_closes[-min_len:]
            )
    except Exception as e:
        print(f"[경고] KOSPI/RS 분석 실패: {e}")

    # 3.7) 추세 전환 감지
    reversal = detect_reversal_signals(indicators, sr)

    # 3.8) 종합 투자 시그널
    sig = compute_composite_signal(indicators, sd or {}, er or {}, relative_strength=rs, trend_reversal=reversal)

    # 3.9) 시그널 이력 저장
    latest_price = prices[-1]["close"]
    latest_date = prices[-1]["date"]
    upsert_signal_history(
        date=latest_date,
        score=sig["score"],
        grade=sig["grade"],
        technical_score=sig["technical_score"],
        supply_score=sig["supply_score"],
        exchange_score=sig["exchange_score"],
        price=latest_price,
    )

    # 3.10) 시그널 정확도 평가
    from src.data import database as db_module
    accuracy_result = evaluate_signals(db_module)
    accuracy_summary = accuracy_result["summary"]

    # 3.11) 시그널 추이 분석
    sig_trend = analyze_signal_trend(db_module, days=5)

    # 4) 리포트 생성
    report = generate_daily_report(indicators, supply_demand=sd, exchange_rate=er, composite_signal=sig, support_resistance=sr, accuracy_summary=accuracy_summary, relative_strength=rs, trend_reversal=reversal, signal_trend=sig_trend)

    # 5) 발송 또는 출력
    if dry_run:
        print(report)
    else:
        send_message(report)
        print("리포트 발송 완료.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="삼성전자 일일 분석 파이프라인")
    parser.add_argument("--dry-run", action="store_true", help="발송 없이 리포트만 출력")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
