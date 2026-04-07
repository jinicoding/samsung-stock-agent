"""글로벌 매크로 분석 모듈 테스트 (NASDAQ 추세 + VIX 리스크 해석)."""

import pytest

from src.analysis.global_macro import (
    analyze_nasdaq_trend,
    analyze_vix_risk,
    compute_global_macro_score,
)


class TestAnalyzeNasdaqTrend:
    """NASDAQ 추세 분석 테스트."""

    def test_insufficient_data_returns_none(self):
        assert analyze_nasdaq_trend([100, 101, 102, 103]) is None  # < 5개

    def test_uptrend(self):
        # 꾸준히 상승하는 25개 데이터
        closes = [100 + i * 2 for i in range(25)]
        result = analyze_nasdaq_trend(closes)
        assert result is not None
        assert result["trend"] == "상승"
        assert result["ma5"] is not None
        assert result["ma20"] is not None
        assert result["momentum_strength"] > 0
        assert -1.0 <= result["momentum_strength"] <= 1.0

    def test_downtrend(self):
        closes = [200 - i * 3 for i in range(25)]
        result = analyze_nasdaq_trend(closes)
        assert result["trend"] == "하락"
        assert result["momentum_strength"] < 0

    def test_sideways(self):
        # 거의 변동 없는 데이터
        closes = [100.0 + (i % 2) * 0.1 for i in range(25)]
        result = analyze_nasdaq_trend(closes)
        assert result["trend"] == "보합"

    def test_result_keys(self):
        closes = [100 + i for i in range(25)]
        result = analyze_nasdaq_trend(closes)
        expected_keys = {"trend", "change_5d_pct", "change_20d_pct", "ma5", "ma20", "current", "momentum_strength"}
        assert set(result.keys()) == expected_keys

    def test_short_data_no_ma20(self):
        # 5~19개: ma20은 None
        closes = [100 + i for i in range(10)]
        result = analyze_nasdaq_trend(closes)
        assert result is not None
        assert result["ma20"] is None
        assert result["ma5"] is not None


class TestAnalyzeVixRisk:
    """VIX 리스크 분석 테스트."""

    def test_insufficient_data_returns_none(self):
        assert analyze_vix_risk([15.0, 16.0]) is None  # < 3개

    def test_stable_market(self):
        closes = [15.0, 14.5, 15.2, 14.8, 15.0]
        result = analyze_vix_risk(closes)
        assert result["risk_level"] == "안정"
        assert result["current"] == 15.0

    def test_caution_market(self):
        closes = [18.0, 20.0, 22.0, 25.0, 24.0]
        result = analyze_vix_risk(closes)
        assert result["risk_level"] == "경계"

    def test_fear_market(self):
        closes = [25.0, 28.0, 32.0, 35.0, 38.0]
        result = analyze_vix_risk(closes)
        assert result["risk_level"] == "공포"

    def test_vix_trend_rising(self):
        closes = [15.0, 17.0, 20.0, 23.0, 26.0]
        result = analyze_vix_risk(closes)
        assert result["vix_trend"] == "상승"

    def test_vix_trend_falling(self):
        closes = [30.0, 27.0, 24.0, 21.0, 18.0]
        result = analyze_vix_risk(closes)
        assert result["vix_trend"] == "하락"

    def test_result_keys(self):
        closes = [20.0, 19.5, 20.5, 21.0, 20.0]
        result = analyze_vix_risk(closes)
        expected_keys = {"risk_level", "current", "vix_trend", "change_pct", "interpretation"}
        assert set(result.keys()) == expected_keys

    def test_interpretation_text(self):
        # 공포 수준이면 해석 텍스트에 관련 키워드 포함
        closes = [30.0, 32.0, 35.0, 38.0, 40.0]
        result = analyze_vix_risk(closes)
        assert "공포" in result["interpretation"] or "리스크" in result["interpretation"]


class TestComputeGlobalMacroScore:
    """글로벌 매크로 종합 스코어 테스트."""

    def test_none_inputs_returns_zero(self):
        assert compute_global_macro_score(None, None) == 0
        assert compute_global_macro_score({"trend": "상승"}, None) == 0
        assert compute_global_macro_score(None, {"risk_level": "안정"}) == 0

    def test_positive_scenario(self):
        # NASDAQ 상승 + VIX 안정 → 긍정 스코어
        nasdaq = {
            "trend": "상승",
            "momentum_strength": 0.5,
            "change_5d_pct": 3.0,
            "change_20d_pct": 8.0,
        }
        vix = {
            "risk_level": "안정",
            "vix_trend": "하락",
            "current": 15.0,
            "change_pct": -5.0,
        }
        score = compute_global_macro_score(nasdaq, vix)
        assert score > 0
        assert -100 <= score <= 100

    def test_negative_scenario(self):
        # NASDAQ 하락 + VIX 공포 → 부정 스코어
        nasdaq = {
            "trend": "하락",
            "momentum_strength": -0.7,
            "change_5d_pct": -5.0,
            "change_20d_pct": -12.0,
        }
        vix = {
            "risk_level": "공포",
            "vix_trend": "상승",
            "current": 35.0,
            "change_pct": 20.0,
        }
        score = compute_global_macro_score(nasdaq, vix)
        assert score < 0
        assert -100 <= score <= 100

    def test_score_bounds(self):
        # 극단값에서도 -100~+100 범위 유지
        nasdaq = {
            "trend": "상승",
            "momentum_strength": 1.0,
            "change_5d_pct": 20.0,
            "change_20d_pct": 50.0,
        }
        vix = {
            "risk_level": "안정",
            "vix_trend": "하락",
            "current": 10.0,
            "change_pct": -30.0,
        }
        score = compute_global_macro_score(nasdaq, vix)
        assert -100 <= score <= 100

    def test_mixed_scenario_moderate(self):
        # NASDAQ 보합 + VIX 경계 → 중립에 가까운 스코어
        nasdaq = {
            "trend": "보합",
            "momentum_strength": 0.0,
            "change_5d_pct": 0.5,
            "change_20d_pct": 1.0,
        }
        vix = {
            "risk_level": "경계",
            "vix_trend": "보합",
            "current": 22.0,
            "change_pct": 2.0,
        }
        score = compute_global_macro_score(nasdaq, vix)
        assert -50 < score < 50  # 극단적이지 않음
