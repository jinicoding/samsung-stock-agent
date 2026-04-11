"""Tests for price scenario analysis module."""

import pytest

from src.analysis.scenario import build_price_scenarios


def _make_composite_signal(score: float, grade: str | None = None) -> dict:
    if grade is None:
        if score >= 60:
            grade = "강력매수신호"
        elif score >= 20:
            grade = "매수우세"
        elif score > -20:
            grade = "중립"
        elif score > -60:
            grade = "매도우세"
        else:
            grade = "강력매도신호"
    return {"score": score, "grade": grade}


def _make_support_resistance(
    nearest_support: float | None = 54000,
    nearest_resistance: float | None = 58000,
) -> dict:
    return {
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "pivot": {"pp": 56000, "s1": 55000, "s2": 54000, "r1": 57000, "r2": 58000},
        "swing_levels": [],
        "ma_levels": {"ma20": 55500, "ma60": 55000},
    }


def _make_volatility(atr: float | None = 800, atr_pct: float | None = 1.43) -> dict:
    return {
        "atr": atr,
        "atr_pct": atr_pct,
        "hv20": 25.0,
        "volatility_percentile": 50.0,
        "volatility_regime": "보통",
        "bandwidth_squeeze": False,
    }


def _make_timeframe(
    alignment: str = "neutral", score_modifier: float = 0.0
) -> dict:
    return {
        "alignment": alignment,
        "interpretation": "테스트",
        "score_modifier": score_modifier,
    }


def _make_convergence(
    level: str = "moderate",
    direction: str = "neutral",
    conviction: int = 50,
) -> dict:
    return {
        "convergence_level": level,
        "dominant_direction": direction,
        "aligned_axes": [],
        "conflicting_axes": [],
        "neutral_axes": [],
        "conviction": conviction,
    }


