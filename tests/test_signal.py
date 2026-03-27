"""종합 투자 시그널 모듈 테스트."""

import pytest

from src.analysis.signal import compute_composite_signal


# ---------------------------------------------------------------------------
# 헬퍼: 각 축 분석 결과 생성
# ---------------------------------------------------------------------------

def _tech(rsi=50.0, macd_histogram=0.0, bb_pctb=0.5,
          price_vs_ma5_pct=0.0, price_vs_ma20_pct=0.0,
          volume_ratio_5d=1.0) -> dict:
    """기술적 분석 결과 stub."""
    return {
        "current_price": 55000,
        "rsi_14": rsi,
        "macd": 0.0,
        "macd_signal": 0.0,
        "macd_histogram": macd_histogram,
        "bb_pctb": bb_pctb,
        "price_vs_ma5_pct": price_vs_ma5_pct,
        "price_vs_ma20_pct": price_vs_ma20_pct,
        "volume_ratio_5d": volume_ratio_5d,
        "ma5": 55000,
        "ma20": 54000,
        "ma60": 53000,
    }


def _supply(judgment="neutral") -> dict:
    """수급 분석 결과 stub."""
    return {
        "overall_judgment": judgment,
        "foreign_consecutive_net_buy": 0,
        "foreign_consecutive_net_sell": 0,
        "institution_consecutive_net_buy": 0,
        "institution_consecutive_net_sell": 0,
        "foreign_cumulative_5d": 0,
        "institution_cumulative_5d": 0,
        "ownership_trend": "sideways",
        "ownership_change_pct": 0.0,
    }


def _fx(trend="보합", change_1d_pct=0.0) -> dict:
    """환율 분석 결과 stub."""
    return {
        "current_rate": 1350.0,
        "trend": trend,
        "change_1d_pct": change_1d_pct,
        "change_5d_pct": 0.0,
        "correlation_20d": None,
    }


# ---------------------------------------------------------------------------
# 테스트
# ---------------------------------------------------------------------------

