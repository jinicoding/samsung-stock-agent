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


class TestTrendReversalIntegration:
    """추세 전환 감지 결과가 종합 시그널에 반영되는지 테스트."""

    def test_strong_bullish_reversal_boosts_score(self):
        """strong bullish 컨버전스 → 종합 점수가 상승."""
        reversal = {
            "direction": "bullish",
            "convergence": "strong",
            "score": 80.0,
            "active_categories": 4,
            "category_signals": {},
            "summary": "강한 강세 반전 신호",
        }
        base = compute_composite_signal(_tech(), _supply(), _fx())
        boosted = compute_composite_signal(
            _tech(), _supply(), _fx(), trend_reversal=reversal,
        )
        assert boosted["score"] > base["score"]

    def test_strong_bearish_reversal_lowers_score(self):
        """strong bearish 컨버전스 → 종합 점수가 하락."""
        reversal = {
            "direction": "bearish",
            "convergence": "strong",
            "score": 80.0,
            "active_categories": 4,
            "category_signals": {},
            "summary": "강한 약세 반전 신호",
        }
        base = compute_composite_signal(_tech(), _supply(), _fx())
        lowered = compute_composite_signal(
            _tech(), _supply(), _fx(), trend_reversal=reversal,
        )
        assert lowered["score"] < base["score"]

    def test_moderate_reversal_has_smaller_effect(self):
        """moderate 컨버전스 효과가 strong보다 작다."""
        strong = {
            "direction": "bullish", "convergence": "strong",
            "score": 80.0, "active_categories": 4,
            "category_signals": {}, "summary": "",
        }
        moderate = {
            "direction": "bullish", "convergence": "moderate",
            "score": 60.0, "active_categories": 3,
            "category_signals": {}, "summary": "",
        }
        r_strong = compute_composite_signal(
            _tech(), _supply(), _fx(), trend_reversal=strong,
        )
        r_moderate = compute_composite_signal(
            _tech(), _supply(), _fx(), trend_reversal=moderate,
        )
        assert r_strong["score"] > r_moderate["score"]

    def test_weak_reversal_no_effect(self):
        """weak/none 컨버전스 → 점수 변화 없음."""
        weak = {
            "direction": "bullish", "convergence": "weak",
            "score": 30.0, "active_categories": 1,
            "category_signals": {}, "summary": "",
        }
        base = compute_composite_signal(_tech(), _supply(), _fx())
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), trend_reversal=weak,
        )
        assert result["score"] == pytest.approx(base["score"])

    def test_none_reversal_no_effect(self):
        """trend_reversal=None이면 기존 동작과 동일."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), trend_reversal=None,
        )
        assert result["score"] == pytest.approx(base["score"])

    def test_score_still_clamped(self):
        """보너스 적용 후에도 -100~+100 범위."""
        reversal = {
            "direction": "bullish", "convergence": "strong",
            "score": 100.0, "active_categories": 5,
            "category_signals": {}, "summary": "",
        }
        tech = _tech(rsi=10, macd_histogram=1000, bb_pctb=0.0, price_vs_ma5_pct=5.0)
        result = compute_composite_signal(
            tech, _supply("buy_dominant"), _fx("원화약세", 2.0),
            trend_reversal=reversal,
        )
        assert -100 <= result["score"] <= 100


def _fund(per_val="적정", pbr_val="적정", outlook="유지", div_attr="보통") -> dict:
    """펀더멘털 분석 결과 stub."""
    return {
        "per": 12.0, "eps": 5000, "estimated_per": 11.0, "estimated_eps": 5500,
        "pbr": 1.2, "bps": 45000, "dividend_yield": 2.0,
        "per_valuation": per_val,
        "pbr_valuation": pbr_val,
        "earnings_outlook": outlook,
        "dividend_attractiveness": div_attr,
    }


class TestFundamentalsIntegration:
    """펀더멘털 분석 결과가 종합 시그널에 반영되는지 테스트."""

    def test_undervalued_boosts_score(self):
        """PER/PBR 저평가 → 종합 점수가 상승."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        boosted = compute_composite_signal(
            _tech(), _supply(), _fx(),
            fundamentals=_fund(per_val="저평가", pbr_val="저평가", outlook="개선", div_attr="매력적"),
        )
        assert boosted["score"] > base["score"]

    def test_overvalued_lowers_score(self):
        """PER/PBR 고평가 → 종합 점수가 하락."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        lowered = compute_composite_signal(
            _tech(), _supply(), _fx(),
            fundamentals=_fund(per_val="고평가", pbr_val="고평가", outlook="악화", div_attr="낮음"),
        )
        assert lowered["score"] < base["score"]

    def test_fundamentals_score_in_result(self):
        """결과에 fundamentals_score가 포함."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), fundamentals=_fund(),
        )
        assert "fundamentals_score" in result

    def test_none_fundamentals_no_score(self):
        """fundamentals=None이면 fundamentals_score 없음."""
        result = compute_composite_signal(_tech(), _supply(), _fx())
        assert "fundamentals_score" not in result

    def test_5axis_weights_with_rs_and_fund(self):
        """RS + 펀더멘털 모두 있으면 5축 가중치 합 100%."""
        rs = {"rs_trend": "neutral", "alpha_1d": 0.0}
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            relative_strength=rs, fundamentals=_fund(),
        )
        w = result["weights"]
        assert w == {"technical": 30, "supply": 30, "exchange": 15,
                     "relative_strength": 10, "fundamentals": 15}
        assert sum(w.values()) == 100

    def test_4axis_fund_only_weights(self):
        """펀더멘털만 있고 RS 없으면 4축 가중치."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), fundamentals=_fund(),
        )
        w = result["weights"]
        assert w == {"technical": 35, "supply": 30, "exchange": 15, "fundamentals": 20}
        assert sum(w.values()) == 100

    def test_earnings_improvement_positive(self):
        """실적 개선 전망 → 양수 점수 기여."""
        neutral = compute_composite_signal(
            _tech(), _supply(), _fx(),
            fundamentals=_fund(outlook="유지"),
        )
        improved = compute_composite_signal(
            _tech(), _supply(), _fx(),
            fundamentals=_fund(outlook="개선"),
        )
        assert improved["fundamentals_score"] > neutral["fundamentals_score"]

    def test_score_clamped_with_fundamentals(self):
        """펀더멘털 포함 시에도 -100~+100 범위."""
        tech = _tech(rsi=10, macd_histogram=1000, bb_pctb=0.0, price_vs_ma5_pct=5.0)
        result = compute_composite_signal(
            tech, _supply("buy_dominant"), _fx("원화약세", 2.0),
            fundamentals=_fund(per_val="저평가", pbr_val="저평가", outlook="개선", div_attr="매력적"),
        )
        assert -100 <= result["score"] <= 100


def _news(label="neutral", score=0, positive=0, negative=0, neutral=5, count=5) -> dict:
    """뉴스 감정 요약 stub."""
    return {
        "label": label,
        "score": score,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "count": count,
    }


class TestNewsSentimentIntegration:
    """뉴스 감정 분석이 종합 시그널에 반영되는지 테스트."""

    def test_bullish_news_boosts_score(self):
        """bullish 뉴스 → 종합 점수 상승."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        boosted = compute_composite_signal(
            _tech(), _supply(), _fx(),
            news_sentiment=_news(label="bullish", score=5, positive=8, negative=3, count=15),
        )
        assert boosted["score"] > base["score"]

    def test_bearish_news_lowers_score(self):
        """bearish 뉴스 → 종합 점수 하락."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        lowered = compute_composite_signal(
            _tech(), _supply(), _fx(),
            news_sentiment=_news(label="bearish", score=-5, positive=2, negative=7, count=15),
        )
        assert lowered["score"] < base["score"]

    def test_neutral_news_minimal_effect(self):
        """neutral 뉴스 → 점수 변화 미미."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            news_sentiment=_news(label="neutral", score=0, positive=3, negative=3, count=10),
        )
        assert abs(result["score"] - base["score"]) < 15

    def test_news_score_in_result(self):
        """결과에 news_score가 포함."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            news_sentiment=_news(),
        )
        assert "news_score" in result

    def test_no_news_no_score(self):
        """news_sentiment=None이면 news_score 없음."""
        result = compute_composite_signal(_tech(), _supply(), _fx())
        assert "news_score" not in result

    def test_6axis_weights_all_present(self):
        """RS + 펀더멘털 + 뉴스 모두 있으면 6축 가중치 합 100%."""
        rs = {"rs_trend": "neutral", "alpha_1d": 0.0}
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            relative_strength=rs, fundamentals=_fund(),
            news_sentiment=_news(),
        )
        w = result["weights"]
        assert "news" in w
        assert sum(w.values()) == 100

    def test_score_clamped_with_news(self):
        """뉴스 포함 시에도 -100~+100 범위."""
        tech = _tech(rsi=10, macd_histogram=1000, bb_pctb=0.0, price_vs_ma5_pct=5.0)
        result = compute_composite_signal(
            tech, _supply("buy_dominant"), _fx("원화약세", 2.0),
            news_sentiment=_news(label="bullish", score=10, positive=15, negative=5, count=20),
        )
        assert -100 <= result["score"] <= 100


def _cons(valuation="적정", rec_label="매수유지", tone="중립") -> dict:
    """컨센서스 분석 결과 stub."""
    return {
        "target_price": 250000,
        "current_price": 200000,
        "divergence_pct": 25.0,
        "valuation": valuation,
        "recommendation": 4.0,
        "recommendation_label": rec_label,
        "researches": [],
        "research_tone": tone,
    }


class TestConsensusIntegration:
    """컨센서스 분석이 종합 시그널에 반영되는지 테스트."""

    def test_undervalued_consensus_boosts_score(self):
        """저평가+매수 → 점수 상승."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        boosted = compute_composite_signal(
            _tech(), _supply(), _fx(),
            consensus=_cons(valuation="저평가", rec_label="매수", tone="긍정"),
        )
        assert boosted["score"] > base["score"]

    def test_overvalued_consensus_lowers_score(self):
        """고평가+매도 → 점수 하락."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        lowered = compute_composite_signal(
            _tech(), _supply(), _fx(),
            consensus=_cons(valuation="고평가", rec_label="매도", tone="부정"),
        )
        assert lowered["score"] < base["score"]

    def test_consensus_score_in_result(self):
        """결과에 consensus_score가 포함."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), consensus=_cons(),
        )
        assert "consensus_score" in result

    def test_no_consensus_no_score(self):
        """consensus=None이면 consensus_score 없음."""
        result = compute_composite_signal(_tech(), _supply(), _fx())
        assert "consensus_score" not in result

    def test_consensus_weight_is_10(self):
        """컨센서스 축 가중치는 10%."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), consensus=_cons(),
        )
        assert result["weights"]["consensus"] == 10

    def test_weights_sum_to_100_with_consensus(self):
        """컨센서스 포함 시 가중치 합 100%."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), consensus=_cons(),
        )
        assert sum(result["weights"].values()) == 100

    def test_weights_sum_to_100_all_axes(self):
        """모든 축(RS+펀더멘털+뉴스+컨센서스) 포함 시 가중치 합 100%."""
        rs = {"rs_trend": "neutral", "alpha_1d": 0.0}
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            relative_strength=rs, fundamentals=_fund(),
            news_sentiment=_news(), consensus=_cons(),
        )
        assert sum(result["weights"].values()) == 100
        assert result["weights"]["consensus"] == 10

    def test_score_clamped_with_consensus(self):
        """컨센서스 포함 시에도 -100~+100 범위."""
        tech = _tech(rsi=10, macd_histogram=1000, bb_pctb=0.0, price_vs_ma5_pct=5.0)
        result = compute_composite_signal(
            tech, _supply("buy_dominant"), _fx("원화약세", 2.0),
            consensus=_cons(valuation="저평가", rec_label="매수", tone="긍정"),
        )
        assert -100 <= result["score"] <= 100


