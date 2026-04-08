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

SAMPLE_HYNIX = [
    {"date": f"2026-03-{d:02d}", "open": 200000.0, "high": 205000.0, "low": 195000.0, "close": 200000.0 + d * 500.0, "volume": 3000000}
    for d in range(1, 61)
]

SAMPLE_SOX = [
    {"date": f"2026-03-{d:02d}", "close": 4000.0 + d * 10.0}
    for d in range(1, 61)
]

SAMPLE_REL_PERF = {
    "samsung_return_5d": 1.0,
    "hynix_return_5d": 1.5,
    "alpha_5d": -0.5,
    "trend": "underperform",
}

SAMPLE_SOX_TREND = {
    "current": 4600.0,
    "ma5": 4550.0,
    "ma20": 4400.0,
    "trend": "uptrend",
    "change_5d_pct": 2.0,
    "change_20d_pct": 5.0,
}

SAMPLE_SEMI_MOMENTUM = 30

SAMPLE_VOLATILITY = {
    "atr": 1500.0,
    "atr_pct": 2.7,
    "hv20": 0.25,
    "volatility_percentile": 50.0,
    "volatility_regime": "보통",
    "bandwidth_squeeze": False,
}

SAMPLE_CANDLESTICK = {
    "patterns": [{"name": "bullish_marubozu", "direction": "bullish", "weight": 60}],
    "signal": "bullish",
    "score": 100.0,
}

SAMPLE_WATCHPOINTS = {
    "scenarios": {
        "nearest_support": 55000.0,
        "nearest_resistance": 58000.0,
        "next_support": 54500.0,
        "next_resistance": None,
    },
    "daily_range": {
        "expected_high": 62500.0,
        "expected_low": 59500.0,
        "atr": 1500.0,
        "atr_pct": 2.7,
    },
    "factors": [
        {"type": "opportunity", "text": "강세 전환 신호 감지"},
        {"type": "opportunity", "text": "외국인·기관 매수 우세 (외인 3일 연속 순매수)"},
    ],
}

SAMPLE_CONVERGENCE = {
    "convergence_level": "moderate",
    "dominant_direction": "bullish",
    "aligned_axes": ["technical_score", "supply_score"],
    "conflicting_axes": [],
    "neutral_axes": ["exchange_score"],
    "conviction": 55,
    "axis_directions": {
        "technical_score": "bullish",
        "supply_score": "bullish",
        "exchange_score": "neutral",
    },
}

SAMPLE_NASDAQ = [
    {"date": f"2026-03-{d:02d}", "close": 16000.0 + d * 20.0}
    for d in range(1, 61)
]

SAMPLE_VIX = [
    {"date": f"2026-03-{d:02d}", "close": 18.0 + d * 0.1}
    for d in range(1, 61)
]

SAMPLE_NASDAQ_TREND = {
    "trend": "상승",
    "change_5d_pct": 1.5,
    "change_20d_pct": 4.0,
    "ma5": 17100.0,
    "ma20": 16800.0,
    "current": 17200.0,
    "momentum_strength": 0.18,
}

SAMPLE_VIX_RISK = {
    "risk_level": "경계",
    "current": 24.0,
    "vix_trend": "보합",
    "change_pct": 2.0,
    "interpretation": "시장 불확실성이 높아지고 있어 주의 필요. 변동성이 횡보 중.",
}

