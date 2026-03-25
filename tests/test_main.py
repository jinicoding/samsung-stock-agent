"""main.py 일일 파이프라인 흐름 테스트 (DB/API 모킹)."""

from unittest.mock import MagicMock, patch

import pytest


# 테스트용 샘플 데이터
SAMPLE_PRICES = [
    {"date": f"2026-03-{d:02d}", "open": 55000, "high": 56000, "low": 54000, "close": 55000 + d * 100, "volume": 10000000}
    for d in range(1, 61)
]

SAMPLE_TRADING = [
    {"date": f"2026-03-{d:02d}", "institution": 100000, "foreign_total": 200000, "individual": -300000, "other_corp": 0}
    for d in range(1, 21)
]

SAMPLE_OWNERSHIP = [
    {"date": f"2026-03-{d:02d}", "listed_shares": 5969782550, "foreign_shares": 3000000000, "ownership_pct": 50.25, "limit_shares": 0, "exhaustion_pct": 0.0}
    for d in range(1, 21)
]

SAMPLE_INDICATORS = {
    "current_date": "2026-03-20",
    "current_price": 61000,
    "ma5": 60500,
    "ma20": 58000,
    "ma60": 55000,
    "price_vs_ma5_pct": 0.83,
    "price_vs_ma20_pct": 5.17,
    "price_vs_ma60_pct": 10.91,
    "change_1d_pct": 0.5,
    "change_5d_pct": 2.1,
    "change_20d_pct": 8.3,
    "volume_ratio_5d": 1.2,
}

SAMPLE_SD = {
    "foreign_consecutive_net_buy": 3,
    "foreign_consecutive_net_sell": 0,
    "institution_consecutive_net_buy": 2,
    "institution_consecutive_net_sell": 0,
    "foreign_cumulative_5d": 500000,
    "foreign_cumulative_20d": 2000000,
    "institution_cumulative_5d": 300000,
    "institution_cumulative_20d": 1000000,
    "ownership_trend": "increasing",
    "ownership_change_pct": 0.15,
    "overall_judgment": "buy_dominant",
}

SAMPLE_RATES = [
    {"date": f"2026-03-{d:02d}", "open": 1380.0, "high": 1385.0, "low": 1375.0, "close": 1380.0 + d * 0.5}
    for d in range(1, 31)
]

SAMPLE_ER = {
    "current_date": "2026-03-30",
    "current_rate": 1395.0,
    "change_1d_pct": 0.1,
    "change_5d_pct": 0.5,
    "change_20d_pct": 1.0,
    "ma5": 1392.0,
    "ma20": 1385.0,
    "trend": "원화약세",
    "correlation_20d": -0.3,
}

SAMPLE_SIGNAL = {
    "score": 35.0,
    "grade": "매수우세",
    "technical_score": 40.0,
    "supply_score": 50.0,
    "exchange_score": -10.0,
    "weights": {"technical": 40, "supply": 40, "exchange": 20},
}

SAMPLE_SR = {
    "pivot": {"pp": 55500.0, "s1": 55000.0, "s2": 54500.0, "r1": 56000.0, "r2": 56500.0},
    "swing_levels": [],
    "ma_levels": {"ma20": 58000.0, "ma60": 55000.0},
    "nearest_support": 55000.0,
    "nearest_resistance": 58000.0,
}

SAMPLE_REPORT_HTML = "<b>삼성전자 일일 분석</b>"


@patch("src.main.send_message")
@patch("src.main.generate_daily_report", return_value=SAMPLE_REPORT_HTML)
@patch("src.main.upsert_signal_history")
@patch("src.main.compute_composite_signal", return_value=SAMPLE_SIGNAL)
@patch("src.main.analyze_support_resistance", return_value=SAMPLE_SR)
@patch("src.main.analyze_exchange_rate", return_value=SAMPLE_ER)
@patch("src.main.analyze_supply_demand", return_value=SAMPLE_SD)
@patch("src.main.compute_technical_indicators", return_value=SAMPLE_INDICATORS)
@patch("src.main.get_exchange_rates", return_value=SAMPLE_RATES)
@patch("src.main.get_foreign_ownership", return_value=SAMPLE_OWNERSHIP)
@patch("src.main.get_foreign_trading", return_value=SAMPLE_TRADING)
@patch("src.main.get_prices", return_value=SAMPLE_PRICES)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_full(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_signal, mock_upsert_sig, mock_report, mock_send,
):
    """전체 파이프라인: 백필→조회→분석→지지저항→시그널→기록→리포트→발송."""
    from src.main import main

    main()

    mock_init.assert_called_once()
    mock_bf_prices.assert_called_once()
    mock_bf_sd.assert_called_once()
    mock_prices.assert_called_once_with(60)
    mock_trading.assert_called_once_with(20)
    mock_ownership.assert_called_once_with(20)
    mock_rates.assert_called_once_with(30)
    mock_tech.assert_called_once_with(SAMPLE_PRICES)
    mock_sd.assert_called_once_with(SAMPLE_TRADING, SAMPLE_OWNERSHIP)
    mock_er.assert_called_once_with(SAMPLE_RATES, SAMPLE_PRICES)
    mock_sr.assert_called_once_with(SAMPLE_PRICES)
    mock_signal.assert_called_once_with(SAMPLE_INDICATORS, SAMPLE_SD, SAMPLE_ER)
    mock_upsert_sig.assert_called_once_with(
        date="2026-03-60", score=35.0, grade="매수우세",
        technical_score=40.0, supply_score=50.0, exchange_score=-10.0,
        price=61000,
    )
    mock_report.assert_called_once_with(SAMPLE_INDICATORS, supply_demand=SAMPLE_SD, exchange_rate=SAMPLE_ER, composite_signal=SAMPLE_SIGNAL, support_resistance=SAMPLE_SR)
    mock_send.assert_called_once_with(SAMPLE_REPORT_HTML)


@patch("src.main.send_message")
@patch("src.main.generate_daily_report", return_value=SAMPLE_REPORT_HTML)
@patch("src.main.upsert_signal_history")
@patch("src.main.compute_composite_signal", return_value=SAMPLE_SIGNAL)
@patch("src.main.analyze_support_resistance", return_value=SAMPLE_SR)
@patch("src.main.analyze_exchange_rate", return_value=SAMPLE_ER)
@patch("src.main.analyze_supply_demand", return_value=SAMPLE_SD)
@patch("src.main.compute_technical_indicators", return_value=SAMPLE_INDICATORS)
@patch("src.main.get_exchange_rates", return_value=SAMPLE_RATES)
@patch("src.main.get_foreign_ownership", return_value=SAMPLE_OWNERSHIP)
@patch("src.main.get_foreign_trading", return_value=SAMPLE_TRADING)
@patch("src.main.get_prices", return_value=SAMPLE_PRICES)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_dry_run(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_signal, mock_upsert_sig, mock_report, mock_send,
    capsys,
):
    """--dry-run: 리포트를 stdout에 출력하고 발송하지 않는다."""
    from src.main import main

    main(dry_run=True)

    mock_report.assert_called_once()
    mock_send.assert_not_called()
    captured = capsys.readouterr()
    assert SAMPLE_REPORT_HTML in captured.out


@patch("src.main.generate_daily_report")
@patch("src.main.get_prices", return_value=[])
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_no_prices_skips_report(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_prices, mock_report,
):
    """주가 데이터가 없으면 리포트를 생성하지 않는다."""
    from src.main import main

    main()

    mock_prices.assert_called_once_with(60)
    mock_report.assert_not_called()