class TestSemiconductorIntegration:
    """반도체 업황 지표가 종합 시그널에 반영되는지 테스트."""

    def test_none_semiconductor_no_effect(self):
        """semiconductor_momentum=None이면 기존 동작 유지."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), semiconductor_momentum=None,
        )
        assert result["score"] == pytest.approx(base["score"])
        assert "semiconductor_score" not in result

    def test_positive_momentum_boosts_score(self):
        """양수 모멘텀 → 종합 점수 상승."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        boosted = compute_composite_signal(
            _tech(), _supply(), _fx(), semiconductor_momentum=60,
        )
        assert boosted["score"] > base["score"]

    def test_negative_momentum_lowers_score(self):
        """음수 모멘텀 → 종합 점수 하락."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        lowered = compute_composite_signal(
            _tech(), _supply(), _fx(), semiconductor_momentum=-60,
        )
        assert lowered["score"] < base["score"]

    def test_semiconductor_score_in_result(self):
        """결과에 semiconductor_score 키 포함."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), semiconductor_momentum=50,
        )
        assert "semiconductor_score" in result
        assert result["semiconductor_score"] == 50

    def test_semiconductor_weight_is_10(self):
        """반도체 축 가중치는 10%."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), semiconductor_momentum=50,
        )
        assert result["weights"]["semiconductor"] == 10

    def test_weights_sum_to_100_with_semiconductor(self):
        """반도체 포함 시 가중치 합 100%."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(), semiconductor_momentum=50,
        )
        assert sum(result["weights"].values()) == 100

    def test_weights_sum_to_100_all_axes(self):
        """모든 축 + 반도체 포함 시 가중치 합 100%."""
        rs = {"rs_trend": "neutral", "alpha_1d": 0.0}
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            relative_strength=rs, fundamentals=_fund(),
            news_sentiment=_news(), consensus=_cons(),
            semiconductor_momentum=30,
        )
        assert sum(result["weights"].values()) == 100
        assert result["weights"]["semiconductor"] == 10

    def test_score_clamped_with_semiconductor(self):
        """반도체 포함 시에도 -100~+100 범위."""
        tech = _tech(rsi=10, macd_histogram=1000, bb_pctb=0.0, price_vs_ma5_pct=5.0)
        result = compute_composite_signal(
            tech, _supply("buy_dominant"), _fx("원화약세", 2.0),
            semiconductor_momentum=100,
        )
        assert -100 <= result["score"] <= 100