SAMPLE_GLOBAL_MACRO_SCORE = 15

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
@patch("src.main.adjust_for_convergence", return_value=SAMPLE_SIGNAL)
@patch("src.main.analyze_convergence", return_value=SAMPLE_CONVERGENCE)
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
@patch("src.main.compute_semiconductor_momentum", return_value=SAMPLE_SEMI_MOMENTUM)
@patch("src.main.compute_sox_trend", return_value=SAMPLE_SOX_TREND)
@patch("src.main.compute_relative_performance", return_value=SAMPLE_REL_PERF)
@patch("src.main.fetch_sox_index", return_value=SAMPLE_SOX)
@patch("src.main.fetch_skhynix_ohlcv", return_value=SAMPLE_HYNIX)
@patch("src.main.summarize_sentiment", return_value=SAMPLE_NEWS_SENTIMENT)
@patch("src.main.fetch_news_headlines", return_value=SAMPLE_NEWS_HEADLINES)
@patch("src.main.compute_volatility", return_value=SAMPLE_VOLATILITY)
@patch("src.main.detect_candlestick_patterns", return_value=SAMPLE_CANDLESTICK)
@patch("src.main.compute_global_macro_score", return_value=SAMPLE_GLOBAL_MACRO_SCORE)
@patch("src.main.analyze_vix_risk", return_value=SAMPLE_VIX_RISK)
@patch("src.main.analyze_nasdaq_trend", return_value=SAMPLE_NASDAQ_TREND)
@patch("src.main.fetch_vix_index", return_value=SAMPLE_VIX)
@patch("src.main.fetch_nasdaq_index", return_value=SAMPLE_NASDAQ)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
@patch("src.main.get_signal_history", return_value=[])
@patch("src.main.summarize_weekly", return_value=None)
@patch("src.main.build_watchpoints", return_value=SAMPLE_WATCHPOINTS)
def test_pipeline_full(
    mock_watchpoints, mock_summarize_weekly, mock_sig_hist,
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_fetch_nasdaq, mock_fetch_vix,
    mock_nasdaq_trend, mock_vix_risk, mock_global_macro_score,
    mock_candlestick, mock_volatility,
    mock_fetch_news, mock_summarize_news,
    mock_fetch_hynix, mock_fetch_sox,
    mock_rel_perf, mock_sox_trend, mock_semi_momentum,
    mock_kospi, mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_rs,
    mock_fetch_fund, mock_analyze_fund,
    mock_fetch_cons, mock_analyze_cons,
    mock_reversal, mock_signal,
    mock_analyze_conv, mock_adjust_conv,
    mock_upsert_sig,
    mock_sig_trend, mock_eval, mock_report, mock_send,
):
    """전체 파이프라인: 백필→조회→분석→뉴스→컨센서스→지지저항→추세전환→펀더멘털→RS→시그널→수렴→기록→정확도→리포트→발송."""
    from src.main import main

    main()

    mock_init.assert_called_once()
    mock_bf_prices.assert_called_once()
    mock_bf_sd.assert_called_once()
    mock_kospi.assert_called_once()
    assert mock_prices.call_count == 2
    mock_prices.assert_any_call(60)
    mock_prices.assert_any_call(5)
    assert mock_trading.call_count == 2
    mock_trading.assert_any_call(20)
    mock_trading.assert_any_call(5)
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
    # 변동성 분석 호출 확인
    mock_volatility.assert_called_once_with(SAMPLE_PRICES)
    # 반도체 수집·분석 호출 확인
    mock_fetch_hynix.assert_called_once()
    mock_fetch_sox.assert_called_once()
    mock_rel_perf.assert_called_once()
    mock_sox_trend.assert_called_once()
    mock_semi_momentum.assert_called_once_with(SAMPLE_REL_PERF, SAMPLE_SOX_TREND)
    # 글로벌 매크로 수집·분석 호출 확인
    mock_fetch_nasdaq.assert_called_once()
    mock_fetch_vix.assert_called_once()
    mock_nasdaq_trend.assert_called_once()
    mock_vix_risk.assert_called_once()
    mock_global_macro_score.assert_called_once_with(SAMPLE_NASDAQ_TREND, SAMPLE_VIX_RISK)
    mock_signal.assert_called_once_with(
        SAMPLE_INDICATORS, SAMPLE_SD, SAMPLE_ER,
        relative_strength=SAMPLE_RS, trend_reversal=SAMPLE_REVERSAL,
        fundamentals=SAMPLE_FUNDAMENTALS,
        news_sentiment=SAMPLE_NEWS_SENTIMENT,
        consensus=SAMPLE_CONSENSUS,
        semiconductor_momentum=SAMPLE_SEMI_MOMENTUM,
        volatility=SAMPLE_VOLATILITY,
        candlestick=SAMPLE_CANDLESTICK,
        global_macro_score=SAMPLE_GLOBAL_MACRO_SCORE,
        accuracy_summary=SAMPLE_ACCURACY,
    )
    # 수렴 분석 호출 확인
    mock_analyze_conv.assert_called_once()
    mock_adjust_conv.assert_called_once_with(SAMPLE_SIGNAL, SAMPLE_CONVERGENCE)
    mock_upsert_sig.assert_called_once_with(
        date="2026-03-60", score=35.0, grade="매수우세",
        technical_score=40.0, supply_score=50.0, exchange_score=-10.0,
        price=61000,
        fundamentals_score=None,
        news_score=None,
        consensus_score=None,
        semiconductor_score=None,
        volatility_score=None,
        candlestick_score=None,
        global_macro_score=None,
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
        weekly_summary=None,
        rel_perf=SAMPLE_REL_PERF,
        sox_trend=SAMPLE_SOX_TREND,
        semiconductor_momentum=SAMPLE_SEMI_MOMENTUM,
        volatility=SAMPLE_VOLATILITY,
        candlestick=SAMPLE_CANDLESTICK,
        watchpoints=SAMPLE_WATCHPOINTS,
        convergence=SAMPLE_CONVERGENCE,
        nasdaq_trend=SAMPLE_NASDAQ_TREND,
        vix_risk=SAMPLE_VIX_RISK,
        global_macro_score=SAMPLE_GLOBAL_MACRO_SCORE,
    )
    mock_send.assert_called_once_with(SAMPLE_REPORT_HTML)


