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

SAMPLE_ACCURACY = {
    "total_signals": 10,
    "hit_rate_1d": 60.0,
    "hit_rate_3d": 55.0,
    "hit_rate_5d": 50.0,
    "avg_return_1d": 0.2,
    "avg_return_3d": 0.5,
    "avg_return_5d": 0.8,
    "evaluated_signals_1d": 8,
    "evaluated_signals_3d": 7,
    "evaluated_signals_5d": 5,
}

SAMPLE_RS = {
    "samsung_return_1d": 0.5,
    "samsung_return_5d": 2.0,
    "samsung_return_20d": 5.0,
    "kospi_return_1d": 0.3,
    "kospi_return_5d": 1.5,
    "kospi_return_20d": 4.0,
    "alpha_1d": 0.2,
    "alpha_5d": 0.5,
    "alpha_20d": 1.0,
    "rs_current": 21.5,
    "rs_ma20": 21.0,
    "rs_trend": "outperform",
}

SAMPLE_KOSPI = [
    {"date": f"2026-03-{d:02d}", "open": 2500.0, "high": 2520.0, "low": 2480.0, "close": 2500.0 + d * 1.0, "volume": 500000}
    for d in range(1, 61)
]

SAMPLE_RAW_FUNDAMENTALS = {
    "per": 12.5, "eps": 4800, "estimated_per": 10.0, "estimated_eps": 6000,
    "pbr": 1.2, "bps": 45000, "dividend_yield": 2.0,
}

SAMPLE_FUNDAMENTALS = {
    **SAMPLE_RAW_FUNDAMENTALS,
    "per_valuation": "적정",
    "pbr_valuation": "적정",
    "earnings_outlook": "개선",
    "dividend_attractiveness": "보통",
}

SAMPLE_NEWS_HEADLINES = [
    {"title": "삼성전자 실적 상승 기대", "source": "한경", "date": "2026-03-29", "sentiment": "positive"},
    {"title": "반도체 업황 우려", "source": "매경", "date": "2026-03-29", "sentiment": "negative"},
    {"title": "삼성전자 주주환원", "source": "조선", "date": "2026-03-29", "sentiment": "neutral"},
]

SAMPLE_NEWS_SENTIMENT = {
    "label": "neutral",
    "score": 0,
    "positive": 1,
    "negative": 1,
    "neutral": 1,
    "count": 3,
}

SAMPLE_RAW_CONSENSUS = {
    "target_price": 252720.0,
    "recommendation": 4.2,
    "researches": [
        {"title": "삼성전자 목표가 상향", "broker": "삼성증권", "date": "2026-03-28"},
    ],
}

SAMPLE_CONSENSUS = {
    "target_price": 252720.0,
    "current_price": 61000,
    "divergence_pct": 314.3,
    "valuation": "저평가",
    "recommendation": 4.2,
    "recommendation_label": "매수유지",
    "researches": SAMPLE_RAW_CONSENSUS["researches"],
    "research_tone": "긍정",
}

SAMPLE_REPORT_HTML = "<b>삼성전자 일일 분석</b>"

SAMPLE_REVERSAL = {
    "direction": "bullish",
    "convergence": "moderate",
    "score": 60.0,
    "active_categories": 3,
    "category_signals": {
        "momentum": {"direction": "bullish", "strength": 80.0},
        "trend": {"direction": "bullish", "strength": 70.0},
        "volatility": {"direction": "bullish", "strength": 60.0},
        "volume": {"direction": "neutral", "strength": 0.0},
        "structure": {"direction": "neutral", "strength": 0.0},
    },
    "summary": "중간 강세 반전 신호 감지",
}


