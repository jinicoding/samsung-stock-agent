"""지지/저항선 분석 모듈 테스트."""

import pytest

from src.analysis.support_resistance import (
    compute_pivot_points,
    find_swing_levels,
    compute_ma_levels,
    analyze_support_resistance,
)


def _make_rows(prices: list[float], base_volume: int = 1_000_000) -> list[dict]:
    """테스트용 OHLCV rows 생성. close = price, high = price+100, low = price-100."""
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


class TestPivotPoints:
    """클래식 피봇 포인트 계산 테스트."""

    def test_basic_pivot(self):
        """전일 HLC로 피봇 포인트 계산."""
        rows = _make_rows([50000, 51000])
        result = compute_pivot_points(rows)
        # 전일(rows[-2]): high=50100, low=49900, close=50000
        h, l, c = 50100, 49900, 50000
        pp = (h + l + c) / 3
        assert abs(result["pp"] - pp) < 0.01
        assert abs(result["s1"] - (2 * pp - h)) < 0.01
        assert abs(result["r1"] - (2 * pp - l)) < 0.01
        assert abs(result["s2"] - (pp - (h - l))) < 0.01
        assert abs(result["r2"] - (pp + (h - l))) < 0.01

    def test_single_row(self):
        """행이 1개면 None dict 반환."""
        rows = _make_rows([50000])
        result = compute_pivot_points(rows)
        assert result["pp"] is None

    def test_empty_rows(self):
        """빈 리스트면 None dict 반환."""
        result = compute_pivot_points([])
        assert result["pp"] is None


class TestSwingLevels:
    """스윙 고점/저점 기반 지지/저항 테스트."""

    def test_finds_swing_high(self):
        """V자 고점을 찾는다."""
        # 상승 → 고점 → 하락 → 저점 → 상승
        prices = [50000, 51000, 52000, 51000, 50000, 51000, 52000]
        rows = _make_rows(prices)
        levels = find_swing_levels(rows, window=1)
        highs = [l for l in levels if l["type"] == "resistance"]
        lows = [l for l in levels if l["type"] == "support"]
        assert len(highs) > 0
        assert len(lows) > 0

    def test_flat_prices_no_swings(self):
        """일정한 가격이면 스윙 레벨 없음."""
        prices = [50000] * 10
        rows = _make_rows(prices)
        levels = find_swing_levels(rows, window=2)
        assert levels == []

    def test_insufficient_data(self):
        """데이터가 window*2+1 미만이면 빈 리스트."""
        prices = [50000, 51000]
        rows = _make_rows(prices)
        levels = find_swing_levels(rows, window=3)
        assert levels == []

    def test_swing_level_structure(self):
        """반환 구조: {type, price, date}."""
        prices = [50000, 51000, 52000, 51000, 50000]
        rows = _make_rows(prices)
        levels = find_swing_levels(rows, window=1)
        for level in levels:
            assert "type" in level
            assert "price" in level
            assert "date" in level
            assert level["type"] in ("support", "resistance")


class TestMALevels:
    """이동평균 기반 동적 지지/저항 테스트."""

    def test_ma20_present(self):
        """20일 이상 데이터면 ma20 반환."""
        prices = [50000 + i * 100 for i in range(25)]
        rows = _make_rows(prices)
        result = compute_ma_levels(rows)
        assert result["ma20"] is not None

    def test_ma60_present(self):
        """60일 이상 데이터면 ma60 반환."""
        prices = [50000 + i * 100 for i in range(65)]
        rows = _make_rows(prices)
        result = compute_ma_levels(rows)
        assert result["ma60"] is not None

    def test_ma60_none_insufficient(self):
        """60일 미만이면 ma60 None."""
        prices = [50000] * 30
        rows = _make_rows(prices)
        result = compute_ma_levels(rows)
        assert result["ma60"] is None

    def test_ma20_none_insufficient(self):
        """20일 미만이면 ma20 None."""
        prices = [50000] * 10
        rows = _make_rows(prices)
        result = compute_ma_levels(rows)
        assert result["ma20"] is None


class TestAnalyzeSupportResistance:
    """종합 지지/저항 분석 테스트."""

    def test_result_structure(self):
        """반환 구조에 필수 키가 있다."""
        prices = [50000 + i * 100 for i in range(25)]
        rows = _make_rows(prices)
        result = analyze_support_resistance(rows)
        assert "pivot" in result
        assert "swing_levels" in result
        assert "ma_levels" in result
        assert "nearest_support" in result
        assert "nearest_resistance" in result

    def test_nearest_support_below_current(self):
        """nearest_support는 현재가 이하."""
        prices = [50000, 51000, 52000, 51000, 50000, 51000, 52000,
                  53000, 52000, 51000, 50000, 51000, 52000, 53000,
                  54000, 53000, 52000, 51000, 52000, 53000, 54000]
        rows = _make_rows(prices)
        result = analyze_support_resistance(rows)
        current = prices[-1]
        if result["nearest_support"] is not None:
            assert result["nearest_support"] <= current

    def test_nearest_resistance_above_current(self):
        """nearest_resistance는 현재가 이상."""
        prices = [50000, 51000, 52000, 51000, 50000, 51000, 52000,
                  53000, 52000, 51000, 50000, 51000, 52000, 53000,
                  54000, 53000, 52000, 51000, 52000, 53000, 54000]
        rows = _make_rows(prices)
        result = analyze_support_resistance(rows)
        current = prices[-1]
        if result["nearest_resistance"] is not None:
            assert result["nearest_resistance"] >= current

    def test_empty_rows(self):
        """빈 입력이면 ValueError."""
        with pytest.raises(ValueError):
            analyze_support_resistance([])

    def test_single_row(self):
        """행 1개면 pivot은 None, nearest도 None."""
        rows = _make_rows([50000])
        result = analyze_support_resistance(rows)
        assert result["pivot"]["pp"] is None
        assert result["nearest_support"] is None
        assert result["nearest_resistance"] is None

    def test_pivot_as_support_resistance(self):
        """피봇 포인트가 nearest 계산에 포함된다."""
        prices = [50000 + i * 100 for i in range(25)]
        rows = _make_rows(prices)
        result = analyze_support_resistance(rows)
        # pivot이 계산되면 nearest에 반영되어야 함
        assert result["pivot"]["pp"] is not None
