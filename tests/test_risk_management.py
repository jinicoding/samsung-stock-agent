"""Tests for risk management levels module."""

import pytest
from src.analysis.risk_management import (
    compute_entry_zone,
    compute_stop_level,
    compute_target_levels,
    compute_risk_reward_ratio,
    determine_position_size_guide,
    compute_risk_levels,
)


# --- Fixtures ---

@pytest.fixture
def bullish_inputs():
    return {
        "current_price": 60000,
        "nearest_support": 57000,
        "nearest_resistance": 65000,
        "atr": 1500,
        "atr_pct": 2.5,
        "volatility_regime": "보통",
        "signal_score": 55,
        "convergence_level": "strong",
        "conviction": 80,
    }


@pytest.fixture
def bearish_inputs():
    return {
        "current_price": 60000,
        "nearest_support": 57000,
        "nearest_resistance": 65000,
        "atr": 1500,
        "atr_pct": 2.5,
        "volatility_regime": "보통",
        "signal_score": -55,
        "convergence_level": "moderate",
        "conviction": 60,
    }


@pytest.fixture
def high_vol_inputs():
    return {
        "current_price": 60000,
        "nearest_support": 55000,
        "nearest_resistance": 68000,
        "atr": 3000,
        "atr_pct": 5.0,
        "volatility_regime": "고변동성",
        "signal_score": 30,
        "convergence_level": "weak",
        "conviction": 40,
    }


@pytest.fixture
def low_vol_inputs():
    return {
        "current_price": 60000,
        "nearest_support": 59000,
        "nearest_resistance": 62000,
        "atr": 600,
        "atr_pct": 1.0,
        "volatility_regime": "저변동성",
        "signal_score": 20,
        "convergence_level": "moderate",
        "conviction": 55,
    }


# --- Entry Zone Tests ---

class TestEntryZone:
    def test_strong_bullish_entry_near_current(self, bullish_inputs):
        """강한 매수 시그널: 현재가 근처 진입 구간."""
        zone = compute_entry_zone(
            bullish_inputs["current_price"],
            bullish_inputs["nearest_support"],
            bullish_inputs["atr"],
            bullish_inputs["signal_score"],
        )
        assert zone["lower"] < zone["upper"]
        assert zone["lower"] >= bullish_inputs["nearest_support"]
        assert zone["upper"] <= bullish_inputs["current_price"] + bullish_inputs["atr"]
        assert zone["direction"] == "매수"

    def test_weak_bullish_entry_near_support(self):
        """약한 매수 시그널: 지지선 근처로 구간 이동."""
        zone = compute_entry_zone(60000, 57000, 1500, 15)
        assert zone["lower"] < 60000
        assert zone["direction"] == "매수"

    def test_bearish_entry_zone(self, bearish_inputs):
        """매도 시그널: 매도 진입 구간."""
        zone = compute_entry_zone(
            bearish_inputs["current_price"],
            bearish_inputs["nearest_support"],
            bearish_inputs["atr"],
            bearish_inputs["signal_score"],
        )
        assert zone["direction"] == "매도"
        assert zone["lower"] < zone["upper"]

    def test_neutral_entry_zone(self):
        """중립 시그널: 관망 구간."""
        zone = compute_entry_zone(60000, 57000, 1500, 5)
        assert zone["direction"] == "관망"


# --- Stop Level Tests ---

class TestStopLevel:
    def test_normal_volatility_stop(self):
        """보통 변동성: ATR 1.5배 하방."""
        stop = compute_stop_level(60000, 57000, 1500, "보통")
        assert stop["price"] < 57000
        assert stop["method"] in ("지지선_ATR", "ATR_배수")

    def test_high_volatility_wider_stop(self):
        """고변동성: ATR 2.0배로 넓은 손절."""
        stop_high = compute_stop_level(60000, 55000, 3000, "고변동성")
        stop_normal = compute_stop_level(60000, 55000, 3000, "보통")
        assert stop_high["price"] < stop_normal["price"]

    def test_low_volatility_tight_stop(self):
        """저변동성: ATR 1.0배로 좁은 손절."""
        stop_low = compute_stop_level(60000, 59000, 600, "저변동성")
        stop_normal = compute_stop_level(60000, 59000, 600, "보통")
        assert stop_low["price"] > stop_normal["price"]

    def test_stop_below_support(self):
        """손절가는 지지선 아래."""
        stop = compute_stop_level(60000, 57000, 1500, "보통")
        assert stop["price"] < 57000


# --- Target Levels Tests ---

