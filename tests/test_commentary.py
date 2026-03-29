"""규칙 기반 자연어 마켓 코멘터리 모듈 테스트."""

from src.analysis.commentary import generate_commentary


class TestGenerateCommentary:
    """generate_commentary 함수 테스트."""

    def _base_indicators(self, **overrides):
        base = {
            "current_price": 55000,
            "rsi_14": 50.0,
            "macd": 100.0,
            "macd_signal": 80.0,
            "macd_histogram": 20.0,
            "bb_pctb": 0.5,
            "ma5": 55000,
            "ma20": 54000,
            "ma60": 53000,
        }
        base.update(overrides)
        return base

    def _base_supply_demand(self, **overrides):
        base = {
            "foreign_consecutive_net_buy": 0,
            "foreign_consecutive_net_sell": 0,
            "institution_consecutive_net_buy": 0,
            "institution_consecutive_net_sell": 0,
            "overall_judgment": "neutral",
            "ownership_trend": "sideways",
        }
        base.update(overrides)
        return base

    def _base_exchange_rate(self, **overrides):
        base = {
            "trend": "보합",
            "change_1d_pct": 0.0,
        }
        base.update(overrides)
        return base

    def _base_composite_signal(self, **overrides):
        base = {
            "score": 0.0,
            "grade": "중립",
        }
        base.update(overrides)
        return base

    def _base_support_resistance(self, **overrides):
        base = {
            "nearest_support": 53000,
            "nearest_resistance": 57000,
        }
        base.update(overrides)
        return base

    def test_returns_nonempty_string(self):
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_bullish_foreign_consecutive_buy_and_macd_golden(self):
        """외국인 5일 연속 매수 + MACD 골든크로스 → 매수 우세 언급."""
        result = generate_commentary(
            self._base_indicators(macd_histogram=20.0),
            self._base_supply_demand(
                foreign_consecutive_net_buy=5,
                overall_judgment="buy_dominant",
            ),
            self._base_exchange_rate(),
            self._base_composite_signal(score=40.0, grade="매수우세"),
            self._base_support_resistance(),
        )
        assert "외국인" in result
        assert "순매수" in result or "매수" in result
        assert "MACD" in result or "골든크로스" in result

    def test_bearish_foreign_sell_and_macd_dead(self):
        """외국인 연속 매도 + MACD 데드크로스 → 매도 우세 언급."""
        result = generate_commentary(
            self._base_indicators(macd_histogram=-30.0),
            self._base_supply_demand(
                foreign_consecutive_net_sell=4,
                overall_judgment="sell_dominant",
            ),
            self._base_exchange_rate(),
            self._base_composite_signal(score=-40.0, grade="매도우세"),
            self._base_support_resistance(),
        )
        assert "외국인" in result
        assert "순매도" in result or "매도" in result

    def test_rsi_overbought_warning(self):
        """RSI 70 이상 → 과매수 경고."""
        result = generate_commentary(
            self._base_indicators(rsi_14=75.0),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "RSI" in result or "과매수" in result

    def test_rsi_oversold_mention(self):
        """RSI 30 이하 → 과매도 반등 기대."""
        result = generate_commentary(
            self._base_indicators(rsi_14=25.0),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "RSI" in result or "과매도" in result

    def test_exchange_rate_won_weakness(self):
        """원화약세 → 수출 수혜 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(trend="원화약세"),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "원화약세" in result or "수출" in result or "환율" in result

    def test_exchange_rate_won_strength(self):
        """원화강세 → 부담 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(trend="원화강세"),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "원화강세" in result or "환율" in result

    def test_support_resistance_near_support(self):
        """지지선 근접 시 언급."""
        result = generate_commentary(
            self._base_indicators(current_price=53500),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(nearest_support=53000),
        )
        assert "지지" in result

    def test_support_resistance_near_resistance(self):
        """저항선 근접 시 언급."""
        result = generate_commentary(
            self._base_indicators(current_price=56500),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(nearest_resistance=57000),
        )
        assert "저항" in result

    def test_strong_buy_signal(self):
        """강력매수신호 → 강한 매수 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(
                foreign_consecutive_net_buy=7,
                overall_judgment="buy_dominant",
            ),
            self._base_exchange_rate(trend="원화약세"),
            self._base_composite_signal(score=70.0, grade="강력매수신호"),
            self._base_support_resistance(),
        )
        assert "강력" in result or "강한" in result or "매수" in result

    def test_ma_alignment_positive(self):
        """정배열 언급."""
        result = generate_commentary(
            self._base_indicators(ma5=56000, ma20=55000, ma60=54000),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(score=30.0, grade="매수우세"),
            self._base_support_resistance(),
        )
        assert "정배열" in result or "이평선" in result or "이동평균" in result

    def test_ma_alignment_negative(self):
        """역배열 언급."""
        result = generate_commentary(
            self._base_indicators(ma5=53000, ma20=54000, ma60=55000),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(score=-30.0, grade="매도우세"),
            self._base_support_resistance(),
        )
        assert "역배열" in result or "이평선" in result or "이동평균" in result

    def test_none_inputs_handled(self):
        """None 입력도 에러 없이 처리."""
        result = generate_commentary(
            self._base_indicators(),
            None,
            None,
            None,
            None,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_bollinger_upper_breakout(self):
        """볼린저 상단 돌파 경고."""
        result = generate_commentary(
            self._base_indicators(bb_pctb=1.1),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "볼린저" in result or "밴드" in result or "과열" in result

    def test_bollinger_lower_breakout(self):
        """볼린저 하단 이탈 반등 기대."""
        result = generate_commentary(
            self._base_indicators(bb_pctb=-0.1),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "볼린저" in result or "밴드" in result or "반등" in result or "과매도" in result

    def test_obv_bearish_divergence_mentioned(self):
        """OBV bearish divergence → 가격-거래량 괴리 경고 문장."""
        result = generate_commentary(
            self._base_indicators(obv_divergence="bearish"),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "거래량" in result or "OBV" in result or "괴리" in result

    def test_obv_bullish_divergence_mentioned(self):
        """OBV bullish divergence → 거래량 선행 반등 신호 문장."""
        result = generate_commentary(
            self._base_indicators(obv_divergence="bullish"),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "거래량" in result or "OBV" in result or "선행" in result

    def test_obv_divergence_none_no_mention(self):
        """OBV divergence가 None이면 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(obv_divergence=None),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "괴리" not in result
        assert "OBV" not in result

    def test_stochastic_overbought_warning(self):
        """스토캐스틱 %K >= 80 → 과매수 경고 문구."""
        result = generate_commentary(
            self._base_indicators(stoch_k=85.0, stoch_d=82.0),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "스토캐스틱" in result or "과매수" in result

    def test_stochastic_oversold_mention(self):
        """스토캐스틱 %K <= 20 → 과매도 반등 기대 문구."""
        result = generate_commentary(
            self._base_indicators(stoch_k=15.0, stoch_d=18.0),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "스토캐스틱" in result or "과매도" in result

    def test_stochastic_none_no_mention(self):
        """스토캐스틱이 None이면 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(stoch_k=None, stoch_d=None),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "스토캐스틱" not in result

    def test_strong_bullish_reversal_sentence(self):
        """strong bullish 컨버전스 → 강세 반전 경고 문장 생성."""
        reversal = {
            "direction": "bullish",
            "convergence": "strong",
            "score": 80.0,
            "active_categories": 4,
            "category_signals": {},
            "summary": "강한 강세 반전 신호",
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            trend_reversal=reversal,
        )
        assert "반전" in result or "전환" in result

    def test_moderate_bearish_reversal_sentence(self):
        """moderate bearish 컨버전스 → 약세 전환 경고 문장 생성."""
        reversal = {
            "direction": "bearish",
            "convergence": "moderate",
            "score": 60.0,
            "active_categories": 3,
            "category_signals": {},
            "summary": "중간 약세 반전 신호",
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            trend_reversal=reversal,
        )
        assert "반전" in result or "전환" in result

    def test_weak_reversal_no_sentence(self):
        """weak 컨버전스 → 반전 문장 없음."""
        reversal = {
            "direction": "bullish",
            "convergence": "weak",
            "score": 30.0,
            "active_categories": 1,
            "category_signals": {},
            "summary": "",
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            trend_reversal=reversal,
        )
        # weak일 때는 반전 문장이 추가되지 않아야 함
        assert "추세 전환" not in result

    def test_no_reversal_param_backward_compat(self):
        """trend_reversal 미전달 시 기존 동작과 동일."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "추세 전환" not in result

    # --- 펀더멘털 문장 테스트 ---

    def _base_fundamentals(self, **overrides):
        base = {
            "per": 12.5, "eps": 4800, "estimated_per": 10.0, "estimated_eps": 6000,
            "pbr": 1.2, "bps": 45000, "dividend_yield": 2.0,
            "per_valuation": "적정", "pbr_valuation": "적정",
            "earnings_outlook": "유지", "dividend_attractiveness": "보통",
        }
        base.update(overrides)
        return base

    def test_undervalued_per_mentioned(self):
        """PER 저평가 → 저평가 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fundamentals=self._base_fundamentals(per_valuation="저평가", per=8.5),
        )
        assert "저평가" in result

    def test_overvalued_pbr_mentioned(self):
        """PBR 고평가 → 고평가 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fundamentals=self._base_fundamentals(pbr_valuation="고평가", pbr=1.8),
        )
        assert "고평가" in result

    def test_earnings_improvement_mentioned(self):
        """실적 개선 전망 → 실적 개선 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fundamentals=self._base_fundamentals(earnings_outlook="개선"),
        )
        assert "실적" in result and "개선" in result

    def test_earnings_deterioration_mentioned(self):
        """실적 악화 전망 → 실적 둔화 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fundamentals=self._base_fundamentals(earnings_outlook="악화"),
        )
        assert "실적" in result and "둔화" in result

    def test_attractive_dividend_mentioned(self):
        """배당수익률 매력적 → 배당 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fundamentals=self._base_fundamentals(dividend_attractiveness="매력적", dividend_yield=3.5),
        )
        assert "배당" in result

    def test_no_fundamentals_no_mention(self):
        """fundamentals=None이면 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "저평가" not in result
        assert "고평가" not in result
        assert "배당" not in result

    def test_fair_value_no_mention(self):
        """적정 밸류에이션이면 저평가/고평가 언급 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fundamentals=self._base_fundamentals(),
        )
        assert "저평가" not in result
        assert "고평가" not in result
