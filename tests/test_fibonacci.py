"""피보나치 되돌림 분석 모듈 테스트."""

import pytest

from src.analysis.fibonacci import (
    find_swing_points,
    compute_retracement_levels,
    compute_extension_levels,
    find_current_position,
    analyze_fibonacci,
)


def _make_rows(prices: list[float]) -> list[dict]:
    """테스트용 OHLCV rows 생성."""
    rows = []
    for i, p in enumerate(prices):
        rows.append({
            "date": f"2026-01-{i + 1:02d}",
            "open": p,
            "high": p + 100,
            "low": p - 100,
            "close": p,
            "volume": 1_000_000,
        })
    return rows


class TestSwingPoints:
    """swing high/low 탐지 테스트."""

    def test_finds_high_and_low(self):
        """상승 후 하락 패턴에서 high/low를 찾는다."""
        prices = [50000, 51000, 52000, 53000, 54000, 53000, 52000, 51000, 50000]
        rows = _make_rows(prices)
        high, low = find_swing_points(rows)
        assert high["price"] == 54100  # 54000 + 100 (high)
        assert low["price"] == 49900  # 50000 - 100 (low of first row)

    def test_downtrend(self):
        """하락 후 상승 패턴."""
        prices = [54000, 53000, 52000, 51000, 50000, 51000, 52000, 53000, 54000]
        rows = _make_rows(prices)
        high, low = find_swing_points(rows)
        assert high["price"] == 54100
        assert low["price"] == 49900

    def test_insufficient_data(self):
        """데이터 부족 시 None 반환."""
        rows = _make_rows([50000, 51000])
        high, low = find_swing_points(rows)
        assert high is None
        assert low is None

    def test_empty_data(self):
        rows = _make_rows([])
        high, low = find_swing_points(rows)
        assert high is None
        assert low is None


class TestRetracementLevels:
    """피보나치 되돌림 수준 계산 테스트."""

    def test_uptrend_retracement(self):
        """상승추세 되돌림: low→high 기준."""
        levels = compute_retracement_levels(50000, 60000, trend="up")
        assert levels["0.0"] == 60000  # high (시작)
        assert levels["1.0"] == 50000  # low (끝)
        assert abs(levels["0.236"] - 57640) < 1
        assert abs(levels["0.382"] - 56180) < 1
        assert abs(levels["0.5"] - 55000) < 1
        assert abs(levels["0.618"] - 53820) < 1
        assert abs(levels["0.786"] - 52140) < 1

    def test_downtrend_retracement(self):
        """하락추세 되돌림: high→low 기준."""
        levels = compute_retracement_levels(50000, 60000, trend="down")
        assert levels["0.0"] == 50000  # low (시작)
        assert levels["1.0"] == 60000  # high (끝)
        assert abs(levels["0.236"] - 52360) < 1
        assert abs(levels["0.382"] - 53820) < 1
        assert abs(levels["0.5"] - 55000) < 1
        assert abs(levels["0.618"] - 56180) < 1
        assert abs(levels["0.786"] - 57860) < 1

    def test_same_high_low(self):
        """고점=저점일 때 빈 dict 반환."""
        levels = compute_retracement_levels(50000, 50000, trend="up")
        assert levels == {}


class TestExtensionLevels:
    """피보나치 확장 수준 테스트."""

    def test_uptrend_extension(self):
        """상승추세 확장."""
        levels = compute_extension_levels(50000, 60000, trend="up")
        diff = 10000
        assert abs(levels["1.0"] - 70000) < 1    # high + diff * 1.0
        assert abs(levels["1.272"] - 72720) < 1
        assert abs(levels["1.618"] - 76180) < 1

    def test_downtrend_extension(self):
        """하락추세 확장."""
        levels = compute_extension_levels(50000, 60000, trend="down")
        diff = 10000
        assert abs(levels["1.0"] - 40000) < 1    # low - diff * 1.0
        assert abs(levels["1.272"] - 37280) < 1
        assert abs(levels["1.618"] - 33820) < 1

    def test_same_high_low(self):
        levels = compute_extension_levels(50000, 50000, trend="up")
        assert levels == {}


class TestCurrentPosition:
    """현재가 위치 판별 테스트."""

    def test_between_levels(self):
        """현재가가 38.2%~50% 사이."""
        levels = compute_retracement_levels(50000, 60000, trend="up")
        pos = find_current_position(55500, levels)
        assert pos["below"] == "0.5"
        assert pos["above"] == "0.382"

    def test_above_all(self):
        """현재가가 0% 위 (고점 초과)."""
        levels = compute_retracement_levels(50000, 60000, trend="up")
        pos = find_current_position(61000, levels)
        assert pos["below"] == "0.0"
        assert pos["above"] is None

    def test_below_all(self):
        """현재가가 100% 아래 (저점 미만)."""
        levels = compute_retracement_levels(50000, 60000, trend="up")
        pos = find_current_position(49000, levels)
        assert pos["below"] is None
        assert pos["above"] == "1.0"

    def test_empty_levels(self):
        pos = find_current_position(55000, {})
        assert pos["below"] is None
        assert pos["above"] is None


class TestAnalyzeFibonacci:
    """통합 분석 함수 테스트."""

    def test_basic_analysis(self):
        """충분한 데이터로 분석 결과 구조 확인."""
        prices = list(range(50000, 56000, 100)) + list(range(56000, 53000, -100))
        rows = _make_rows(prices)
        result = analyze_fibonacci(rows)
        assert "retracement" in result
        assert "extension" in result
        assert "position" in result
        assert "swing_high" in result
        assert "swing_low" in result
        assert "trend" in result

    def test_insufficient_data(self):
        """데이터 부족 시 빈 결과."""
        rows = _make_rows([50000, 51000])
        result = analyze_fibonacci(rows)
        assert result["retracement"] == {}
        assert result["extension"] == {}

    def test_flat_prices(self):
        """모든 OHLC 동일 시 빈 결과."""
        rows = [{"date": f"2026-01-{i+1:02d}", "open": 50000, "high": 50000,
                 "low": 50000, "close": 50000, "volume": 1_000_000} for i in range(20)]
        result = analyze_fibonacci(rows)
        assert result["retracement"] == {}