@patch("src.main.send_message")
@patch("src.main.generate_daily_report", return_value=SAMPLE_REPORT_HTML)
@patch("src.main.evaluate_signals", return_value={"details": [], "summary": SAMPLE_ACCURACY})
@patch("src.main.analyze_signal_trend", return_value=None)
@patch("src.main.upsert_signal_history")
@patch("src.main.adjust_for_convergence", return_value=SAMPLE_SIGNAL)
@patch("src.main.analyze_convergence", return_value=SAMPLE_CONVERGENCE)
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
@patch("src.main.compute_semiconductor_momentum", return_value=SAMPLE_SEMI_MOMENTUM)
@patch("src.main.compute_sox_trend", return_value=SAMPLE_SOX_TREND)
@patch("src.main.compute_relative_performance", return_value=SAMPLE_REL_PERF)
@patch("src.main.fetch_sox_index", return_value=SAMPLE_SOX)
@patch("src.main.fetch_skhynix_ohlcv", return_value=SAMPLE_HYNIX)
@patch("src.main.summarize_sentiment", return_value=SAMPLE_NEWS_SENTIMENT)
@patch("src.main.fetch_news_headlines", return_value=SAMPLE_NEWS_HEADLINES)
@patch("src.main.compute_volatility", return_value=SAMPLE_VOLATILITY)
@patch("src.main.detect_candlestick_patterns", return_value=SAMPLE_CANDLESTICK)
@patch("src.main.compute_global_macro_score", return_value=SAMPLE_GLOBAL_MACRO_SCORE)
@patch("src.main.analyze_vix_risk", return_value=SAMPLE_VIX_RISK)
@patch("src.main.analyze_nasdaq_trend", return_value=SAMPLE_NASDAQ_TREND)
@patch("src.main.fetch_vix_index", return_value=SAMPLE_VIX)
@patch("src.main.fetch_nasdaq_index", return_value=SAMPLE_NASDAQ)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_dry_run(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_fetch_nasdaq, mock_fetch_vix,
    mock_nasdaq_trend, mock_vix_risk, mock_global_macro_score,
    mock_candlestick, mock_volatility,
    mock_fetch_news, mock_summarize_news,
    mock_fetch_hynix, mock_fetch_sox,
    mock_rel_perf, mock_sox_trend, mock_semi_momentum,
    mock_kospi, mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_rs,
    mock_fetch_fund, mock_analyze_fund,
    mock_fetch_cons, mock_analyze_cons,
    mock_reversal, mock_signal,
    mock_analyze_conv, mock_adjust_conv,
    mock_upsert_sig,
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
@patch("src.main.adjust_for_convergence", return_value=SAMPLE_SIGNAL)
@patch("src.main.analyze_convergence", return_value=SAMPLE_CONVERGENCE)
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
@patch("src.main.compute_semiconductor_momentum", return_value=SAMPLE_SEMI_MOMENTUM)
@patch("src.main.compute_sox_trend", return_value=SAMPLE_SOX_TREND)
@patch("src.main.compute_relative_performance", return_value=SAMPLE_REL_PERF)
@patch("src.main.fetch_sox_index", return_value=SAMPLE_SOX)
@patch("src.main.fetch_skhynix_ohlcv", return_value=SAMPLE_HYNIX)
@patch("src.main.summarize_sentiment", return_value=SAMPLE_NEWS_SENTIMENT)
@patch("src.main.fetch_news_headlines", return_value=SAMPLE_NEWS_HEADLINES)
@patch("src.main.compute_volatility", return_value=SAMPLE_VOLATILITY)
@patch("src.main.detect_candlestick_patterns", return_value=SAMPLE_CANDLESTICK)
@patch("src.main.compute_global_macro_score", return_value=SAMPLE_GLOBAL_MACRO_SCORE)
@patch("src.main.analyze_vix_risk", return_value=SAMPLE_VIX_RISK)
@patch("src.main.analyze_nasdaq_trend", return_value=SAMPLE_NASDAQ_TREND)
@patch("src.main.fetch_vix_index", return_value=SAMPLE_VIX)
@patch("src.main.fetch_nasdaq_index", return_value=SAMPLE_NASDAQ)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_with_rs(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_fetch_nasdaq, mock_fetch_vix,
    mock_nasdaq_trend, mock_vix_risk, mock_global_macro_score,
    mock_candlestick, mock_volatility,
    mock_fetch_news, mock_summarize_news,
    mock_fetch_hynix, mock_fetch_sox,
    mock_rel_perf, mock_sox_trend, mock_semi_momentum,
    mock_kospi, mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_rs,
    mock_fetch_fund, mock_analyze_fund,
    mock_fetch_cons, mock_analyze_cons,
    mock_reversal, mock_signal,
    mock_analyze_conv, mock_adjust_conv,
    mock_upsert_sig,
    mock_sig_trend, mock_eval, mock_report, mock_send,
):
    """RS + 반도체 + 변동성 + 캔들스틱 + 글로벌매크로 분석이 파이프라인에 통합되어 composite_signal과 report에 전달된다."""
    from src.main import main

    main()

    # KOSPI 수집 호출 확인
    mock_kospi.assert_called_once()
    # RS 분석 호출 확인
    mock_rs.assert_called_once()
    # 변동성 분석 호출 확인
    mock_volatility.assert_called_once_with(SAMPLE_PRICES)
    # 반도체 수집·분석 호출 확인
    mock_fetch_hynix.assert_called_once()
    mock_fetch_sox.assert_called_once()
    mock_semi_momentum.assert_called_once()
    # 글로벌 매크로 수집·분석 호출 확인
    mock_fetch_nasdaq.assert_called_once()
    mock_fetch_vix.assert_called_once()
    mock_nasdaq_trend.assert_called_once()
    mock_vix_risk.assert_called_once()
    mock_global_macro_score.assert_called_once_with(SAMPLE_NASDAQ_TREND, SAMPLE_VIX_RISK)
    # composite_signal에 RS와 reversal과 fundamentals와 뉴스와 컨센서스와 반도체와 변동성과 캔들스틱과 글로벌매크로가 전달됨
    mock_signal.assert_called_once_with(
        SAMPLE_INDICATORS, SAMPLE_SD, SAMPLE_ER,
        relative_strength=SAMPLE_RS, trend_reversal=SAMPLE_REVERSAL,
        fundamentals=SAMPLE_FUNDAMENTALS,
        news_sentiment=SAMPLE_NEWS_SENTIMENT,
        consensus=SAMPLE_CONSENSUS,
        semiconductor_momentum=SAMPLE_SEMI_MOMENTUM,
        volatility=SAMPLE_VOLATILITY,
        candlestick=SAMPLE_CANDLESTICK,
        global_macro_score=SAMPLE_GLOBAL_MACRO_SCORE,
        accuracy_summary=SAMPLE_ACCURACY,
    )
    # report에 RS와 reversal과 fundamentals와 뉴스와 컨센서스와 반도체와 변동성과 캔들스틱이 전달됨
    mock_report.assert_called_once()
    report_kwargs = mock_report.call_args
    assert report_kwargs[1].get("relative_strength") == SAMPLE_RS
    assert report_kwargs[1].get("trend_reversal") == SAMPLE_REVERSAL
    assert report_kwargs[1].get("fundamentals") == SAMPLE_FUNDAMENTALS
    assert report_kwargs[1].get("news_sentiment") == SAMPLE_NEWS_SENTIMENT
    assert report_kwargs[1].get("news_headlines") == SAMPLE_NEWS_HEADLINES
    assert report_kwargs[1].get("consensus") == SAMPLE_CONSENSUS
    assert report_kwargs[1].get("semiconductor_momentum") == SAMPLE_SEMI_MOMENTUM
    assert report_kwargs[1].get("volatility") == SAMPLE_VOLATILITY
    assert report_kwargs[1].get("candlestick") == SAMPLE_CANDLESTICK
    assert report_kwargs[1].get("convergence") == SAMPLE_CONVERGENCE
    assert report_kwargs[1].get("nasdaq_trend") == SAMPLE_NASDAQ_TREND
    assert report_kwargs[1].get("vix_risk") == SAMPLE_VIX_RISK
    assert report_kwargs[1].get("global_macro_score") == SAMPLE_GLOBAL_MACRO_SCORE
    # 수렴 분석 호출 확인
    mock_analyze_conv.assert_called_once()
    mock_adjust_conv.assert_called_once()


@patch("src.main.send_message")
@patch("src.main.generate_daily_report", return_value=SAMPLE_REPORT_HTML)
@patch("src.main.evaluate_signals", return_value={"details": [], "summary": SAMPLE_ACCURACY})
@patch("src.main.analyze_signal_trend", return_value=None)
@patch("src.main.upsert_signal_history")
@patch("src.main.adjust_for_convergence", return_value=SAMPLE_SIGNAL)
@patch("src.main.analyze_convergence", return_value=SAMPLE_CONVERGENCE)
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
@patch("src.main.compute_semiconductor_momentum", return_value=SAMPLE_SEMI_MOMENTUM)
@patch("src.main.compute_sox_trend", return_value=SAMPLE_SOX_TREND)
@patch("src.main.compute_relative_performance", return_value=SAMPLE_REL_PERF)
@patch("src.main.fetch_sox_index", return_value=SAMPLE_SOX)
@patch("src.main.fetch_skhynix_ohlcv", return_value=SAMPLE_HYNIX)
@patch("src.main.summarize_sentiment", return_value=SAMPLE_NEWS_SENTIMENT)
@patch("src.main.fetch_news_headlines", return_value=SAMPLE_NEWS_HEADLINES)
@patch("src.main.compute_volatility", return_value=SAMPLE_VOLATILITY)
@patch("src.main.detect_candlestick_patterns", return_value=SAMPLE_CANDLESTICK)
@patch("src.main.compute_global_macro_score", return_value=SAMPLE_GLOBAL_MACRO_SCORE)
@patch("src.main.analyze_vix_risk", return_value=SAMPLE_VIX_RISK)
@patch("src.main.analyze_nasdaq_trend", return_value=SAMPLE_NASDAQ_TREND)
@patch("src.main.fetch_vix_index", return_value=SAMPLE_VIX)
@patch("src.main.fetch_nasdaq_index", return_value=SAMPLE_NASDAQ)
@patch("src.main.backfill_supply_demand")
@patch("src.main.backfill_prices")
@patch("src.main.init_db")
def test_pipeline_kospi_failure_fallback(
    mock_init, mock_bf_prices, mock_bf_sd,
    mock_fetch_nasdaq, mock_fetch_vix,
    mock_nasdaq_trend, mock_vix_risk, mock_global_macro_score,
    mock_candlestick, mock_volatility,
    mock_fetch_news, mock_summarize_news,
    mock_fetch_hynix, mock_fetch_sox,
    mock_rel_perf, mock_sox_trend, mock_semi_momentum,
    mock_kospi, mock_prices, mock_trading, mock_ownership, mock_rates,
    mock_tech, mock_sd, mock_er, mock_sr, mock_rs,
    mock_fetch_fund, mock_analyze_fund,
    mock_fetch_cons, mock_analyze_cons,
    mock_reversal, mock_signal,
    mock_analyze_conv, mock_adjust_conv,
    mock_upsert_sig,
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
    # 변동성 분석은 여전히 호출됨
    mock_volatility.assert_called_once_with(SAMPLE_PRICES)
    # 반도체 수집은 KOSPI와 독립 — 여전히 호출됨
    mock_fetch_hynix.assert_called_once()
    mock_fetch_sox.assert_called_once()
    # 글로벌 매크로도 KOSPI와 독립 — 여전히 호출됨
    mock_fetch_nasdaq.assert_called_once()
    mock_fetch_vix.assert_called_once()
    mock_global_macro_score.assert_called_once()
    # composite_signal에 RS=None 전달, 글로벌 매크로 포함, accuracy_summary 전달
    mock_signal.assert_called_once_with(
        SAMPLE_INDICATORS, SAMPLE_SD, SAMPLE_ER,
        relative_strength=None, trend_reversal=SAMPLE_REVERSAL,
        fundamentals=SAMPLE_FUNDAMENTALS,
        news_sentiment=SAMPLE_NEWS_SENTIMENT,
        consensus=SAMPLE_CONSENSUS,
        semiconductor_momentum=SAMPLE_SEMI_MOMENTUM,
        volatility=SAMPLE_VOLATILITY,
        candlestick=SAMPLE_CANDLESTICK,
        global_macro_score=SAMPLE_GLOBAL_MACRO_SCORE,
        accuracy_summary=SAMPLE_ACCURACY,
    )
    # report에 RS=None, 글로벌 매크로 포함
    report_kwargs = mock_report.call_args
    assert report_kwargs[1].get("relative_strength") is None
    assert report_kwargs[1].get("trend_reversal") == SAMPLE_REVERSAL
    assert report_kwargs[1].get("fundamentals") == SAMPLE_FUNDAMENTALS
    assert report_kwargs[1].get("news_sentiment") == SAMPLE_NEWS_SENTIMENT
    assert report_kwargs[1].get("consensus") == SAMPLE_CONSENSUS
    assert report_kwargs[1].get("semiconductor_momentum") == SAMPLE_SEMI_MOMENTUM
    assert report_kwargs[1].get("volatility") == SAMPLE_VOLATILITY
    assert report_kwargs[1].get("candlestick") == SAMPLE_CANDLESTICK
    assert report_kwargs[1].get("convergence") == SAMPLE_CONVERGENCE
    assert report_kwargs[1].get("nasdaq_trend") == SAMPLE_NASDAQ_TREND
    assert report_kwargs[1].get("vix_risk") == SAMPLE_VIX_RISK
    assert report_kwargs[1].get("global_macro_score") == SAMPLE_GLOBAL_MACRO_SCORE


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
