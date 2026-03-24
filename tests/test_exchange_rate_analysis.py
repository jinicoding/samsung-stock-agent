"""USD/KRW 환율 분석 모듈 테스트."""

import pytest

from src.analysis.exchange_rate import analyze_exchange_rate


def _make_rate_rows(rates: list[float]) -> list[dict]:
    """테스트용 환율 rows 생성. close = rate."""
    return [
        {
            "date": f"2026-01-{i + 1:02d}",
            "open": r,
            "high": r + 5,
            "low": r - 5,
            "close": r,
        }
        for i, r in enumerate(rates)
    ]


def _make_price_rows(prices: list[float]) -> list[dict]:
    """테스트용 주가 rows 생성."""
    return [
        {
            "date": f"2026-01-{i + 1:02d}",
            "open": p,
            "high": p + 100,
            "low": p - 100,
            "close": p,
            "volume": 1_000_000,
        }
        for i, p in enumerate(prices)
    ]


class TestCurrentRateAndChange:
    """환율 현재가 및 등락률 테스트."""

    def test_current_rate(self):
        rows = _make_rate_rows([1300, 1310, 1320])
        result = analyze_exchange_rate(rows)
        assert result["current_rate"] == 1320

    def test_change_1d(self):
        rows = _make_rate_rows([1300, 1310, 1320])
        result = analyze_exchange_rate(rows)
        # (1320 - 1310) / 1310 * 100
        expected = (1320 - 1310) / 1310 * 100
        assert result["change_1d_pct"] == pytest.approx(expected, rel=1e-6)

    def test_change_5d(self):
        rows = _make_rate_rows([1300, 1310, 1320, 1330, 1340, 1350])
        result = analyze_exchange_rate(rows)
        expected = (1350 - 1300) / 1300 * 100
        assert result["change_5d_pct"] == pytest.approx(expected, rel=1e-6)

    def test_change_20d(self):
        rates = [1300 + i * 2 for i in range(21)]
        rows = _make_rate_rows(rates)
        result = analyze_exchange_rate(rows)
        expected = (rates[-1] - rates[-21]) / rates[-21] * 100
        assert result["change_20d_pct"] == pytest.approx(expected, rel=1e-6)

    def test_change_insufficient_data(self):
        rows = _make_rate_rows([1300])
        result = analyze_exchange_rate(rows)
        assert result["change_1d_pct"] is None
        assert result["change_5d_pct"] is None
        assert result["change_20d_pct"] is None

    def test_empty_rows(self):
        with pytest.raises(ValueError):
            analyze_exchange_rate([])


class TestMovingAverageAndTrend:
    """환율 이동평균 및 추세 판정 테스트."""

    def test_ma5(self):
        rows = _make_rate_rows([1300, 1310, 1320, 1330, 1340])
        result = analyze_exchange_rate(rows)
        assert result["ma5"] == pytest.approx(1320.0)

    def test_ma20(self):
        rates = [1300 + i for i in range(20)]
        rows = _make_rate_rows(rates)
        result = analyze_exchange_rate(rows)
        assert result["ma20"] == pytest.approx(sum(rates) / 20)

    def test_ma_insufficient(self):
        rows = _make_rate_rows([1300, 1310])
        result = analyze_exchange_rate(rows)
        assert result["ma5"] is None
        assert result["ma20"] is None
        assert result["trend"] is None

    def test_trend_weakening_krw(self):
        """환율 상승 = 원화약세: close > ma5 > ma20."""
        rates = list(range(1300, 1320))  # 20개, 꾸준히 상승
        rows = _make_rate_rows(rates)
        result = analyze_exchange_rate(rows)
        assert result["trend"] == "원화약세"

    def test_trend_strengthening_krw(self):
        """환율 하락 = 원화강세: close < ma5 < ma20."""
        rates = list(range(1340, 1320, -1))  # 20개, 꾸준히 하락
        rows = _make_rate_rows(rates)
        result = analyze_exchange_rate(rows)
        assert result["trend"] == "원화강세"

    def test_trend_sideways(self):
        """횡보: close와 MA가 엇갈릴 때."""
        rates = [1300] * 20
        rows = _make_rate_rows(rates)
        result = analyze_exchange_rate(rows)
        assert result["trend"] == "보합"


class TestCorrelation:
    """주가-환율 상관관계 테스트."""

    def test_perfect_positive_correlation(self):
        """환율과 주가가 같은 방향으로 움직이면 상관계수 ≈ 1."""
        rates = [1300 + i * 10 for i in range(20)]
        prices = [50000 + i * 1000 for i in range(20)]
        rate_rows = _make_rate_rows(rates)
        price_rows = _make_price_rows(prices)
        result = analyze_exchange_rate(rate_rows, price_rows)
        assert result["correlation_20d"] == pytest.approx(1.0, abs=0.01)

    def test_perfect_negative_correlation(self):
        """환율 상승 + 주가 하락이면 상관계수 ≈ -1."""
        rates = [1300 + i * 10 for i in range(20)]
        prices = [60000 - i * 1000 for i in range(20)]
        rate_rows = _make_rate_rows(rates)
        price_rows = _make_price_rows(prices)
        result = analyze_exchange_rate(rate_rows, price_rows)
        assert result["correlation_20d"] == pytest.approx(-1.0, abs=0.01)

    def test_no_price_data(self):
        """주가 데이터 없으면 상관계수 None."""
        rows = _make_rate_rows([1300 + i for i in range(20)])
        result = analyze_exchange_rate(rows)
        assert result["correlation_20d"] is None

    def test_insufficient_overlap(self):
        """겹치는 날짜가 20일 미만이면 None."""
        rate_rows = _make_rate_rows([1300, 1310, 1320])
        price_rows = _make_price_rows([50000, 51000, 52000])
        result = analyze_exchange_rate(rate_rows, price_rows)
        assert result["correlation_20d"] is None