@patch("src.main.send_message")
@patch("src.main.generate_daily_report", return_value=SAMPLE_REPORT_HTML)
@patch("src.main.evaluate_signals", return_value={"details": [], "summary": SAMPLE_ACCURACY})
@patch("src.main.analyze_signal_trend", return_value=None)
@patch("src.main.upsert_signal_history")
@patch("src.main.compute_composite_signal", return_value=SAMPLE_SIGNAL)
@patch("src.main.detect_reversal_signals", return_value=SAMPLE_REVERSAL)
@patch("src.main.analyze_consensus", return_value=SAMPLE_CONSENSUS)
@patch("src.main.fetch_consensus", return_value=SAMPLE_RAW_CONSENSUS)
@patch("src.main.analyze_fundamentals", return_value=SAMPLE_FUNDAMENTALS)
@patch("src.main.fetch_fundamentals", return_value=SAMPLE_RAW_FUNDAMENTALS)
@patch("src.main.compute_relative_strength", return_value=SAMPLE_RS)
@patch("src.main.analyze_support_resistance", return_value=SAMPLE_SR)
@patch("src.main.analyze_exchange_rate", return_value=SAMPLE_ER)
@patch("src.main.analyze_supply_demand", return_value=SAMPLE_SD)
@patch("src.main.compute_technical_indicators", return_value=SAMPLE_INDICATORS)
@patch("src.main.get_exchange_rates", return_value=SAMPLE_RATES)
@patch("src.main.get_foreign_ownership", return_value=SAMPLE_OWNERSHIP)
@patch("src.main.get_foreign_trading", return_value=SAMPLE_TRADING)
@patch("src.main.get_prices", return_value=SAMPLE_PRICES)
@patch("src.main.fetch_kospi_ohlcv", return_value=SAMPLE_KOSPI)
@patch("src.main.summarize_sentiment", return_value=SAMPLE_NEWS_SENTIMENT)
@patch("src.main.fetch_news_headlines", return_value=SAMPLE_NEWS_HEADLINES)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_full(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_fetch_news, mock_summarize_news,
    mock_kospi, mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_rs,
    mock_fetch_fund, mock_analyze_fund,
    mock_fetch_cons, mock_analyze_cons,
    mock_reversal, mock_signal, mock_upsert_sig,
    mock_sig_trend, mock_eval, mock_report, mock_send,
):
    """전체 파이프라인: 백필→조회→분석→뉴스→컨센서스→지지저항→추세전환→펀더멘털→RS→시그널→기록→정확도→리포트→발송."""
    from src.main import main

    main()

    mock_init.assert_called_once()
    mock_bf_prices.assert_called_once()
    mock_bf_sd.assert_called_once()
    mock_kospi.assert_called_once()
    mock_prices.assert_called_once_with(60)
    mock_trading.assert_called_once_with(20)
    mock_ownership.assert_called_once_with(20)
    mock_rates.assert_called_once_with(30)
    mock_tech.assert_called_once_with(SAMPLE_PRICES)
    mock_sd.assert_called_once_with(SAMPLE_TRADING, SAMPLE_OWNERSHIP)
    mock_er.assert_called_once_with(SAMPLE_RATES, SAMPLE_PRICES)
    mock_sr.assert_called_once_with(SAMPLE_PRICES)
    mock_reversal.assert_called_once_with(SAMPLE_INDICATORS, SAMPLE_SR)
    mock_fetch_fund.assert_called_once()
    mock_analyze_fund.assert_called_once_with(SAMPLE_RAW_FUNDAMENTALS)
    mock_fetch_news.assert_called_once()
    mock_summarize_news.assert_called_once_with(SAMPLE_NEWS_HEADLINES)
    mock_fetch_cons.assert_called_once()
    mock_analyze_cons.assert_called_once()
    mock_signal.assert_called_once_with(
        SAMPLE_INDICATORS, SAMPLE_SD, SAMPLE_ER,
        relative_strength=SAMPLE_RS, trend_reversal=SAMPLE_REVERSAL,
        fundamentals=SAMPLE_FUNDAMENTALS,
        news_sentiment=SAMPLE_NEWS_SENTIMENT,
        consensus=SAMPLE_CONSENSUS,
    )
    mock_upsert_sig.assert_called_once_with(
        date="2026-03-60", score=35.0, grade="매수우세",
        technical_score=40.0, supply_score=50.0, exchange_score=-10.0,
        price=61000,
    )
    mock_eval.assert_called_once()
    mock_report.assert_called_once_with(
        SAMPLE_INDICATORS, supply_demand=SAMPLE_SD, exchange_rate=SAMPLE_ER,
        composite_signal=SAMPLE_SIGNAL, support_resistance=SAMPLE_SR,
        accuracy_summary=SAMPLE_ACCURACY, relative_strength=SAMPLE_RS,
        trend_reversal=SAMPLE_REVERSAL, signal_trend=None,
        fundamentals=SAMPLE_FUNDAMENTALS,
        news_sentiment=SAMPLE_NEWS_SENTIMENT,
        news_headlines=SAMPLE_NEWS_HEADLINES,
        consensus=SAMPLE_CONSENSUS,
    )
    mock_send.assert_called_once_with(SAMPLE_REPORT_HTML)