class TestBuildPriceScenarios:
    """Core scenario building tests."""

    def test_returns_required_keys(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(0),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        assert "scenarios" in result
        assert "dominant_scenario" in result
        assert "key_level" in result
        assert "risk_reward_comment" in result
        assert len(result["scenarios"]) == 3

    def test_scenario_labels(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(0),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        labels = {s["label"] for s in result["scenarios"]}
        assert labels == {"상승", "기본", "하락"}

    def test_each_scenario_has_conviction(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(30),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        for s in result["scenarios"]:
            assert "conviction" in s
            assert s["conviction"] in ("높음", "보통", "낮음")


class TestStrongBuySignal:
    """강력매수신호 시나리오."""

    def test_dominant_is_bullish(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(70),
            timeframe_alignment=_make_timeframe("aligned_bullish", 0.5),
            convergence=_make_convergence("strong", "bullish", 85),
        )
        assert result["dominant_scenario"] == "상승"

    def test_bullish_target_above_current(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(70),
            timeframe_alignment=_make_timeframe("aligned_bullish", 0.5),
            convergence=_make_convergence("strong", "bullish", 85),
        )
        bullish = [s for s in result["scenarios"] if s["label"] == "상승"][0]
        assert bullish["target"] > 56000

    def test_high_conviction_with_aligned_timeframe(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(70),
            timeframe_alignment=_make_timeframe("aligned_bullish", 0.5),
            convergence=_make_convergence("strong", "bullish", 85),
        )
        bullish = [s for s in result["scenarios"] if s["label"] == "상승"][0]
        assert bullish["conviction"] == "높음"


class TestStrongSellSignal:
    """강력매도신호 시나리오."""

    def test_dominant_is_bearish(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(-70),
            timeframe_alignment=_make_timeframe("aligned_bearish", -0.5),
            convergence=_make_convergence("strong", "bearish", 85),
        )
        assert result["dominant_scenario"] == "하락"

    def test_bearish_target_below_current(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(-70),
            timeframe_alignment=_make_timeframe("aligned_bearish", -0.5),
            convergence=_make_convergence("strong", "bearish", 85),
        )
        bearish = [s for s in result["scenarios"] if s["label"] == "하락"][0]
        assert bearish["target"] < 56000


class TestNeutralSignal:
    """중립 시나리오."""

    def test_dominant_is_neutral(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(5),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence("mixed", "neutral", 30),
        )
        assert result["dominant_scenario"] == "기본"

    def test_base_scenario_has_range(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(atr=800),
            composite_signal=_make_composite_signal(5),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence("mixed", "neutral", 30),
        )
        base = [s for s in result["scenarios"] if s["label"] == "기본"][0]
        assert "range" in base
        assert len(base["range"]) == 2
        assert base["range"][0] < 56000 < base["range"][1]


class TestBuyLeanSignal:
    """매수우세 시나리오."""

    def test_dominant_is_bullish(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(35),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence("moderate", "bullish", 55),
        )
        assert result["dominant_scenario"] == "상승"


class TestSellLeanSignal:
    """매도우세 시나리오."""

    def test_dominant_is_bearish(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(-35),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence("moderate", "bearish", 55),
        )
        assert result["dominant_scenario"] == "하락"


class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_no_support_resistance(self):
        """지지/저항 데이터가 없을 때 ATR 기반 폴백."""
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(
                nearest_support=None, nearest_resistance=None
            ),
            volatility=_make_volatility(atr=800),
            composite_signal=_make_composite_signal(50),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        bullish = [s for s in result["scenarios"] if s["label"] == "상승"][0]
        assert bullish["target"] is not None
        bearish = [s for s in result["scenarios"] if s["label"] == "하락"][0]
        assert bearish["target"] is not None

    def test_no_atr(self):
        """ATR 없을 때 지지/저항 기반 폴백."""
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(atr=None, atr_pct=None),
            composite_signal=_make_composite_signal(50),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        bullish = [s for s in result["scenarios"] if s["label"] == "상승"][0]
        assert bullish["target"] is not None

    def test_no_atr_no_sr(self):
        """ATR도 지지/저항도 없을 때 현재가 기반 추정."""
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(
                nearest_support=None, nearest_resistance=None
            ),
            volatility=_make_volatility(atr=None, atr_pct=None),
            composite_signal=_make_composite_signal(50),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        assert len(result["scenarios"]) == 3
        bullish = [s for s in result["scenarios"] if s["label"] == "상승"][0]
        assert bullish["target"] > 56000

    def test_risk_reward_comment_format(self):
        """리스크/리워드 코멘트 형식 확인."""
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(30),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        comment = result["risk_reward_comment"]
        assert "상승 여력" in comment
        assert "하방 리스크" in comment
        assert "%" in comment

    def test_key_level_is_numeric(self):
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(0),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        assert isinstance(result["key_level"], (int, float))

    def test_low_convergence_reduces_conviction(self):
        """수렴도가 낮으면 확신도도 낮아져야 한다."""
        high_conv = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(50),
            timeframe_alignment=_make_timeframe("aligned_bullish", 0.5),
            convergence=_make_convergence("strong", "bullish", 90),
        )
        low_conv = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(50),
            timeframe_alignment=_make_timeframe("divergent_bullish", 0.2),
            convergence=_make_convergence("weak", "bullish", 25),
        )
        # conviction 순서: 높음 > 보통 > 낮음
        conv_rank = {"높음": 3, "보통": 2, "낮음": 1}
        high_bull = [s for s in high_conv["scenarios"] if s["label"] == "상승"][0]
        low_bull = [s for s in low_conv["scenarios"] if s["label"] == "상승"][0]
        assert conv_rank[high_bull["conviction"]] >= conv_rank[low_bull["conviction"]]

    def test_scenarios_have_trigger(self):
        """모든 시나리오에 trigger 문자열이 있어야 한다."""
        result = build_price_scenarios(
            current_price=56000,
            support_resistance=_make_support_resistance(),
            volatility=_make_volatility(),
            composite_signal=_make_composite_signal(30),
            timeframe_alignment=_make_timeframe(),
            convergence=_make_convergence(),
        )
        for s in result["scenarios"]:
            assert "trigger" in s
            assert isinstance(s["trigger"], str)
            assert len(s["trigger"]) > 0
