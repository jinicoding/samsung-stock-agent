"""기초 기술적 분석 모듈 테스트."""

import pytest

from src.analysis.technical import compute_technical_indicators


def _make_rows(prices: list[float], base_volume: int = 1_000_000) -> list[dict]:
    """테스트용 OHLCV rows 생성. close = price, volume = base_volume."""
    rows = []
    for i, p in enumerate(prices):
        rows.append({
            "date": f"2026-01-{i + 1:02d}",
            "open": p,
            "high": p + 100,
            "low": p - 100,
            "close": p,
            "volume": base_volume,
        })
    return rows


class TestMovingAverages:
    """이동평균선 계산 테스트."""

    def test_ma5(self):
        prices = [50000, 51000, 52000, 53000, 54000]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["ma5"] == 52000.0

    def test_ma20(self):
        prices = list(range(50000, 70000, 1000))  # 20개
        result = compute_technical_indicators(_make_rows(prices))
        assert result["ma20"] == sum(prices) / 20

    def test_ma60_insufficient_data(self):
        """60일 미만 데이터면 ma60은 None."""
        prices = [50000] * 30
        result = compute_technical_indicators(_make_rows(prices))
        assert result["ma60"] is None

    def test_ma60_sufficient_data(self):
        prices = [50000 + i * 100 for i in range(60)]
        result = compute_technical_indicators(_make_rows(prices))
        expected = sum(prices) / 60
        assert abs(result["ma60"] - expected) < 0.01


class TestPriceVsMA:
    """현재가 대비 이동평균 위치(%) 테스트."""

    def test_price_above_ma5(self):
        prices = [50000, 51000, 52000, 53000, 56000]
        result = compute_technical_indicators(_make_rows(prices))
        # ma5 = 52400, close = 56000 → (56000-52400)/52400 * 100
        expected = (56000 - 52400) / 52400 * 100
        assert abs(result["price_vs_ma5_pct"] - expected) < 0.01

    def test_price_below_ma20(self):
        prices = [60000 - i * 100 for i in range(20)]  # 하락 추세
        result = compute_technical_indicators(_make_rows(prices))
        assert result["price_vs_ma20_pct"] < 0  # 현재가가 MA20 아래


class TestPriceChange:
    """가격 변동률 테스트."""

    def test_change_1d(self):
        prices = [50000, 51000]
        result = compute_technical_indicators(_make_rows(prices))
        assert abs(result["change_1d_pct"] - 2.0) < 0.01

    def test_change_5d(self):
        prices = [50000, 51000, 52000, 53000, 54000, 55000]
        result = compute_technical_indicators(_make_rows(prices))
        # 5일전 close=50000, 현재 close=55000 → 10%
        assert abs(result["change_5d_pct"] - 10.0) < 0.01

    def test_change_20d_insufficient(self):
        prices = [50000] * 10
        result = compute_technical_indicators(_make_rows(prices))
        assert result["change_20d_pct"] is None


class TestVolumeChange:
    """거래량 변화율 테스트."""

    def test_volume_ratio_equal(self):
        """5일 평균과 동일 거래량이면 ratio = 1.0."""
        rows = _make_rows([50000] * 6, base_volume=1_000_000)
        result = compute_technical_indicators(rows)
        assert abs(result["volume_ratio_5d"] - 1.0) < 0.01

    def test_volume_spike(self):
        """당일 거래량이 5일 평균의 2배."""
        rows = _make_rows([50000] * 6, base_volume=1_000_000)
        rows[-1]["volume"] = 2_000_000  # 당일만 2배
        result = compute_technical_indicators(rows)
        assert abs(result["volume_ratio_5d"] - 2.0) < 0.01

    def test_insufficient_data(self):
        """데이터 1개면 volume_ratio_5d는 None."""
        rows = _make_rows([50000])
        result = compute_technical_indicators(rows)
        assert result["volume_ratio_5d"] is None


class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_empty_input(self):
        with pytest.raises(ValueError):
            compute_technical_indicators([])

    def test_single_row(self):
        result = compute_technical_indicators(_make_rows([50000]))
        assert result["ma5"] is None
        assert result["change_1d_pct"] is None

    def test_result_has_current_price(self):
        result = compute_technical_indicators(_make_rows([50000, 51000]))
        assert result["current_price"] == 51000
        assert result["current_date"] == "2026-01-02"