@patch("src.main.send_message")
@patch("src.main.generate_daily_report", return_value=SAMPLE_REPORT_HTML)
@patch("src.main.evaluate_signals", return_value={"details": [], "summary": SAMPLE_ACCURACY})
@patch("src.main.analyze_signal_trend", return_value=None)
@patch("src.main.upsert_signal_history")
@patch("src.main.compute_composite_signal", return_value=SAMPLE_SIGNAL)
@patch("src.main.detect_reversal_signals", return_value=SAMPLE_REVERSAL)
@patch("src.main.analyze_consensus", return_value=SAMPLE_CONSENSUS)
@patch("src.main.fetch_consensus", return_value=SAMPLE_RAW_CONSENSUS)
@patch("src.main.analyze_fundamentals", return_value=SAMPLE_FUNDAMENTALS)
@patch("src.main.fetch_fundamentals", return_value=SAMPLE_RAW_FUNDAMENTALS)
@patch("src.main.compute_relative_strength", return_value=SAMPLE_RS)
@patch("src.main.analyze_support_resistance", return_value=SAMPLE_SR)
@patch("src.main.analyze_exchange_rate", return_value=SAMPLE_ER)
@patch("src.main.analyze_supply_demand", return_value=SAMPLE_SD)
@patch("src.main.compute_technical_indicators", return_value=SAMPLE_INDICATORS)
@patch("src.main.get_exchange_rates", return_value=SAMPLE_RATES)
@patch("src.main.get_foreign_ownership", return_value=SAMPLE_OWNERSHIP)
@patch("src.main.get_foreign_trading", return_value=SAMPLE_TRADING)
@patch("src.main.get_prices", return_value=SAMPLE_PRICES)
@patch("src.main.fetch_kospi_ohlcv", return_value=SAMPLE_KOSPI)
@patch("src.main.summarize_sentiment", return_value=SAMPLE_NEWS_SENTIMENT)
@patch("src.main.fetch_news_headlines", return_value=SAMPLE_NEWS_HEADLINES)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_dry_run(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_fetch_news, mock_summarize_news,
    mock_kospi, mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_rs,
    mock_fetch_fund, mock_analyze_fund,
    mock_fetch_cons, mock_analyze_cons,
    mock_reversal, mock_signal, mock_upsert_sig,
    mock_sig_trend, mock_eval, mock_report, mock_send,
    capsys,
):
    """--dry-run: 리포트를 stdout에 출력하고 발송하지 않는다."""
    from src.main import main

    main(dry_run=True)

    mock_report.assert_called_once()
    mock_send.assert_not_called()
    captured = capsys.readouterr()
    assert SAMPLE_REPORT_HTML in captured.out


