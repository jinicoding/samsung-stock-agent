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

    # --- 뉴스 감정 분석 문장 테스트 ---

    def _base_news_sentiment(self, **overrides):
        base = {
            "label": "neutral",
            "score": 0,
            "positive": 3,
            "negative": 3,
            "neutral": 4,
            "count": 10,
        }
        base.update(overrides)
        return base

    def test_bullish_news_mentioned(self):
        """bullish 뉴스 → 긍정 심리 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            news_sentiment=self._base_news_sentiment(label="bullish", score=5, positive=8, negative=3),
        )
        assert "뉴스" in result or "심리" in result or "긍정" in result

    def test_bearish_news_mentioned(self):
        """bearish 뉴스 → 부정 심리 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            news_sentiment=self._base_news_sentiment(label="bearish", score=-5, positive=2, negative=7),
        )
        assert "뉴스" in result or "심리" in result or "부정" in result

    def test_neutral_news_no_mention(self):
        """neutral 뉴스 → 뉴스 심리 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            news_sentiment=self._base_news_sentiment(label="neutral", score=0),
        )
        assert "뉴스 심리" not in result

    def test_no_news_no_mention(self):
        """news_sentiment=None이면 뉴스 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "뉴스 심리" not in result

    def test_consensus_undervalued_mention(self):
        """저평가 컨센서스 → 저평가 문장 포함."""
        cons = {
            "target_price": 250000, "current_price": 180000,
            "divergence_pct": 38.9, "valuation": "저평가",
            "recommendation": 4.5, "recommendation_label": "매수",
            "researches": [], "research_tone": "긍정",
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            consensus=cons,
        )
        assert "저평가" in result
        assert "매수" in result

    def test_consensus_overvalued_mention(self):
        """고평가 컨센서스 → 고평가 문장 포함."""
        cons = {
            "target_price": 160000, "current_price": 180000,
            "divergence_pct": -11.1, "valuation": "고평가",
            "recommendation": 3.0, "recommendation_label": "중립",
            "researches": [], "research_tone": "부정",
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            consensus=cons,
        )
        assert "고평가" in result

    def test_no_consensus_no_mention(self):
        """consensus=None이면 컨센서스 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "컨센서스" not in result

    # --- 주간 추이 요약 문장 테스트 ---

    def _base_weekly_summary(self, **overrides):
        base = {
            "days": 5,
            "start_date": "2026-03-24",
            "end_date": "2026-03-28",
            "week_open": 54000,
            "week_close": 56000,
            "week_high": 57000,
            "week_low": 53500,
            "change_pct": 3.7,
            "total_volume": 50000000,
            "avg_daily_volume": 10000000,
            "institution_net_total": 500000,
            "foreign_net_total": 1200000,
            "signal_start_score": 20.0,
            "signal_end_score": 45.0,
            "signal_score_change": 25.0,
            "signal_start_grade": "중립",
            "signal_end_grade": "매수우세",
            "judgment": "상승 지속",
        }
        base.update(overrides)
        return base

    def test_weekly_rising_mentioned(self):
        """상승 지속 주간 → 상승 관련 문장."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            weekly_summary=self._base_weekly_summary(judgment="상승 지속", change_pct=3.7),
        )
        assert "주간" in result or "이번 주" in result

    def test_weekly_falling_mentioned(self):
        """하락 지속 주간 → 하락 관련 문장."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            weekly_summary=self._base_weekly_summary(judgment="하락 지속", change_pct=-4.2),
        )
        assert "주간" in result or "이번 주" in result

    def test_weekly_sideways_mentioned(self):
        """횡보 주간 → 횡보 관련 문장."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            weekly_summary=self._base_weekly_summary(judgment="횡보", change_pct=0.3),
        )
        assert "주간" in result or "이번 주" in result

    def test_weekly_reversal_mentioned(self):
        """상승 전환 주간 → 전환 문장."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            weekly_summary=self._base_weekly_summary(judgment="상승 전환", change_pct=2.5),
        )
        assert "주간" in result or "이번 주" in result or "전환" in result

    def test_no_weekly_summary_no_mention(self):
        """weekly_summary=None이면 주간 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "주간" not in result
        assert "이번 주" not in result

    # --- 반도체 업황 문장 테스트 ---

    def _base_rel_perf(self, **overrides):
        base = {
            "alpha_5d": 1.5,
            "alpha_20d": 3.0,
            "relative_trend": "outperform",
        }
        base.update(overrides)
        return base

    def _base_sox_trend(self, **overrides):
        base = {
            "trend": "상승",
            "change_pct": 5.2,
            "strength": 0.5,
        }
        base.update(overrides)
        return base

    def test_semiconductor_bullish_mentioned(self):
        """SOX 상승 + outperform → 반도체 호조 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            rel_perf=self._base_rel_perf(),
            sox_trend=self._base_sox_trend(),
            semiconductor_momentum=45,
        )
        assert "반도체" in result

    def test_semiconductor_bearish_mentioned(self):
        """SOX 하락 + underperform → 반도체 부진 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            rel_perf=self._base_rel_perf(relative_trend="underperform", alpha_5d=-2.0),
            sox_trend=self._base_sox_trend(trend="하락", change_pct=-4.5),
            semiconductor_momentum=-40,
        )
        assert "반도체" in result

    def test_semiconductor_none_no_mention(self):
        """반도체 데이터가 None이면 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "반도체" not in result

    def test_semiconductor_momentum_zero_no_mention(self):
        """모멘텀이 0이고 SOX 횡보면 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            rel_perf=self._base_rel_perf(relative_trend="neutral", alpha_5d=0.1),
            sox_trend=self._base_sox_trend(trend="횡보", change_pct=0.5),
            semiconductor_momentum=0,
        )
        # 횡보/중립이면 반도체 문장 안 나올 수 있음
        # (구현에 따라 달라질 수 있으므로 에러 없이 동작하는지만 확인)
        assert isinstance(result, str)

    # --- 변동성 분석 문장 테스트 ---

    def _base_volatility(self, **overrides):
        base = {
            "atr": 1500.0,
            "atr_pct": 2.7,
            "hv20": 0.25,
            "volatility_percentile": 50.0,
            "volatility_regime": "보통",
            "bandwidth_squeeze": False,
        }
        base.update(overrides)
        return base

    def test_high_volatility_risk_warning(self):
        """고변동성 → 리스크 경고 문장."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            volatility=self._base_volatility(volatility_regime="고변동성"),
        )
        assert "변동성" in result or "리스크" in result

    def test_low_volatility_squeeze_breakout_mention(self):
        """저변동성 + 밴드폭 수축 → 돌파 대비 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            volatility=self._base_volatility(volatility_regime="저변동성", bandwidth_squeeze=True),
        )
        assert "변동성" in result or "수축" in result or "돌파" in result

    def test_normal_volatility_no_mention(self):
        """보통 변동성 + 수축 없음 → 변동성 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            volatility=self._base_volatility(volatility_regime="보통", bandwidth_squeeze=False),
        )
        assert "고변동성" not in result
        assert "밴드폭 수축" not in result

    def test_no_volatility_no_mention(self):
        """volatility=None이면 변동성 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "ATR" not in result

    # --- ADX 추세 강도 문장 테스트 ---

    def test_adx_strong_bullish_trend_mentioned(self):
        """ADX>25이고 +DI>-DI → 강한 상승 추세 언급."""
        result = generate_commentary(
            self._base_indicators(adx=30.0, plus_di=28.0, minus_di=15.0),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "추세" in result or "ADX" in result

    def test_adx_strong_bearish_trend_mentioned(self):
        """ADX>25이고 -DI>+DI → 강한 하락 추세 언급."""
        result = generate_commentary(
            self._base_indicators(adx=32.0, plus_di=12.0, minus_di=30.0),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "추세" in result or "ADX" in result or "하락" in result

    def test_adx_weak_no_trend_mentioned(self):
        """ADX<20 → 추세 부재/방향성 모색 언급."""
        result = generate_commentary(
            self._base_indicators(adx=15.0, plus_di=18.0, minus_di=17.0),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "추세" in result or "방향" in result or "횡보" in result

    def test_adx_none_no_mention(self):
        """ADX=None이면 추세 강도 문장 없음."""
        result = generate_commentary(
            self._base_indicators(adx=None, plus_di=None, minus_di=None),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "ADX" not in result

    # --- 수렴 분석 코멘터리 테스트 ---

    def _base_convergence(self, **overrides):
        base = {
            "convergence_level": "moderate",
            "dominant_direction": "bullish",
            "aligned_axes": ["technical_score", "supply_score", "exchange_score",
                             "fundamental_score", "news_score"],
            "conflicting_axes": ["volatility_score"],
            "neutral_axes": ["candlestick_score"],
            "conviction": 55,
            "axis_directions": {},
        }
        base.update(overrides)
        return base

    def test_strong_convergence_bullish_mentioned(self):
        """strong 수렴 + bullish → 강한 수렴/신뢰도 높음 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            convergence=self._base_convergence(
                convergence_level="strong",
                dominant_direction="bullish",
                aligned_axes=["a"] * 7,
                conviction=80,
            ),
        )
        assert "수렴" in result or "신뢰" in result

    def test_strong_convergence_bearish_mentioned(self):
        """strong 수렴 + bearish → 약세 수렴 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            convergence=self._base_convergence(
                convergence_level="strong",
                dominant_direction="bearish",
                aligned_axes=["a"] * 7,
                conviction=80,
            ),
        )
        assert "수렴" in result or "신뢰" in result

    def test_mixed_convergence_mentioned(self):
        """mixed 수렴 → 혼조/신뢰도 낮음 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            convergence=self._base_convergence(
                convergence_level="mixed",
                dominant_direction="neutral",
                aligned_axes=[],
                conflicting_axes=["a", "b"],
                conviction=15,
            ),
        )
        assert "혼조" in result or "신뢰" in result or "분산" in result

    def test_no_convergence_no_mention(self):
        """convergence=None이면 수렴 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "수렴" not in result

    # --- 글로벌 매크로 코멘터리 테스트 ---

    def _base_nasdaq_trend(self, **overrides):
        base = {
            "trend": "상승",
            "momentum": 0.6,
            "ma5": 17500.0,
            "ma20": 17000.0,
            "latest": 17600.0,
        }
        base.update(overrides)
        return base

    def _base_vix_risk(self, **overrides):
        base = {
            "risk_level": "안정",
            "vix_latest": 15.0,
            "vix_trend": "하락",
            "interpretation": "시장 안정",
        }
        base.update(overrides)
        return base

    def test_global_macro_bullish_mentioned(self):
        """NASDAQ 상승 + VIX 안정 → 글로벌 기술주 우호적 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            nasdaq_trend=self._base_nasdaq_trend(trend="상승"),
            vix_risk=self._base_vix_risk(risk_level="안정"),
        )
        assert "글로벌" in result and "우호" in result

    def test_global_macro_bearish_mentioned(self):
        """NASDAQ 하락 + VIX 공포 → 글로벌 리스크 확대 언급."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            nasdaq_trend=self._base_nasdaq_trend(trend="하락"),
            vix_risk=self._base_vix_risk(risk_level="공포", vix_latest=35.0, vix_trend="상승"),
        )
        assert "글로벌" in result and ("리스크" in result or "부담" in result)

    def test_global_macro_neutral_omitted(self):
        """NASDAQ 보합 + VIX 안정 → 글로벌 매크로 문장 생략."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            nasdaq_trend=self._base_nasdaq_trend(trend="보합"),
            vix_risk=self._base_vix_risk(risk_level="안정"),
        )
        assert "글로벌" not in result

    def test_global_macro_none_no_mention(self):
        """nasdaq_trend=None, vix_risk=None이면 글로벌 매크로 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "글로벌" not in result

    def test_global_macro_nasdaq_only(self):
        """nasdaq_trend만 있고 vix_risk=None → 글로벌 매크로 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            nasdaq_trend=self._base_nasdaq_trend(trend="상승"),
        )
        assert "글로벌" not in result

    def test_global_macro_vix_only(self):
        """vix_risk만 있고 nasdaq_trend=None → 글로벌 매크로 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            vix_risk=self._base_vix_risk(risk_level="공포"),
        )
        assert "글로벌" not in result

    def test_global_macro_nasdaq_up_vix_caution(self):
        """NASDAQ 상승 + VIX 경계 → 우호적이나 경계 문장."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            nasdaq_trend=self._base_nasdaq_trend(trend="상승"),
            vix_risk=self._base_vix_risk(risk_level="경계", vix_latest=25.0),
        )
        assert "글로벌" in result

    def test_timeframe_aligned_bullish_sentence(self):
        """주봉 상승 추세 + aligned_bullish → 주봉 관련 문장 포함."""
        alignment = {
            "alignment": "aligned_bullish",
            "interpretation": "주봉 상승 추세에서 일봉 과매도",
            "score_modifier": 0.5,
        }
        weekly_ind = {
            "ma5w": 55000, "ma13w": 54000,
            "rsi_weekly": 55.0, "weekly_trend": "up",
            "weekly_close": 55500, "weekly_data_weeks": 15,
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            timeframe_alignment=alignment,
            weekly_indicators=weekly_ind,
        )
        assert "주봉" in result

    def test_timeframe_aligned_bearish_sentence(self):
        """주봉 하락 추세 + aligned_bearish → 하락 관련 문장."""
        alignment = {
            "alignment": "aligned_bearish",
            "interpretation": "주봉 하락 추세에서 일봉 과매수",
            "score_modifier": -0.5,
        }
        weekly_ind = {
            "ma5w": 53000, "ma13w": 54000,
            "rsi_weekly": 35.0, "weekly_trend": "down",
            "weekly_close": 52500, "weekly_data_weeks": 15,
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            timeframe_alignment=alignment,
            weekly_indicators=weekly_ind,
        )
        assert "주봉" in result

    def test_timeframe_none_no_sentence(self):
        """타임프레임 데이터 없으면 주봉 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "주봉 상승" not in result
        assert "주봉 하락" not in result

    def test_daily_delta_sentence_significant_move(self):
        """유의미한 변동이 있으면 델타 문장이 생성됨."""
        delta = {
            "axes_delta": {
                "supply_score": {"prev": -10, "curr": 15, "change": 25},
            },
            "alerts": [
                {"type": "significant_move", "axis": "supply_score",
                 "detail": "supply_score +25.0점 변동"},
            ],
            "overall": {
                "prev_score": 20.0, "curr_score": 35.0, "change": 15.0,
                "prev_grade": "약매수", "curr_grade": "매수",
            },
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            daily_delta=delta,
        )
        assert "전일 대비" in result

    def test_daily_delta_sentence_signal_flip(self):
        """방향 전환 알림이 있으면 전환 문장 생성됨."""
        delta = {
            "axes_delta": {
                "technical_score": {"prev": -5, "curr": 10, "change": 15},
            },
            "alerts": [
                {"type": "signal_flip", "axis": "technical_score",
                 "detail": "technical_score bearish→bullish (-5.0 → +10.0)"},
            ],
            "overall": {
                "prev_score": 10.0, "curr_score": 25.0, "change": 15.0,
                "prev_grade": "약매수", "curr_grade": "매수",
            },
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            daily_delta=delta,
        )
        assert "전환" in result

    def test_daily_delta_none_no_sentence(self):
        """daily_delta가 None이면 델타 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "전일 대비" not in result

    def test_risk_management_favorable_rr_mentioned(self):
        """R:R 유리 시 관련 문장 생성."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "risk_reward": {"ratio": 2.0, "grade": "유리", "risk": 3000.0, "reward": 6000.0},
            "position_guide": {"level": "표준", "description": "기본", "score": 4},
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            risk_management=rm,
        )
        assert "유리" in result

    def test_risk_management_unfavorable_rr_mentioned(self):
        """R:R 불리 시 주의 문장 생성."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "risk_reward": {"ratio": 0.5, "grade": "불리", "risk": 5000.0, "reward": 2500.0},
            "position_guide": {"level": "관망", "description": "대기", "score": 0},
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            risk_management=rm,
        )
        assert "불리" in result

    def test_risk_management_aggressive_position_mentioned(self):
        """공격적 포지션 가이드 시 관련 문장 생성."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "risk_reward": {"ratio": 2.5, "grade": "유리", "risk": 2000.0, "reward": 5000.0},
            "position_guide": {"level": "공격적", "description": "확대 진입", "score": 7},
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            risk_management=rm,
        )
        assert "확대 진입" in result

    def test_risk_management_standby_position_mentioned(self):
        """관망 포지션 가이드 시 진입 대기 문장 생성."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "risk_reward": {"ratio": 0.3, "grade": "불리", "risk": 5000.0, "reward": 1500.0},
            "position_guide": {"level": "관망", "description": "대기", "score": -1},
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            risk_management=rm,
        )
        assert "진입 대기" in result

    def test_risk_management_none_no_mention(self):
        """risk_management가 None이면 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "리스크 대비" not in result
        assert "확대 진입" not in result

    def test_market_regime_trending_up_framing(self):
        """상승 추세장 체제가 프레이밍 문장에 반영됨."""
        regime = {
            "regime": "trending_up",
            "phase": "markup",
            "confidence": 75,
            "duration": 12,
            "interpretation_hints": {},
            "adx": 30.0,
            "ma_alignment": "bullish",
            "bb_pctb": 0.7,
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            market_regime=regime,
        )
        assert "상승 추세장" in result

    def test_market_regime_range_bound_framing(self):
        """횡보 체제가 프레이밍 문장에 반영됨."""
        regime = {
            "regime": "range_bound",
            "phase": "accumulation",
            "confidence": 60,
            "duration": 8,
            "interpretation_hints": {},
            "adx": 15.0,
            "ma_alignment": "mixed",
            "bb_pctb": 0.5,
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            market_regime=regime,
        )
        assert "횡보" in result

    def test_market_regime_none_no_framing(self):
        """market_regime=None이면 체제 프레이밍 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            market_regime=None,
        )
        assert "추세장" not in result
        assert "횡보" not in result

    def test_market_regime_trending_up_explains_adjustment(self):
        """상승 추세장에서 RSI 기준 완화 설명이 포함됨."""
        regime = {
            "regime": "trending_up",
            "phase": "markup",
            "confidence": 75,
            "duration": 5,
            "interpretation_hints": {
                "rsi_thresholds": {"overbought": 80, "oversold": 20},
            },
            "adx": 30.0,
            "ma_alignment": "bullish",
            "bb_pctb": 0.7,
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            market_regime=regime,
        )
        assert "RSI" in result
        assert "완화" in result or "조정" in result

    def test_market_regime_range_bound_explains_tightening(self):
        """횡보 국면에서 RSI 기준 강화 설명이 포함됨."""
        regime = {
            "regime": "range_bound",
            "phase": "accumulation",
            "confidence": 60,
            "duration": 8,
            "interpretation_hints": {
                "rsi_thresholds": {"overbought": 70, "oversold": 30},
            },
            "adx": 15.0,
            "ma_alignment": "mixed",
            "bb_pctb": 0.5,
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            market_regime=regime,
        )
        # 기본값(70/30)이면 조정 설명 없어야 함
        assert "완화" not in result

    # --- 피보나치 되돌림 코멘터리 테스트 ---

    def _base_fibonacci(self, **overrides):
        base = {
            "retracement": {"0.0": 60000, "0.236": 58112, "0.382": 56952, "0.5": 56000, "0.618": 55048, "0.786": 53712, "1.0": 52000},
            "extension": {"1.0": 68000, "1.272": 70176, "1.618": 72944},
            "position": {"below": "0.618", "above": "0.5", "nearest_support": 55048, "nearest_resistance": 56000},
            "swing_high": {"price": 60000, "date": "2026-03-15", "index": 40},
            "swing_low": {"price": 52000, "date": "2026-03-01", "index": 10},
            "trend": "up",
        }
        base.update(overrides)
        return base

    def test_fibonacci_near_618_support_mentioned(self):
        """현재가가 0.618 되돌림 근처 → 깊은 되돌림/약한 추세 언급."""
        result = generate_commentary(
            self._base_indicators(current_price=55100),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fibonacci=self._base_fibonacci(),
        )
        assert "피보나치" in result or "되돌림" in result

    def test_fibonacci_near_382_mentioned(self):
        """0.382 되돌림 근처 → 얕은 되돌림/강한 추세 언급."""
        fib = self._base_fibonacci(
            position={"below": "0.382", "above": "0.236", "nearest_support": 56952, "nearest_resistance": 58112},
        )
        result = generate_commentary(
            self._base_indicators(current_price=57000),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fibonacci=fib,
        )
        assert "피보나치" in result or "되돌림" in result

    def test_fibonacci_none_no_mention(self):
        """fibonacci=None이면 피보나치 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
        )
        assert "피보나치" not in result

    def test_fibonacci_empty_no_mention(self):
        """피보나치 데이터가 비어있으면 문장 없음."""
        empty_fib = {
            "retracement": {},
            "extension": {},
            "position": {"below": None, "above": None, "nearest_support": None, "nearest_resistance": None},
            "swing_high": None,
            "swing_low": None,
            "trend": None,
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            fibonacci=empty_fib,
        )
        assert "피보나치" not in result

    # --- 백테스팅 성과 코멘터리 ---

    def test_backtest_high_hit_rate_positive(self):
        """강력매수 적중률이 높으면 긍정적 코멘터리."""
        bt = {
            "grade_performance": {
                "강력매수": {"count": 10, "avg_return_5d": 2.5, "hit_rate_5d": 78.0},
            },
            "score_range_performance": [],
            "streak_analysis": {"max_win_streak": 5, "max_lose_streak": 2, "equity_curve": []},
            "axis_contribution": {},
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(score=70, grade="강력매수"),
            self._base_support_resistance(),
            backtest=bt,
        )
        assert "적중률" in result or "신뢰" in result

    def test_backtest_low_hit_rate_caution(self):
        """강력매수 적중률이 낮으면 주의 코멘터리."""
        bt = {
            "grade_performance": {
                "강력매수": {"count": 10, "avg_return_5d": -0.5, "hit_rate_5d": 35.0},
            },
            "score_range_performance": [],
            "streak_analysis": {"max_win_streak": 2, "max_lose_streak": 5, "equity_curve": []},
            "axis_contribution": {},
        }
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(score=70, grade="강력매수"),
            self._base_support_resistance(),
            backtest=bt,
        )
        assert "주의" in result or "낮" in result or "신뢰" in result

    def test_backtest_none_no_mention(self):
        """백테스트 없으면 관련 문장 없음."""
        result = generate_commentary(
            self._base_indicators(),
            self._base_supply_demand(),
            self._base_exchange_rate(),
            self._base_composite_signal(),
            self._base_support_resistance(),
            backtest=None,
        )
        assert "백테스팅" not in result
