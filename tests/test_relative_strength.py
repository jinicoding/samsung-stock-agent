"""상대강도(RS) 분석 모듈 테스트."""

import pytest

from src.analysis.relative_strength import compute_relative_strength


class TestComputeRelativeStrength:
    """compute_relative_strength 함수 테스트."""

    def _make_prices(self, base: float, changes: list[float]) -> list[float]:
        """base에서 시작하여 변동률(%)을 적용한 종가 배열 생성."""
        prices = [base]
        for c in changes:
            prices.append(prices[-1] * (1 + c / 100))
        return prices

    def test_basic_outperform(self):
        """삼성전자가 KOSPI를 상회하면 outperform."""
        # 삼성전자: +10% over 20 days, KOSPI: +2%
        samsung = self._make_prices(50000, [0.5] * 20)
        kospi = self._make_prices(2500, [0.1] * 20)
        result = compute_relative_strength(samsung, kospi)

        assert result["rs_trend"] == "outperform"
        assert result["alpha_1d"] > 0
        assert result["alpha_5d"] > 0

    def test_basic_underperform(self):
        """삼성전자가 KOSPI를 하회하면 underperform."""
        samsung = self._make_prices(50000, [-0.5] * 20)
        kospi = self._make_prices(2500, [0.5] * 20)
        result = compute_relative_strength(samsung, kospi)

        assert result["rs_trend"] == "underperform"
        assert result["alpha_1d"] < 0

    def test_neutral_trend(self):
        """비슷한 수익률이면 neutral."""
        samsung = self._make_prices(50000, [0.1] * 20)
        kospi = self._make_prices(2500, [0.1] * 20)
        result = compute_relative_strength(samsung, kospi)

        assert result["rs_trend"] == "neutral"
        assert abs(result["alpha_1d"]) < 0.5

    def test_return_keys(self):
        """반환값에 필수 키가 모두 포함되어야 한다."""
        samsung = self._make_prices(50000, [0.3] * 25)
        kospi = self._make_prices(2500, [0.1] * 25)
        result = compute_relative_strength(samsung, kospi)

        expected_keys = {
            "samsung_return_1d", "samsung_return_5d", "samsung_return_20d",
            "kospi_return_1d", "kospi_return_5d", "kospi_return_20d",
            "alpha_1d", "alpha_5d", "alpha_20d",
            "rs_current", "rs_ma20", "rs_trend",
        }
        assert expected_keys.issubset(result.keys())

    def test_insufficient_data_short(self):
        """데이터가 2개 미만이면 None 반환."""
        result = compute_relative_strength([50000], [2500])
        assert result is None

    def test_insufficient_data_mismatch(self):
        """삼성전자와 KOSPI 배열 길이가 다르면 None 반환."""
        result = compute_relative_strength([50000, 51000], [2500])
        assert result is None

    def test_partial_data_no_20d(self):
        """20일 미만 데이터면 20일 수익률은 None, 나머지는 계산."""
        samsung = self._make_prices(50000, [0.3] * 10)
        kospi = self._make_prices(2500, [0.1] * 10)
        result = compute_relative_strength(samsung, kospi)

        assert result is not None
        assert result["samsung_return_1d"] is not None
        assert result["samsung_return_20d"] is None
        assert result["alpha_20d"] is None
        # RS trend should be based on available data (no MA20)
        assert result["rs_ma20"] is None

    def test_partial_data_no_5d(self):
        """5일 미만 데이터면 5일/20일 수익률은 None."""
        samsung = self._make_prices(50000, [0.3] * 3)
        kospi = self._make_prices(2500, [0.1] * 3)
        result = compute_relative_strength(samsung, kospi)

        assert result is not None
        assert result["samsung_return_1d"] is not None
        assert result["samsung_return_5d"] is None
        assert result["rs_trend"] in ("outperform", "underperform", "neutral")

    def test_alpha_calculation(self):
        """초과수익률(alpha) = 삼성전자 수익률 - KOSPI 수익률."""
        # 정확한 수치 검증
        samsung = [50000, 51000]  # +2%
        kospi = [2500, 2525]      # +1%
        result = compute_relative_strength(samsung, kospi)

        assert result is not None
        assert abs(result["samsung_return_1d"] - 2.0) < 0.01
        assert abs(result["kospi_return_1d"] - 1.0) < 0.01
        assert abs(result["alpha_1d"] - 1.0) < 0.01

    def test_rs_current_value(self):
        """RS = 삼성전자 종가 / KOSPI 종가."""
        samsung = [50000, 51000]
        kospi = [2500, 2525]
        result = compute_relative_strength(samsung, kospi)

        expected_rs = 51000 / 2525
        assert abs(result["rs_current"] - expected_rs) < 0.01
