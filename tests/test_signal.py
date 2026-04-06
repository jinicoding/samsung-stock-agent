"""종합 투자 시그널 모듈 테스트."""

import pytest

from src.analysis.signal import adapt_weights, compute_composite_signal


# ---------------------------------------------------------------------------
# 헬퍼: 각 축 분석 결과 생성
# ---------------------------------------------------------------------------

def _tech(rsi=50.0, macd_histogram=0.0, bb_pctb=0.5,
          price_vs_ma5_pct=0.0, price_vs_ma20_pct=0.0,
          volume_ratio_5d=1.0, adx=None, plus_di=None,
          minus_di=None) -> dict:
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
        "adx": adx,
        "plus_di": plus_di,
        "minus_di": minus_di,
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

    def test_adx_strong_trend_bullish_boosts(self):
        """ADX>25이고 +DI>-DI면 기술적 점수가 ADX 없을 때보다 높다."""
        tech_no_adx = _tech(macd_histogram=100)
        tech_adx_bull = _tech(macd_histogram=100, adx=30, plus_di=28, minus_di=15)
        r_no = compute_composite_signal(tech_no_adx, _supply(), _fx())
        r_adx = compute_composite_signal(tech_adx_bull, _supply(), _fx())
        assert r_adx["technical_score"] > r_no["technical_score"]

    def test_adx_strong_trend_bearish_lowers(self):
        """ADX>25이고 -DI>+DI면 기술적 점수가 ADX 없을 때보다 낮다."""
        tech_no_adx = _tech(macd_histogram=-100)
        tech_adx_bear = _tech(macd_histogram=-100, adx=30, plus_di=12, minus_di=28)
        r_no = compute_composite_signal(tech_no_adx, _supply(), _fx())
        r_adx = compute_composite_signal(tech_adx_bear, _supply(), _fx())
        assert r_adx["technical_score"] < r_no["technical_score"]

    def test_adx_weak_trend_dampens_momentum(self):
        """ADX<20이면 모멘텀 시그널이 약화되어 극단 점수가 줄어든다."""
        tech_no_adx = _tech(rsi=30, macd_histogram=300)
        tech_weak = _tech(rsi=30, macd_histogram=300, adx=15, plus_di=20, minus_di=18)
        r_no = compute_composite_signal(tech_no_adx, _supply(), _fx())
        r_weak = compute_composite_signal(tech_weak, _supply(), _fx())
        # 약한 추세 → 시그널 약화 → 절대값이 줄어듦
        assert abs(r_weak["technical_score"]) < abs(r_no["technical_score"])

    def test_adx_none_no_effect(self):
        """ADX가 None이면 점수에 영향 없음."""
        tech1 = _tech(adx=None, plus_di=None, minus_di=None)
        tech2 = _tech()
        r1 = compute_composite_signal(tech1, _supply(), _fx())
        r2 = compute_composite_signal(tech2, _supply(), _fx())
        assert r1["technical_score"] == pytest.approx(r2["technical_score"])


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


def _vol(regime="보통", squeeze=False) -> dict:
    """변동성 분석 결과 stub."""
    return {
        "atr": 1500.0,
        "atr_pct": 2.7,
        "hv20": 0.25,
        "volatility_percentile": 50.0,
        "volatility_regime": regime,
        "bandwidth_squeeze": squeeze,
    }