@patch("src.main.send_message")
@patch("src.main.generate_daily_report", return_value=SAMPLE_REPORT_HTML)
@patch("src.main.evaluate_signals", return_value={"details": [], "summary": SAMPLE_ACCURACY})
@patch("src.main.analyze_signal_trend", return_value=None)
@patch("src.main.upsert_signal_history")
@patch("src.main.compute_composite_signal", return_value=SAMPLE_SIGNAL)
@patch("src.main.detect_reversal_signals", return_value=SAMPLE_REVERSAL)
@patch("src.main.analyze_consensus", return_value=SAMPLE_CONSENSUS)
@patch("src.main.fetch_consensus", return_value=SAMPLE_RAW_CONSENSUS)
@patch("src.main.analyze_fundamentals", return_value=SAMPLE_FUNDAMENTALS)
@patch("src.main.fetch_fundamentals", return_value=SAMPLE_RAW_FUNDAMENTALS)
@patch("src.main.compute_relative_strength", return_value=SAMPLE_RS)
@patch("src.main.analyze_support_resistance", return_value=SAMPLE_SR)
@patch("src.main.analyze_exchange_rate", return_value=SAMPLE_ER)
@patch("src.main.analyze_supply_demand", return_value=SAMPLE_SD)
@patch("src.main.compute_technical_indicators", return_value=SAMPLE_INDICATORS)
@patch("src.main.get_exchange_rates", return_value=SAMPLE_RATES)
@patch("src.main.get_foreign_ownership", return_value=SAMPLE_OWNERSHIP)
@patch("src.main.get_foreign_trading", return_value=SAMPLE_TRADING)
@patch("src.main.get_prices", return_value=SAMPLE_PRICES)
@patch("src.main.fetch_kospi_ohlcv", return_value=SAMPLE_KOSPI)
@patch("src.main.summarize_sentiment", return_value=SAMPLE_NEWS_SENTIMENT)
@patch("src.main.fetch_news_headlines", return_value=SAMPLE_NEWS_HEADLINES)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_with_rs(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_fetch_news, mock_summarize_news,
    mock_kospi, mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_rs,
    mock_fetch_fund, mock_analyze_fund,
    mock_fetch_cons, mock_analyze_cons,
    mock_reversal, mock_signal, mock_upsert_sig,
    mock_sig_trend, mock_eval, mock_report, mock_send,
):
    """RS 분석이 파이프라인에 통합되어 composite_signal과 report에 전달된다."""
    from src.main import main

    main()

    # KOSPI 수집 호출 확인
    mock_kospi.assert_called_once()
    # RS 분석 호출 확인
    mock_rs.assert_called_once()
    # composite_signal에 RS와 reversal과 fundamentals와 뉴스와 컨센서스가 전달됨
    mock_signal.assert_called_once_with(
        SAMPLE_INDICATORS, SAMPLE_SD, SAMPLE_ER,
        relative_strength=SAMPLE_RS, trend_reversal=SAMPLE_REVERSAL,
        fundamentals=SAMPLE_FUNDAMENTALS,
        news_sentiment=SAMPLE_NEWS_SENTIMENT,
        consensus=SAMPLE_CONSENSUS,
    )
    # report에 RS와 reversal과 fundamentals와 뉴스와 컨센서스가 전달됨
    mock_report.assert_called_once()
    report_kwargs = mock_report.call_args
    assert report_kwargs[1].get("relative_strength") == SAMPLE_RS
    assert report_kwargs[1].get("trend_reversal") == SAMPLE_REVERSAL
    assert report_kwargs[1].get("fundamentals") == SAMPLE_FUNDAMENTALS
    assert report_kwargs[1].get("news_sentiment") == SAMPLE_NEWS_SENTIMENT
    assert report_kwargs[1].get("news_headlines") == SAMPLE_NEWS_HEADLINES
    assert report_kwargs[1].get("consensus") == SAMPLE_CONSENSUS


