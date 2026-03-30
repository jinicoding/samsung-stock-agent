"""주간 추이 요약 분석 모듈 테스트."""

import pytest

from src.analysis.weekly_summary import summarize_weekly


def _make_prices(data: list[tuple]) -> list[dict]:
    """(date, open, high, low, close, volume) 튜플 → dict 리스트."""
    return [
        {"date": d, "open": o, "high": h, "low": l, "close": c, "volume": v}
        for d, o, h, l, c, v in data
    ]


def _make_trading(data: list[tuple]) -> list[dict]:
    """(date, institution, foreign_total) 튜플 → dict 리스트."""
    return [
        {"date": d, "institution": inst, "foreign_total": ft, "individual": 0, "other_corp": 0}
        for d, inst, ft in data
    ]


def _make_signals(data: list[tuple]) -> list[dict]:
    """(date, score, grade) 튜플 → dict 리스트."""
    return [
        {"date": d, "score": s, "grade": g, "technical_score": 0,
         "supply_score": 0, "exchange_score": 0, "price": 0}
        for d, s, g in data
    ]


# ── 기본 동작 ──

class TestWeeklySummaryBasic:
    """기본 입출력 검증."""

    def test_returns_none_when_no_prices(self):
        result = summarize_weekly([], [], [])
        assert result is None

    def test_returns_none_when_single_day(self):
        prices = _make_prices([("2026-03-30", 55000, 56000, 54000, 55500, 1000000)])
        result = summarize_weekly(prices, [], [])
        assert result is None

    def test_basic_five_day_output(self):
        prices = _make_prices([
            ("2026-03-24", 54000, 55000, 53500, 54500, 10000000),
            ("2026-03-25", 54500, 56000, 54000, 55500, 12000000),
            ("2026-03-26", 55500, 56500, 55000, 56000, 11000000),
            ("2026-03-27", 56000, 57000, 55500, 56500, 13000000),
            ("2026-03-28", 56500, 57500, 56000, 57000, 14000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result is not None
        assert result["days"] == 5
        assert result["week_open"] == 54000
        assert result["week_close"] == 57000
        assert result["week_high"] == 57500
        assert result["week_low"] == 53500

    def test_change_pct(self):
        prices = _make_prices([
            ("2026-03-24", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-25", 50000, 52000, 49500, 51000, 10000000),
            ("2026-03-26", 51000, 53000, 50000, 52000, 10000000),
            ("2026-03-27", 52000, 54000, 51000, 53000, 10000000),
            ("2026-03-28", 53000, 55000, 52000, 55000, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        # 주간 등락률: (55000 - 50000) / 50000 * 100 = 10.0%
        assert result["change_pct"] == pytest.approx(10.0, abs=0.01)


# ── 거래량 ──

class TestWeeklyVolume:
    """거래량 관련 테스트."""

    def test_total_volume(self):
        prices = _make_prices([
            ("2026-03-24", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-25", 50000, 51000, 49000, 50000, 20000000),
            ("2026-03-26", 50000, 51000, 49000, 50000, 15000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["total_volume"] == 45000000
        assert result["avg_daily_volume"] == pytest.approx(15000000)


# ── 수급 ──

class TestWeeklySupplyDemand:
    """외국인/기관 순매수 합계."""

    def test_supply_demand_totals(self):
        prices = _make_prices([
            ("2026-03-24", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-25", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-26", 50000, 51000, 49000, 50000, 10000000),
        ])
        trading = _make_trading([
            ("2026-03-24", 5000, 3000),
            ("2026-03-25", -2000, 4000),
            ("2026-03-26", 1000, -1000),
        ])
        result = summarize_weekly(prices, trading, [])
        assert result["institution_net_total"] == 4000  # 5000-2000+1000
        assert result["foreign_net_total"] == 6000  # 3000+4000-1000

    def test_empty_trading_data(self):
        prices = _make_prices([
            ("2026-03-24", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-25", 50000, 51000, 49000, 50000, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["institution_net_total"] == 0
        assert result["foreign_net_total"] == 0


# ── 시그널 변화 ──

class TestWeeklySignal:
    """시그널 점수/등급 변화."""

    def test_signal_change(self):
        prices = _make_prices([
            ("2026-03-24", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-25", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-26", 50000, 51000, 49000, 50000, 10000000),
        ])
        signals = _make_signals([
            ("2026-03-24", 20.0, "관망"),
            ("2026-03-25", 35.0, "매수 관심"),
            ("2026-03-26", 50.0, "매수 신호"),
        ])
        result = summarize_weekly(prices, [], signals)
        assert result["signal_start_score"] == 20.0
        assert result["signal_end_score"] == 50.0
        assert result["signal_score_change"] == pytest.approx(30.0)
        assert result["signal_start_grade"] == "관망"
        assert result["signal_end_grade"] == "매수 신호"

    def test_no_signal_data(self):
        prices = _make_prices([
            ("2026-03-24", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-25", 50000, 51000, 49000, 50000, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["signal_start_score"] is None
        assert result["signal_end_score"] is None
        assert result["signal_score_change"] is None
        assert result["signal_start_grade"] is None
        assert result["signal_end_grade"] is None


# ── 주간 판정 ──

class TestWeeklyJudgment:
    """주간 요약 판정 로직."""

    def test_uptrend(self):
        """종가가 지속 상승 → '상승 지속'."""
        prices = _make_prices([
            ("2026-03-24", 50000, 51000, 49000, 50500, 10000000),
            ("2026-03-25", 50500, 52000, 50000, 51500, 10000000),
            ("2026-03-26", 51500, 53000, 51000, 52500, 10000000),
            ("2026-03-27", 52500, 54000, 52000, 53500, 10000000),
            ("2026-03-28", 53500, 55000, 53000, 54500, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["judgment"] == "상승 지속"

    def test_downtrend(self):
        """종가가 지속 하락 → '하락 지속'."""
        prices = _make_prices([
            ("2026-03-24", 55000, 55500, 54000, 54500, 10000000),
            ("2026-03-25", 54500, 55000, 53500, 53500, 10000000),
            ("2026-03-26", 53500, 54000, 52500, 52500, 10000000),
            ("2026-03-27", 52500, 53000, 51500, 51500, 10000000),
            ("2026-03-28", 51500, 52000, 50500, 50500, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["judgment"] == "하락 지속"

    def test_sideways(self):
        """등락률이 미미 → '횡보'."""
        prices = _make_prices([
            ("2026-03-24", 50000, 50500, 49500, 50100, 10000000),
            ("2026-03-25", 50100, 50300, 49800, 50000, 10000000),
            ("2026-03-26", 50000, 50200, 49700, 49900, 10000000),
            ("2026-03-27", 49900, 50100, 49600, 50050, 10000000),
            ("2026-03-28", 50050, 50200, 49800, 50000, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["judgment"] == "횡보"

    def test_upward_reversal(self):
        """전반 하락 후반 상승 → '상승 전환'."""
        prices = _make_prices([
            ("2026-03-24", 55000, 55500, 54000, 54000, 10000000),
            ("2026-03-25", 54000, 54500, 52000, 52000, 10000000),
            ("2026-03-26", 52000, 53000, 51000, 51500, 10000000),
            ("2026-03-27", 51500, 54000, 51000, 53500, 10000000),
            ("2026-03-28", 53500, 56000, 53000, 56000, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["judgment"] == "상승 전환"

    def test_downward_reversal(self):
        """전반 상승 후반 하락 → '하락 전환'."""
        prices = _make_prices([
            ("2026-03-24", 50000, 52000, 49500, 52000, 10000000),
            ("2026-03-25", 52000, 54000, 51500, 54000, 10000000),
            ("2026-03-26", 54000, 55000, 53000, 54500, 10000000),
            ("2026-03-27", 54500, 55000, 52000, 52000, 10000000),
            ("2026-03-28", 52000, 52500, 49000, 49000, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["judgment"] == "하락 전환"


# ── 날짜 범위 ──

class TestWeeklyDateRange:
    """주간 날짜 범위 정보."""

    def test_date_range(self):
        prices = _make_prices([
            ("2026-03-24", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-25", 50000, 51000, 49000, 50000, 10000000),
            ("2026-03-28", 50000, 51000, 49000, 50000, 10000000),
        ])
        result = summarize_weekly(prices, [], [])
        assert result["start_date"] == "2026-03-24"
        assert result["end_date"] == "2026-03-28"