class TestVolatilityIntegration:
    """변동성 분석이 종합 시그널에 반영되는지 테스트."""

    def test_high_volatility_lowers_score(self):
        """고변동성 → 종합 점수 하락."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        lowered = compute_composite_signal(
            _tech(), _supply(), _fx(),
            volatility=_vol(regime="고변동성"),
        )
        assert lowered["score"] < base["score"]

    def test_low_volatility_boosts_score(self):
        """저변동성 → 종합 점수 상승."""
        base = compute_composite_signal(_tech(), _supply(), _fx())
        boosted = compute_composite_signal(
            _tech(), _supply(), _fx(),
            volatility=_vol(regime="저변동성"),
        )
        assert boosted["score"] > base["score"]

    def test_squeeze_boosts_score(self):
        """밴드폭 수축 → 추가 상승."""
        no_squeeze = compute_composite_signal(
            _tech(), _supply(), _fx(),
            volatility=_vol(regime="보통", squeeze=False),
        )
        squeeze = compute_composite_signal(
            _tech(), _supply(), _fx(),
            volatility=_vol(regime="보통", squeeze=True),
        )
        assert squeeze["volatility_score"] > no_squeeze["volatility_score"]

    def test_volatility_score_in_result(self):
        """결과에 volatility_score 키 포함."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            volatility=_vol(),
        )
        assert "volatility_score" in result

    def test_no_volatility_no_score(self):
        """volatility=None이면 volatility_score 없음."""
        result = compute_composite_signal(_tech(), _supply(), _fx())
        assert "volatility_score" not in result

    def test_volatility_weight_is_5(self):
        """변동성 축 가중치는 5%."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            volatility=_vol(),
        )
        assert result["weights"]["volatility"] == 5

    def test_weights_sum_to_100_with_volatility(self):
        """변동성 포함 시 가중치 합 100%."""
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            volatility=_vol(),
        )
        assert sum(result["weights"].values()) == 100

    def test_weights_sum_to_100_all_axes(self):
        """모든 축 + 변동성 포함 시 가중치 합 100%."""
        rs = {"rs_trend": "neutral", "alpha_1d": 0.0}
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            relative_strength=rs, fundamentals=_fund(),
            news_sentiment=_news(), consensus=_cons(),
            semiconductor_momentum=30,
            volatility=_vol(),
        )
        assert sum(result["weights"].values()) == 100
        assert result["weights"]["volatility"] == 5

    def test_score_clamped_with_volatility(self):
        """변동성 포함 시에도 -100~+100 범위."""
        tech = _tech(rsi=10, macd_histogram=1000, bb_pctb=0.0, price_vs_ma5_pct=5.0)
        result = compute_composite_signal(
            tech, _supply("buy_dominant"), _fx("원화약세", 2.0),
            volatility=_vol(regime="저변동성", squeeze=True),
        )
        assert -100 <= result["score"] <= 100


class TestConvergenceAdjustment:
    """수렴 분석에 따른 시그널 점수 조절 테스트."""

    def test_strong_convergence_amplifies_positive_score(self):
        """strong 수렴 → 양수 점수가 10% 강화."""
        from src.analysis.signal import adjust_for_convergence
        sig = {"score": 50.0, "grade": "매수우세", "weights": {}}
        conv = {"convergence_level": "strong", "conviction": 80,
                "dominant_direction": "bullish", "aligned_axes": ["a"] * 7,
                "conflicting_axes": [], "neutral_axes": [], "axis_directions": {}}
        result = adjust_for_convergence(sig, conv)
        assert result["score"] == pytest.approx(55.0, abs=0.1)

    def test_strong_convergence_amplifies_negative_score(self):
        """strong 수렴 → 음수 점수도 절대값 10% 강화."""
        from src.analysis.signal import adjust_for_convergence
        sig = {"score": -50.0, "grade": "매도우세", "weights": {}}
        conv = {"convergence_level": "strong", "conviction": 80,
                "dominant_direction": "bearish", "aligned_axes": ["a"] * 7,
                "conflicting_axes": [], "neutral_axes": [], "axis_directions": {}}
        result = adjust_for_convergence(sig, conv)
        assert result["score"] == pytest.approx(-55.0, abs=0.1)

    def test_mixed_convergence_dampens_score(self):
        """mixed 수렴 → 점수 10% 감쇠."""
        from src.analysis.signal import adjust_for_convergence
        sig = {"score": 50.0, "grade": "매수우세", "weights": {}}
        conv = {"convergence_level": "mixed", "conviction": 20,
                "dominant_direction": "neutral", "aligned_axes": [],
                "conflicting_axes": [], "neutral_axes": [], "axis_directions": {}}
        result = adjust_for_convergence(sig, conv)
        assert result["score"] == pytest.approx(45.0, abs=0.1)

    def test_moderate_convergence_no_adjustment(self):
        """moderate 수렴 → 점수 조절 없음."""
        from src.analysis.signal import adjust_for_convergence
        sig = {"score": 50.0, "grade": "매수우세", "weights": {}}
        conv = {"convergence_level": "moderate", "conviction": 55,
                "dominant_direction": "bullish", "aligned_axes": ["a"] * 5,
                "conflicting_axes": [], "neutral_axes": [], "axis_directions": {}}
        result = adjust_for_convergence(sig, conv)
        assert result["score"] == pytest.approx(50.0, abs=0.1)

    def test_weak_convergence_no_adjustment(self):
        """weak 수렴 → 점수 조절 없음."""
        from src.analysis.signal import adjust_for_convergence
        sig = {"score": 50.0, "grade": "매수우세", "weights": {}}
        conv = {"convergence_level": "weak", "conviction": 35,
                "dominant_direction": "bullish", "aligned_axes": ["a"] * 3,
                "conflicting_axes": [], "neutral_axes": [], "axis_directions": {}}
        result = adjust_for_convergence(sig, conv)
        assert result["score"] == pytest.approx(50.0, abs=0.1)

    def test_grade_updated_after_adjustment(self):
        """점수 조정 후 grade도 재계산."""
        from src.analysis.signal import adjust_for_convergence
        sig = {"score": 58.0, "grade": "매수우세", "weights": {}}
        conv = {"convergence_level": "strong", "conviction": 80,
                "dominant_direction": "bullish", "aligned_axes": ["a"] * 7,
                "conflicting_axes": [], "neutral_axes": [], "axis_directions": {}}
        result = adjust_for_convergence(sig, conv)
        # 58 * 1.1 = 63.8 → 강력매수신호
        assert result["grade"] == "강력매수신호"

    def test_convergence_included_in_result(self):
        """결과에 convergence 데이터가 포함."""
        from src.analysis.signal import adjust_for_convergence
        sig = {"score": 50.0, "grade": "매수우세", "weights": {}}
        conv = {"convergence_level": "strong", "conviction": 80,
                "dominant_direction": "bullish", "aligned_axes": [],
                "conflicting_axes": [], "neutral_axes": [], "axis_directions": {}}
        result = adjust_for_convergence(sig, conv)
        assert "convergence" in result
        assert result["convergence"]["convergence_level"] == "strong"

    def test_score_still_clamped_after_adjustment(self):
        """조정 후에도 -100~+100 범위."""
        from src.analysis.signal import adjust_for_convergence
        sig = {"score": 98.0, "grade": "강력매수신호", "weights": {}}
        conv = {"convergence_level": "strong", "conviction": 90,
                "dominant_direction": "bullish", "aligned_axes": ["a"] * 8,
                "conflicting_axes": [], "neutral_axes": [], "axis_directions": {}}
        result = adjust_for_convergence(sig, conv)
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


# ---------------------------------------------------------------------------
# adapt_weights 테스트
# ---------------------------------------------------------------------------

def _accuracy_summary(overrides: dict | None = None) -> dict:
    """축별 정확도 요약 stub.

    기본값: 모든 축 hit_rate_5d=50%, evaluated_5d=10.
    overrides로 특정 축 값 덮어쓰기.
    """
    per_axis = {}
    for axis in (
        "technical_score", "supply_score", "exchange_score",
        "fundamentals_score", "news_score", "consensus_score",
        "semiconductor_score", "volatility_score", "candlestick_score",
    ):
        per_axis[axis] = {
            "hit_rate_5d": 50.0,
            "evaluated_5d": 10,
            "hit_rate_3d": 50.0,
            "evaluated_3d": 10,
            "hit_rate_1d": 50.0,
            "evaluated_1d": 10,
        }
    if overrides:
        for axis, vals in overrides.items():
            per_axis[axis].update(vals)
    return {"total_signals": 20, "per_axis": per_axis}


class TestAdaptWeights:
    """적응형 가중치 시스템 테스트."""

    def test_all_equal_hit_rate_no_change(self):
        """모든 축 적중률이 동일하면 가중치 변동 없음."""
        base = {"technical": 40, "supply": 40, "exchange": 20}
        summary = _accuracy_summary()
        result = adapt_weights(base, summary)
        assert result == base

    def test_high_hit_rate_increases_weight(self):
        """적중률 높은 축의 가중치가 증가."""
        base = {"technical": 40, "supply": 40, "exchange": 20}
        summary = _accuracy_summary({
            "technical_score": {"hit_rate_5d": 80.0, "evaluated_5d": 10},
        })
        result = adapt_weights(base, summary)
        assert result["technical"] > 40

    def test_low_hit_rate_decreases_weight(self):
        """적중률 낮은 축의 가중치가 감소."""
        base = {"technical": 40, "supply": 40, "exchange": 20}
        summary = _accuracy_summary({
            "technical_score": {"hit_rate_5d": 20.0, "evaluated_5d": 10},
        })
        result = adapt_weights(base, summary)
        assert result["technical"] < 40

    def test_weights_sum_to_100(self):
        """조정 후 가중치 합계는 항상 100."""
        base = {"technical": 25, "supply": 25, "exchange": 15,
                "relative_strength": 10, "fundamentals": 15, "news": 10}
        summary = _accuracy_summary({
            "technical_score": {"hit_rate_5d": 90.0, "evaluated_5d": 10},
            "supply_score": {"hit_rate_5d": 30.0, "evaluated_5d": 10},
            "news_score": {"hit_rate_5d": 70.0, "evaluated_5d": 10},
        })
        result = adapt_weights(base, summary)
        assert sum(result.values()) == 100

    def test_adjustment_within_30_percent(self):
        """가중치 조정폭은 기본값의 ±30% 이내."""
        base = {"technical": 40, "supply": 40, "exchange": 20}
        summary = _accuracy_summary({
            "technical_score": {"hit_rate_5d": 100.0, "evaluated_5d": 10},
            "supply_score": {"hit_rate_5d": 0.0, "evaluated_5d": 10},
        })
        result = adapt_weights(base, summary)
        for key in base:
            assert result[key] >= base[key] * 0.7
            assert result[key] <= base[key] * 1.3

    def test_insufficient_data_no_adjustment(self):
        """evaluated_5d < 5이면 해당 축 조정하지 않음."""
        base = {"technical": 40, "supply": 40, "exchange": 20}
        summary = _accuracy_summary({
            "technical_score": {"hit_rate_5d": 90.0, "evaluated_5d": 3},
        })
        result = adapt_weights(base, summary)
        assert result == base

    def test_none_hit_rate_no_adjustment(self):
        """hit_rate_5d가 None이면 해당 축 조정하지 않음."""
        base = {"technical": 40, "supply": 40, "exchange": 20}
        summary = _accuracy_summary({
            "technical_score": {"hit_rate_5d": None, "evaluated_5d": 10},
        })
        result = adapt_weights(base, summary)
        assert result == base

    def test_empty_accuracy_summary_no_change(self):
        """accuracy_summary가 비어있으면 가중치 변동 없음."""
        base = {"technical": 40, "supply": 40, "exchange": 20}
        summary = {"total_signals": 0, "per_axis": {}}
        result = adapt_weights(base, summary)
        assert result == base

    def test_composite_signal_with_accuracy(self):
        """compute_composite_signal에 accuracy_summary 전달 시 적응형 가중치 사용."""
        summary = _accuracy_summary({
            "technical_score": {"hit_rate_5d": 90.0, "evaluated_5d": 10},
            "supply_score": {"hit_rate_5d": 30.0, "evaluated_5d": 10},
        })
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            accuracy_summary=summary,
        )
        w = result["weights"]
        assert w["technical"] > w["supply"]
        assert sum(w.values()) == 100

    def test_composite_signal_without_accuracy_unchanged(self):
        """accuracy_summary 미제공 시 기존 정적 가중치 유지 (하위 호환)."""
        result = compute_composite_signal(_tech(), _supply(), _fx())
        assert result["weights"] == {"technical": 40, "supply": 40, "exchange": 20}

    def test_adapted_weights_in_result(self):
        """적응형 가중치 사용 시 결과에 adapted_weights 표시."""
        summary = _accuracy_summary({
            "technical_score": {"hit_rate_5d": 80.0, "evaluated_5d": 10},
        })
        result = compute_composite_signal(
            _tech(), _supply(), _fx(),
            accuracy_summary=summary,
        )
        assert result.get("adapted_weights") is True