class TestCompositeSignal:
    """종합 시그널 계산 테스트."""

    def test_neutral_inputs_give_neutral(self):
        """모든 축이 중립이면 종합도 중립."""
        result = compute_composite_signal(_tech(), _supply(), _fx())
        assert result["score"] == pytest.approx(0.0, abs=15)
        assert result["grade"] == "중립"

    def test_strong_bullish(self):
        """기술·수급 모두 강하게 매수면 강력매수신호."""
        tech = _tech(rsi=35, macd_histogram=500, bb_pctb=0.1,
                     price_vs_ma5_pct=2.0, price_vs_ma20_pct=5.0)
        supply = _supply(judgment="buy_dominant")
        fx = _fx(trend="원화약세")
        result = compute_composite_signal(tech, supply, fx)
        assert result["score"] > 60
        assert result["grade"] == "강력매수신호"

    def test_strong_bearish(self):
        """기술·수급 모두 강하게 매도면 강력매도신호."""
        tech = _tech(rsi=80, macd_histogram=-500, bb_pctb=0.95,
                     price_vs_ma5_pct=-3.0, price_vs_ma20_pct=-5.0)
        supply = _supply(judgment="sell_dominant")
        fx = _fx(trend="원화강세")
        result = compute_composite_signal(tech, supply, fx)
        assert result["score"] < -60
        assert result["grade"] == "강력매도신호"

    def test_score_range(self):
        """점수는 -100 ~ +100 범위."""
        # 극단적 매수
        tech = _tech(rsi=10, macd_histogram=1000, bb_pctb=0.0,
                     price_vs_ma5_pct=5.0, price_vs_ma20_pct=10.0,
                     volume_ratio_5d=3.0)
        supply = _supply(judgment="buy_dominant")
        fx = _fx(trend="원화약세", change_1d_pct=2.0)
        result = compute_composite_signal(tech, supply, fx)
        assert -100 <= result["score"] <= 100

        # 극단적 매도
        tech2 = _tech(rsi=95, macd_histogram=-1000, bb_pctb=1.0,
                      price_vs_ma5_pct=-5.0, price_vs_ma20_pct=-10.0,
                      volume_ratio_5d=0.3)
        supply2 = _supply(judgment="sell_dominant")
        fx2 = _fx(trend="원화강세", change_1d_pct=-2.0)
        result2 = compute_composite_signal(tech2, supply2, fx2)
        assert -100 <= result2["score"] <= 100

    def test_grade_levels(self):
        """5단계 판정이 올바른 문자열인지 확인."""
        valid_grades = {"강력매수신호", "매수우세", "중립", "매도우세", "강력매도신호"}
        result = compute_composite_signal(_tech(), _supply(), _fx())
        assert result["grade"] in valid_grades

    def test_result_has_breakdown(self):
        """결과에 각 축 점수 분해가 포함되는지 확인."""
        result = compute_composite_signal(_tech(), _supply(), _fx())
        assert "technical_score" in result
        assert "supply_score" in result
        assert "exchange_score" in result
        assert "score" in result
        assert "grade" in result

    def test_weights_sum_to_100(self):
        """가중치 합이 100%."""
        result = compute_composite_signal(_tech(), _supply(), _fx())
        weights = result.get("weights", {})
        assert weights.get("technical") == 40
        assert weights.get("supply") == 40
        assert weights.get("exchange") == 20

    def test_buy_dominant_supply_positive_score(self):
        """수급 매수 우위면 supply_score가 양수."""
        result = compute_composite_signal(
            _tech(), _supply(judgment="buy_dominant"), _fx())
        assert result["supply_score"] > 0

    def test_sell_dominant_supply_negative_score(self):
        """수급 매도 우위면 supply_score가 음수."""
        result = compute_composite_signal(
            _tech(), _supply(judgment="sell_dominant"), _fx())
        assert result["supply_score"] < 0

    def test_none_values_handled(self):
        """지표 값이 None이어도 에러 없이 동작."""
        tech = _tech()
        tech["rsi_14"] = None
        tech["macd_histogram"] = None
        tech["bb_pctb"] = None
        tech["volume_ratio_5d"] = None
        result = compute_composite_signal(tech, _supply(), _fx())
        assert -100 <= result["score"] <= 100

    def test_obv_bearish_divergence_lowers_score(self):
        """OBV bearish divergence(가격↑+OBV↓)면 기술적 점수가 감소."""
        tech_no_div = _tech()
        tech_no_div["obv_divergence"] = None
        score_no_div = compute_composite_signal(tech_no_div, _supply(), _fx())

        tech_bearish = _tech()
        tech_bearish["obv_divergence"] = "bearish"
        score_bearish = compute_composite_signal(tech_bearish, _supply(), _fx())

        assert score_bearish["technical_score"] < score_no_div["technical_score"]

    def test_obv_bullish_divergence_raises_score(self):
        """OBV bullish divergence(가격↓+OBV↑)면 기술적 점수가 증가."""
        tech_no_div = _tech()
        tech_no_div["obv_divergence"] = None
        score_no_div = compute_composite_signal(tech_no_div, _supply(), _fx())

        tech_bullish = _tech()
        tech_bullish["obv_divergence"] = "bullish"
        score_bullish = compute_composite_signal(tech_bullish, _supply(), _fx())

        assert score_bullish["technical_score"] > score_no_div["technical_score"]

    def test_obv_divergence_none_no_effect(self):
        """OBV divergence가 None이면 점수에 영향 없음."""
        tech1 = _tech()
        tech1["obv_divergence"] = None
        tech2 = _tech()
        # obv_divergence 키가 없는 경우도 동일
        result1 = compute_composite_signal(tech1, _supply(), _fx())
        result2 = compute_composite_signal(tech2, _supply(), _fx())
        assert result1["technical_score"] == pytest.approx(result2["technical_score"])

    def test_stochastic_oversold_raises_score(self):
        """스토캐스틱 %K ≤ 20이면 기술적 점수가 상승."""
        tech_neutral = _tech()
        tech_neutral["stoch_k"] = 50.0
        score_neutral = compute_composite_signal(tech_neutral, _supply(), _fx())

        tech_oversold = _tech()
        tech_oversold["stoch_k"] = 15.0
        score_oversold = compute_composite_signal(tech_oversold, _supply(), _fx())

        assert score_oversold["technical_score"] > score_neutral["technical_score"]

    def test_stochastic_overbought_lowers_score(self):
        """스토캐스틱 %K ≥ 80이면 기술적 점수가 하락."""
        tech_neutral = _tech()
        tech_neutral["stoch_k"] = 50.0
        score_neutral = compute_composite_signal(tech_neutral, _supply(), _fx())

        tech_overbought = _tech()
        tech_overbought["stoch_k"] = 85.0
        score_overbought = compute_composite_signal(tech_overbought, _supply(), _fx())

        assert score_overbought["technical_score"] < score_neutral["technical_score"]

    def test_stochastic_none_no_effect(self):
        """스토캐스틱이 None이면 점수에 영향 없음."""
        tech1 = _tech()
        tech1["stoch_k"] = None
        tech2 = _tech()
        # stoch_k 키가 없는 경우
        result1 = compute_composite_signal(tech1, _supply(), _fx())
        result2 = compute_composite_signal(tech2, _supply(), _fx())
        assert result1["technical_score"] == pytest.approx(result2["technical_score"])
