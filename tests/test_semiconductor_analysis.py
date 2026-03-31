"""반도체 업황 분석 모듈 테스트."""

import pytest

from src.analysis.semiconductor import (
    compute_relative_performance,
    compute_sox_trend,
    compute_semiconductor_momentum,
)


class TestComputeRelativePerformance:
    """삼성전자 vs SK하이닉스 상대 성과 분석 테스트."""

    def _make_prices(self, base: float, changes: list[float]) -> list[float]:
        prices = [base]
        for c in changes:
            prices.append(prices[-1] * (1 + c / 100))
        return prices

    def test_samsung_outperforms(self):
        """삼성전자가 하이닉스를 상회하면 양수 alpha."""
        samsung = self._make_prices(55000, [1.0] * 20)
        hynix = self._make_prices(200000, [0.2] * 20)
        result = compute_relative_performance(samsung, hynix)

        assert result is not None
        assert result["alpha_5d"] > 0
        assert result["alpha_20d"] > 0
        assert result["relative_trend"] == "outperform"

    def test_samsung_underperforms(self):
        """삼성전자가 하이닉스를 하회하면 음수 alpha."""
        samsung = self._make_prices(55000, [-0.5] * 20)
        hynix = self._make_prices(200000, [0.5] * 20)
        result = compute_relative_performance(samsung, hynix)

        assert result is not None
        assert result["alpha_5d"] < 0
        assert result["relative_trend"] == "underperform"

    def test_neutral(self):
        """비슷한 수익률이면 neutral."""
        samsung = self._make_prices(55000, [0.1] * 20)
        hynix = self._make_prices(200000, [0.1] * 20)
        result = compute_relative_performance(samsung, hynix)

        assert result is not None
        assert result["relative_trend"] == "neutral"

    def test_insufficient_data(self):
        """데이터 부족 시 None."""
        assert compute_relative_performance([55000], [200000]) is None

    def test_length_mismatch(self):
        """배열 길이 불일치 시 None."""
        assert compute_relative_performance([55000, 56000], [200000]) is None

    def test_required_keys(self):
        """필수 키 확인."""
        samsung = self._make_prices(55000, [0.3] * 25)
        hynix = self._make_prices(200000, [0.2] * 25)
        result = compute_relative_performance(samsung, hynix)

        expected_keys = {
            "samsung_return_5d", "samsung_return_20d",
            "hynix_return_5d", "hynix_return_20d",
            "alpha_5d", "alpha_20d",
            "rs_current", "rs_ma20", "relative_trend",
        }
        assert expected_keys.issubset(result.keys())


class TestComputeSoxTrend:
    """SOX 지수 추세 분석 테스트."""

    def test_uptrend(self):
        """상승 추세 감지."""
        closes = [4000 + i * 50 for i in range(30)]
        result = compute_sox_trend(closes)

        assert result is not None
        assert result["trend"] == "상승"
        assert result["change_pct"] > 0

    def test_downtrend(self):
        """하락 추세 감지."""
        closes = [5000 - i * 50 for i in range(30)]
        result = compute_sox_trend(closes)

        assert result is not None
        assert result["trend"] == "하락"
        assert result["change_pct"] < 0

    def test_sideways(self):
        """횡보 추세 감지."""
        closes = [4500 + (i % 2) * 10 for i in range(30)]
        result = compute_sox_trend(closes)

        assert result is not None
        assert result["trend"] == "횡보"

    def test_insufficient_data(self):
        """데이터 부족 시 None."""
        assert compute_sox_trend([4500]) is None

    def test_required_keys(self):
        """필수 키 확인."""
        closes = [4000 + i * 10 for i in range(30)]
        result = compute_sox_trend(closes)

        expected_keys = {"trend", "change_pct", "ma20", "current", "strength"}
        assert expected_keys.issubset(result.keys())


class TestComputeSemiconductorMomentum:
    """반도체 섹터 모멘텀 스코어 테스트."""

    def test_strong_positive(self):
        """모든 지표 긍정 → 높은 양수 스코어."""
        rel_perf = {
            "alpha_5d": 3.0, "alpha_20d": 5.0,
            "relative_trend": "outperform",
        }
        sox_trend = {
            "trend": "상승", "change_pct": 10.0,
            "strength": 0.8,
        }
        score = compute_semiconductor_momentum(rel_perf, sox_trend)
        assert -100 <= score <= 100
        assert score > 30

    def test_strong_negative(self):
        """모든 지표 부정 → 낮은 음수 스코어."""
        rel_perf = {
            "alpha_5d": -3.0, "alpha_20d": -5.0,
            "relative_trend": "underperform",
        }
        sox_trend = {
            "trend": "하락", "change_pct": -10.0,
            "strength": -0.8,
        }
        score = compute_semiconductor_momentum(rel_perf, sox_trend)
        assert -100 <= score <= 100
        assert score < -30

    def test_mixed_signals(self):
        """혼합 신호 → 중립 부근."""
        rel_perf = {
            "alpha_5d": 1.0, "alpha_20d": -1.0,
            "relative_trend": "neutral",
        }
        sox_trend = {
            "trend": "횡보", "change_pct": 0.5,
            "strength": 0.0,
        }
        score = compute_semiconductor_momentum(rel_perf, sox_trend)
        assert -100 <= score <= 100
        assert -30 <= score <= 30

    def test_none_inputs(self):
        """입력이 None이면 0."""
        assert compute_semiconductor_momentum(None, None) == 0
        assert compute_semiconductor_momentum(None, {"trend": "상승", "change_pct": 5.0, "strength": 0.5}) == 0

    def test_score_clamped(self):
        """스코어는 항상 -100~+100 범위."""
        rel_perf = {
            "alpha_5d": 50.0, "alpha_20d": 50.0,
            "relative_trend": "outperform",
        }
        sox_trend = {
            "trend": "상승", "change_pct": 50.0,
            "strength": 1.0,
        }
        score = compute_semiconductor_momentum(rel_perf, sox_trend)
        assert -100 <= score <= 100