class TestTargetLevels:
    def test_bullish_targets(self):
        """매수 시그널: 저항선 + ATR 기반 목표가."""
        targets = compute_target_levels(60000, 65000, 1500, 50)
        assert targets["target_1"]["price"] == 65000
        assert targets["target_2"]["price"] > targets["target_1"]["price"]
        assert targets["direction"] == "상승"

    def test_bearish_targets(self):
        """매도 시그널: 하락 관점 목표가."""
        targets = compute_target_levels(60000, 65000, 1500, -50)
        assert targets["direction"] == "하락"
        assert targets["target_1"]["price"] < 60000

    def test_neutral_targets(self):
        """중립: 양방향 목표 제시."""
        targets = compute_target_levels(60000, 65000, 1500, 5)
        assert targets["direction"] == "중립"

    def test_target2_above_target1(self):
        """2차 목표가는 항상 1차보다 높다."""
        targets = compute_target_levels(60000, 65000, 1500, 50)
        assert targets["target_2"]["price"] > targets["target_1"]["price"]

    def test_target2_uses_atr_when_no_resistance(self):
        """저항선 없을 때 2차 목표가는 ATR 2.5배 기반."""
        targets = compute_target_levels(60000, None, 1500, 50)
        expected_t2 = max(60000 + 1500 * 2.5, targets["target_1"]["price"] + 1500)
        assert targets["target_2"]["price"] == pytest.approx(expected_t2, rel=0.01)


# --- Risk/Reward Ratio Tests ---

class TestRiskRewardRatio:
    def test_favorable_ratio(self):
        """유리한 비율 (1.5 이상)."""
        rr = compute_risk_reward_ratio(60000, 65000, 57000)
        assert rr["ratio"] == pytest.approx(5000 / 3000, rel=0.01)
        assert rr["grade"] == "유리"

    def test_neutral_ratio(self):
        """보통 비율 (1.0~1.5)."""
        rr = compute_risk_reward_ratio(60000, 62000, 58500)
        assert 1.0 <= rr["ratio"] <= 1.5
        assert rr["grade"] == "보통"

    def test_unfavorable_ratio(self):
        """불리한 비율 (1.0 미만)."""
        rr = compute_risk_reward_ratio(60000, 61000, 57000)
        assert rr["ratio"] < 1.0
        assert rr["grade"] == "불리"

    def test_zero_risk_division(self):
        """진입가 == 손절가: 비율 무한대 방지."""
        rr = compute_risk_reward_ratio(60000, 65000, 60000)
        assert rr["ratio"] is None
        assert rr["grade"] == "산출불가"


# --- Position Size Guide Tests ---

class TestPositionSizeGuide:
    def test_aggressive(self):
        """강한 시그널 + 좋은 R:R + 수렴 → 공격적."""
        guide = determine_position_size_guide("저변동성", 80, 2.5, "strong")
        assert guide["level"] == "공격적"

    def test_standard(self):
        """보통 조건 → 표준."""
        guide = determine_position_size_guide("보통", 55, 1.8, "moderate")
        assert guide["level"] == "표준"

    def test_conservative(self):
        """높은 변동성 또는 낮은 확신 → 보수적."""
        guide = determine_position_size_guide("고변동성", 50, 1.5, "weak")
        assert guide["level"] == "보수적"

    def test_wait(self):
        """불리한 R:R 또는 mixed 수렴 → 관망."""
        guide = determine_position_size_guide("보통", 30, 0.8, "mixed")
        assert guide["level"] == "관망"

    def test_no_amount_in_guide(self):
        """투자 조언 금지: 금액/주수 없음."""
        guide = determine_position_size_guide("보통", 60, 1.5, "moderate")
        result_str = str(guide)
        assert "원" not in result_str
        assert "주" not in result_str or "주의" in result_str or "주요" in result_str


# --- Integration: compute_risk_levels ---

class TestComputeRiskLevels:
    def test_full_output_structure(self, bullish_inputs):
        """통합 함수 출력 구조 검증."""
        result = compute_risk_levels(**bullish_inputs)
        assert "entry_zone" in result
        assert "stop_level" in result
        assert "target_levels" in result
        assert "risk_reward" in result
        assert "position_guide" in result
        assert "summary" in result

    def test_bullish_coherence(self, bullish_inputs):
        """매수 시나리오: 진입 < 목표, 손절 < 진입."""
        result = compute_risk_levels(**bullish_inputs)
        entry_mid = (result["entry_zone"]["lower"] + result["entry_zone"]["upper"]) / 2
        assert result["stop_level"]["price"] < entry_mid
        assert result["target_levels"]["target_1"]["price"] > entry_mid

    def test_bearish_coherence(self, bearish_inputs):
        """매도 시나리오: 목표 < 현재가."""
        result = compute_risk_levels(**bearish_inputs)
        assert result["target_levels"]["direction"] == "하락"

    def test_high_volatility_wider_range(self, high_vol_inputs):
        """고변동성: 더 넓은 진입 구간과 손절."""
        result = compute_risk_levels(**high_vol_inputs)
        entry_range = result["entry_zone"]["upper"] - result["entry_zone"]["lower"]
        assert entry_range > 1000

    def test_none_support_resistance(self):
        """지지/저항 없을 때 ATR 기반 폴백."""
        result = compute_risk_levels(
            current_price=60000,
            nearest_support=None,
            nearest_resistance=None,
            atr=1500,
            atr_pct=2.5,
            volatility_regime="보통",
            signal_score=30,
            convergence_level="moderate",
            conviction=50,
        )
        assert result["entry_zone"] is not None
        assert result["stop_level"]["price"] < 60000
        assert result["target_levels"]["target_1"]["price"] > 60000