@patch("src.main.send_message")
@patch("src.main.generate_daily_report", return_value=SAMPLE_REPORT_HTML)
@patch("src.main.evaluate_signals", return_value={"details": [], "summary": SAMPLE_ACCURACY})
@patch("src.main.analyze_signal_trend", return_value=None)
@patch("src.main.upsert_signal_history")
@patch("src.main.compute_composite_signal", return_value=SAMPLE_SIGNAL)
@patch("src.main.detect_reversal_signals", return_value=SAMPLE_REVERSAL)
@patch("src.main.analyze_consensus", return_value=SAMPLE_CONSENSUS)
@patch("src.main.fetch_consensus", return_value=SAMPLE_RAW_CONSENSUS)
@patch("src.main.analyze_fundamentals", return_value=SAMPLE_FUNDAMENTALS)
@patch("src.main.fetch_fundamentals", return_value=SAMPLE_RAW_FUNDAMENTALS)
@patch("src.main.compute_relative_strength", return_value=SAMPLE_RS)
@patch("src.main.analyze_support_resistance", return_value=SAMPLE_SR)
@patch("src.main.analyze_exchange_rate", return_value=SAMPLE_ER)
@patch("src.main.analyze_supply_demand", return_value=SAMPLE_SD)
@patch("src.main.compute_technical_indicators", return_value=SAMPLE_INDICATORS)
@patch("src.main.get_exchange_rates", return_value=SAMPLE_RATES)
@patch("src.main.get_foreign_ownership", return_value=SAMPLE_OWNERSHIP)
@patch("src.main.get_foreign_trading", return_value=SAMPLE_TRADING)
@patch("src.main.get_prices", return_value=SAMPLE_PRICES)
@patch("src.main.fetch_kospi_ohlcv", side_effect=Exception("KOSPI API 실패"))
@patch("src.main.summarize_sentiment", return_value=SAMPLE_NEWS_SENTIMENT)
@patch("src.main.fetch_news_headlines", return_value=SAMPLE_NEWS_HEADLINES)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_kospi_failure_fallback(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_fetch_news, mock_summarize_news,
    mock_kospi, mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_rs,
    mock_fetch_fund, mock_analyze_fund,
    mock_fetch_cons, mock_analyze_cons,
    mock_reversal, mock_signal, mock_upsert_sig,
    mock_sig_trend, mock_eval, mock_report, mock_send,
):
    """KOSPI 수집 실패 시 RS=None으로 폴백하여 파이프라인이 정상 동작한다."""
    from src.main import main

    main()

    # KOSPI 수집 시도했지만 실패
    mock_kospi.assert_called_once()
    # RS 분석은 호출되지 않아야 함
    mock_rs.assert_not_called()
    # reversal은 여전히 호출됨 (KOSPI와 무관)
    mock_reversal.assert_called_once()
    # composite_signal에 RS=None 전달, reversal과 fundamentals와 뉴스와 컨센서스 전달
    mock_signal.assert_called_once_with(
        SAMPLE_INDICATORS, SAMPLE_SD, SAMPLE_ER,
        relative_strength=None, trend_reversal=SAMPLE_REVERSAL,
        fundamentals=SAMPLE_FUNDAMENTALS,
        news_sentiment=SAMPLE_NEWS_SENTIMENT,
        consensus=SAMPLE_CONSENSUS,
    )
    # report에 RS=None, reversal과 fundamentals와 뉴스와 컨센서스 전달
    report_kwargs = mock_report.call_args
    assert report_kwargs[1].get("relative_strength") is None
    assert report_kwargs[1].get("trend_reversal") == SAMPLE_REVERSAL
    assert report_kwargs[1].get("fundamentals") == SAMPLE_FUNDAMENTALS
    assert report_kwargs[1].get("news_sentiment") == SAMPLE_NEWS_SENTIMENT
    assert report_kwargs[1].get("consensus") == SAMPLE_CONSENSUS


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
