"""일일 분석 리포트 생성기 테스트."""

import pytest

from src.analysis.report import generate_daily_report, classify_ma_alignment, assess_volume, assess_market_temperature, classify_macd, classify_bb_position, classify_stochastic, _build_executive_summary, _build_fibonacci_section, _build_backtest_section


class TestClassifyMaAlignment:
    """이동평균선 배열 판단 테스트."""

    def test_golden_cross(self):
        """MA5 > MA20이고 price_vs_ma5 > 0 → 정배열 또는 골든크로스."""
        indicators = _base_indicators(ma5=55000, ma20=54000, ma60=53000)
        result = classify_ma_alignment(indicators)
        assert result == "정배열"

    def test_dead_cross(self):
        """MA5 < MA20 < MA60 → 역배열."""
        indicators = _base_indicators(ma5=53000, ma20=54000, ma60=55000)
        result = classify_ma_alignment(indicators)
        assert result == "역배열"

    def test_mixed(self):
        """정배열도 역배열도 아닌 경우."""
        indicators = _base_indicators(ma5=55000, ma20=53000, ma60=54000)
        result = classify_ma_alignment(indicators)
        assert result == "혼조"

    def test_insufficient_data(self):
        """MA 값이 None이면 판단 불가."""
        indicators = _base_indicators(ma5=55000, ma20=None, ma60=None)
        result = classify_ma_alignment(indicators)
        assert result == "데이터 부족"


class TestAssessVolume:
    """거래량 이상 감지 테스트."""

    def test_volume_surge(self):
        """거래량 비율 2.0 이상이면 급증."""
        assert assess_volume(2.5) == "급증"

    def test_volume_increase(self):
        """거래량 비율 1.5~2.0 → 증가."""
        assert assess_volume(1.7) == "증가"

    def test_volume_normal(self):
        """거래량 비율 0.7~1.5 → 보통."""
        assert assess_volume(1.0) == "보통"

    def test_volume_decrease(self):
        """거래량 비율 0.7 미만 → 감소."""
        assert assess_volume(0.5) == "감소"

    def test_volume_none(self):
        """거래량 데이터 없으면 None."""
        assert assess_volume(None) is None


class TestAssessMarketTemperature:
    """종합 시장 온도 판정 테스트."""

    def test_bullish(self):
        """상승 조건: 양봉 + 정배열 + 거래량 증가."""
        result = assess_market_temperature(
            change_1d_pct=2.0, ma_alignment="정배열", volume_status="증가"
        )
        assert result == "강세"

    def test_bearish(self):
        """하락 조건: 음봉 + 역배열."""
        result = assess_market_temperature(
            change_1d_pct=-2.0, ma_alignment="역배열", volume_status="보통"
        )
        assert result == "약세"

    def test_neutral(self):
        """중립 조건: 혼조 배열 + 소폭 변동."""
        result = assess_market_temperature(
            change_1d_pct=0.3, ma_alignment="혼조", volume_status="보통"
        )
        assert result == "중립"

    def test_data_insufficient(self):
        """데이터 부족 시 중립."""
        result = assess_market_temperature(
            change_1d_pct=None, ma_alignment="데이터 부족", volume_status=None
        )
        assert result == "중립"


class TestGenerateDailyReport:
    """HTML 리포트 생성 테스트."""

    def test_returns_string(self):
        indicators = _full_indicators()
        report = generate_daily_report(indicators)
        assert isinstance(report, str)

    def test_contains_price(self):
        indicators = _full_indicators(current_price=55000)
        report = generate_daily_report(indicators)
        assert "55,000" in report

    def test_contains_change(self):
        indicators = _full_indicators(change_1d_pct=2.5)
        report = generate_daily_report(indicators)
        assert "2.50%" in report or "+2.50%" in report

    def test_contains_ma_alignment(self):
        indicators = _full_indicators(ma5=55000, ma20=54000, ma60=53000)
        report = generate_daily_report(indicators)
        assert "정배열" in report

    def test_contains_temperature(self):
        indicators = _full_indicators()
        report = generate_daily_report(indicators)
        assert any(t in report for t in ["강세", "중립", "약세"])

    def test_contains_date(self):
        indicators = _full_indicators()
        report = generate_daily_report(indicators)
        assert "2026-03-21" in report

    def test_html_tags(self):
        """텔레그램 HTML parse_mode에 맞는 태그 사용."""
        indicators = _full_indicators()
        report = generate_daily_report(indicators)
        assert "<b>" in report

    def test_negative_change(self):
        indicators = _full_indicators(change_1d_pct=-1.5)
        report = generate_daily_report(indicators)
        assert "-1.50%" in report

    def test_backward_compatible_without_supply_demand(self):
        """supply_demand=None이면 수급 섹션 없이 기존 리포트 생성."""
        indicators = _full_indicators()
        report = generate_daily_report(indicators)
        assert "수급 동향" not in report

    def test_supply_demand_section_present(self):
        """supply_demand가 주어지면 수급 섹션이 포함된다."""
        indicators = _full_indicators()
        sd = _supply_demand_buy_dominant()
        report = generate_daily_report(indicators, supply_demand=sd)
        assert "수급 동향" in report

    def test_supply_demand_foreign_consecutive_buy(self):
        """외국인 연속 순매수 표시."""
        sd = _supply_demand_buy_dominant()
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "외국인" in report
        assert "연속" in report
        assert "순매수" in report

    def test_supply_demand_institution_consecutive_sell(self):
        """기관 연속 순매도 표시."""
        sd = _supply_demand_sell_dominant()
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "기관" in report
        assert "순매도" in report

    def test_supply_demand_cumulative_5d(self):
        """5일 누적 순매매 표시."""
        sd = _supply_demand_buy_dominant()
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "5일 누적" in report

    def test_supply_demand_ownership_trend_increasing(self):
        """보유비율 증가 추이 화살표."""
        sd = _supply_demand_buy_dominant()
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "↑" in report

    def test_supply_demand_ownership_trend_decreasing(self):
        """보유비율 감소 추이 화살표."""
        sd = _supply_demand_sell_dominant()
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "↓" in report

    def test_supply_demand_judgment_buy_dominant(self):
        """매수우위 판정 이모지."""
        sd = _supply_demand_buy_dominant()
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "매수우위" in report
        assert "🟢" in report

    def test_supply_demand_judgment_sell_dominant(self):
        """매도우위 판정 이모지."""
        sd = _supply_demand_sell_dominant()
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "매도우위" in report
        assert "🔴" in report

    def test_supply_demand_judgment_neutral(self):
        """중립 판정 이모지."""
        sd = _supply_demand_neutral()
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "중립" in report
        assert "🟡" in report

    def test_exchange_rate_section_absent_by_default(self):
        """exchange_rate=None이면 환율 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "USD/KRW" not in report

    def test_exchange_rate_section_present(self):
        """환율 분석이 주어지면 섹션이 포함된다."""
        er = _exchange_rate_sample()
        report = generate_daily_report(_full_indicators(), exchange_rate=er)
        assert "USD/KRW" in report

    def test_exchange_rate_trend(self):
        """환율 추세가 리포트에 표시된다."""
        er = _exchange_rate_sample()
        report = generate_daily_report(_full_indicators(), exchange_rate=er)
        assert "원화약세" in report

    def test_exchange_rate_correlation(self):
        """상관계수가 리포트에 표시된다."""
        er = _exchange_rate_sample()
        report = generate_daily_report(_full_indicators(), exchange_rate=er)
        assert "상관" in report

    def test_exchange_rate_no_correlation(self):
        """상관계수 None이면 상관 라인 없음."""
        er = _exchange_rate_sample()
        er["correlation_20d"] = None
        report = generate_daily_report(_full_indicators(), exchange_rate=er)
        assert "주가 상관" not in report

    def test_supply_demand_no_ownership_data(self):
        """보유비율 데이터 없을 때도 에러 없이 동작."""
        sd = _supply_demand_buy_dominant()
        sd["ownership_trend"] = None
        sd["ownership_change_pct"] = None
        report = generate_daily_report(_full_indicators(), supply_demand=sd)
        assert "수급 동향" in report

    def test_contains_rsi_value(self):
        """RSI 값이 리포트에 표시된다."""
        indicators = _full_indicators(rsi_14=65.3)
        report = generate_daily_report(indicators)
        assert "RSI" in report
        assert "65.3" in report

    def test_rsi_overbought_label(self):
        """RSI 70 이상이면 과매수 표시."""
        indicators = _full_indicators(rsi_14=75.0)
        report = generate_daily_report(indicators)
        assert "과매수" in report

    def test_rsi_oversold_label(self):
        """RSI 30 이하이면 과매도 표시."""
        indicators = _full_indicators(rsi_14=25.0)
        report = generate_daily_report(indicators)
        assert "과매도" in report

    def test_rsi_neutral_label(self):
        """RSI 30~70이면 중립 표시."""
        indicators = _full_indicators(rsi_14=50.0)
        report = generate_daily_report(indicators)
        assert "RSI" in report
        assert "중립" in report

    def test_rsi_none_no_crash(self):
        """RSI가 None이면 N/A로 표시, 에러 없음."""
        indicators = _full_indicators(rsi_14=None)
        report = generate_daily_report(indicators)
        assert isinstance(report, str)


class TestClassifyMACD:
    """MACD 크로스 판정 테스트."""

    def test_golden_cross(self):
        """MACD > Signal → 골든크로스."""
        assert classify_macd(100.0, 50.0, 50.0) == "골든크로스"

    def test_dead_cross(self):
        """MACD < Signal → 데드크로스."""
        assert classify_macd(-100.0, -50.0, -50.0) == "데드크로스"

    def test_data_insufficient(self):
        """데이터 부족 시 N/A."""
        assert classify_macd(None, None, None) == "N/A"

    def test_histogram_expanding_positive(self):
        """양의 히스토그램 → 골든크로스."""
        assert classify_macd(200.0, 100.0, 100.0) == "골든크로스"

    def test_histogram_expanding_negative(self):
        """음의 히스토그램 → 데드크로스."""
        assert classify_macd(-200.0, -100.0, -100.0) == "데드크로스"


class TestReportContainsMACD:
    """리포트에 MACD 섹션이 포함되는지 테스트."""

    def test_macd_section_present(self):
        """MACD 값이 있으면 섹션이 표시된다."""
        indicators = _full_indicators()
        indicators["macd"] = 150.0
        indicators["macd_signal"] = 100.0
        indicators["macd_histogram"] = 50.0
        report = generate_daily_report(indicators)
        assert "MACD" in report

    def test_macd_golden_cross_in_report(self):
        """골든크로스 상태가 리포트에 표시."""
        indicators = _full_indicators()
        indicators["macd"] = 150.0
        indicators["macd_signal"] = 100.0
        indicators["macd_histogram"] = 50.0
        report = generate_daily_report(indicators)
        assert "골든크로스" in report

    def test_macd_dead_cross_in_report(self):
        """데드크로스 상태가 리포트에 표시."""
        indicators = _full_indicators()
        indicators["macd"] = -150.0
        indicators["macd_signal"] = -100.0
        indicators["macd_histogram"] = -50.0
        report = generate_daily_report(indicators)
        assert "데드크로스" in report

    def test_macd_none_no_crash(self):
        """MACD가 None이면 MACD 섹션 없이 정상 동작."""
        indicators = _full_indicators()
        indicators["macd"] = None
        indicators["macd_signal"] = None
        indicators["macd_histogram"] = None
        report = generate_daily_report(indicators)
        assert isinstance(report, str)

    def test_macd_histogram_direction(self):
        """히스토그램 방향(확장/수축) 표시."""
        indicators = _full_indicators()
        indicators["macd"] = 150.0
        indicators["macd_signal"] = 100.0
        indicators["macd_histogram"] = 50.0
        report = generate_daily_report(indicators)
        # 양수 히스토그램 → 확장 or 관련 표현
        assert "확장" in report or "수축" in report


class TestBollingerBandsInReport:
    """볼린저 밴드가 리포트에 표시되는지 테스트."""

    def test_bb_section_present(self):
        """BB 값이 있으면 볼린저 밴드 섹션이 표시된다."""
        indicators = _full_indicators()
        indicators["bb_upper"] = 56000.0
        indicators["bb_lower"] = 52000.0
        indicators["bb_width"] = 0.075
        indicators["bb_pctb"] = 0.75
        report = generate_daily_report(indicators)
        assert "볼린저" in report or "BB" in report

    def test_bb_pctb_displayed(self):
        """%B 값이 리포트에 표시된다."""
        indicators = _full_indicators()
        indicators["bb_upper"] = 56000.0
        indicators["bb_lower"] = 52000.0
        indicators["bb_width"] = 0.075
        indicators["bb_pctb"] = 0.75
        report = generate_daily_report(indicators)
        assert "%B" in report

    def test_bb_overheated_label(self):
        """%B > 1.0이면 과열 관련 표현."""
        indicators = _full_indicators()
        indicators["bb_upper"] = 56000.0
        indicators["bb_lower"] = 52000.0
        indicators["bb_width"] = 0.075
        indicators["bb_pctb"] = 1.2
        report = generate_daily_report(indicators)
        assert "과열" in report or "상단 돌파" in report

    def test_bb_depressed_label(self):
        """%B < 0이면 침체 관련 표현."""
        indicators = _full_indicators()
        indicators["bb_upper"] = 56000.0
        indicators["bb_lower"] = 52000.0
        indicators["bb_width"] = 0.075
        indicators["bb_pctb"] = -0.1
        report = generate_daily_report(indicators)
        assert "침체" in report or "하단 이탈" in report

    def test_bb_none_no_crash(self):
        """BB가 None이면 에러 없이 동작."""
        indicators = _full_indicators()
        indicators["bb_upper"] = None
        indicators["bb_lower"] = None
        indicators["bb_width"] = None
        indicators["bb_pctb"] = None
        report = generate_daily_report(indicators)
        assert isinstance(report, str)


class TestMarketTemperatureWithBB:
    """볼린저 밴드가 시장 온도에 반영되는지 테스트."""

    def test_bb_overheated_adds_bearish(self):
        """%B > 1.0 (밴드 상단 돌파)은 약세 가산."""
        result = assess_market_temperature(
            change_1d_pct=1.5, ma_alignment="혼조", volume_status="보통",
            bb_pctb=1.2,
        )
        assert result != "강세"

    def test_bb_depressed_adds_bullish(self):
        """%B < 0 (밴드 하단 이탈)은 강세 가산."""
        result = assess_market_temperature(
            change_1d_pct=-0.5, ma_alignment="혼조", volume_status="보통",
            bb_pctb=-0.1,
        )
        assert result != "약세"

    def test_bb_normal_no_effect(self):
        """%B 0~1이면 온도 판정에 영향 없음."""
        without = assess_market_temperature(
            change_1d_pct=0.3, ma_alignment="혼조", volume_status="보통",
        )
        with_bb = assess_market_temperature(
            change_1d_pct=0.3, ma_alignment="혼조", volume_status="보통",
            bb_pctb=0.5,
        )
        assert without == with_bb

    def test_bb_none_same_as_without(self):
        """%B가 None이면 기존과 동일."""
        without = assess_market_temperature(
            change_1d_pct=2.0, ma_alignment="정배열", volume_status="증가",
        )
        with_none = assess_market_temperature(
            change_1d_pct=2.0, ma_alignment="정배열", volume_status="증가",
            bb_pctb=None,
        )
        assert without == with_none


class TestCompositeSignalInReport:
    """종합 투자 시그널이 리포트에 표시되는지 테스트."""

    def test_signal_section_absent_by_default(self):
        """composite_signal=None이면 종합 시그널 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "종합 판정" not in report

    def test_signal_section_present(self):
        """composite_signal이 주어지면 종합 시그널 섹션이 포함된다."""
        sig = _composite_signal_bullish()
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "종합 판정" in report

    def test_signal_grade_displayed(self):
        """5단계 판정이 리포트에 표시된다."""
        sig = _composite_signal_bullish()
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert sig["grade"] in report

    def test_signal_score_displayed(self):
        """종합 점수가 리포트에 표시된다."""
        sig = _composite_signal_bullish()
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "45" in report

    def test_signal_three_axes_displayed(self):
        """기술/수급/환율 3축 점수가 표시된다."""
        sig = _composite_signal_bullish()
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "기술" in report
        assert "수급" in report
        assert "환율" in report

    def test_signal_section_before_price(self):
        """종합 시그널 섹션이 현재가 섹션보다 앞에 위치한다."""
        sig = _composite_signal_bullish()
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        signal_pos = report.index("종합 판정")
        price_pos = report.index("현재가")
        assert signal_pos < price_pos

    def test_signal_strong_buy(self):
        """강력매수신호 판정 표시."""
        sig = _composite_signal_bullish()
        sig["score"] = 80.0
        sig["grade"] = "강력매수신호"
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "강력매수신호" in report

    def test_signal_strong_sell(self):
        """강력매도신호 판정 표시."""
        sig = {
            "score": -75.0, "grade": "강력매도신호",
            "technical_score": -80.0, "supply_score": -70.0, "exchange_score": -60.0,
            "weights": {"technical": 40, "supply": 40, "exchange": 20},
        }
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "강력매도신호" in report


class TestMarketTemperatureWithMACD:
    """MACD가 시장 온도 판정에 반영되는지 테스트."""

    def test_golden_cross_adds_bullish(self):
        """골든크로스는 강세 가산."""
        without = assess_market_temperature(
            change_1d_pct=0.5, ma_alignment="혼조", volume_status="보통",
        )
        with_macd = assess_market_temperature(
            change_1d_pct=0.5, ma_alignment="혼조", volume_status="보통",
            macd_cross="골든크로스",
        )
        # 골든크로스가 강세 방향으로 기여
        assert with_macd != "약세"

    def test_dead_cross_adds_bearish(self):
        """데드크로스는 약세 가산."""
        with_macd = assess_market_temperature(
            change_1d_pct=-0.5, ma_alignment="혼조", volume_status="보통",
            macd_cross="데드크로스",
        )
        assert with_macd != "강세"

    def test_macd_none_same_as_without(self):
        """MACD 없으면 기존과 동일."""
        without = assess_market_temperature(
            change_1d_pct=2.0, ma_alignment="정배열", volume_status="증가",
        )
        with_none = assess_market_temperature(
            change_1d_pct=2.0, ma_alignment="정배열", volume_status="증가",
            macd_cross="N/A",
        )
        assert without == with_none


class TestMarketTemperatureWithRSI:
    """RSI가 시장 온도 판정에 반영되는지 테스트."""

    def test_overbought_adds_bearish(self):
        """과매수(RSI 70↑)는 약세 가산 → 강세에서 중립으로."""
        result = assess_market_temperature(
            change_1d_pct=1.5, ma_alignment="혼조", volume_status="보통",
            rsi_14=80.0,
        )
        assert result != "강세"

    def test_oversold_adds_bullish(self):
        """과매도(RSI 30↓)는 강세 가산 → 약세에서 중립으로."""
        result = assess_market_temperature(
            change_1d_pct=-0.5, ma_alignment="혼조", volume_status="보통",
            rsi_14=20.0,
        )
        assert result != "약세"

    def test_neutral_rsi_no_effect(self):
        """RSI 30~70은 온도 판정에 영향 없음."""
        without_rsi = assess_market_temperature(
            change_1d_pct=0.3, ma_alignment="혼조", volume_status="보통",
        )
        with_rsi = assess_market_temperature(
            change_1d_pct=0.3, ma_alignment="혼조", volume_status="보통",
            rsi_14=50.0,
        )
        assert without_rsi == with_rsi

    def test_rsi_none_same_as_without(self):
        """RSI가 None이면 기존과 동일하게 동작."""
        without = assess_market_temperature(
            change_1d_pct=2.0, ma_alignment="정배열", volume_status="증가",
        )
        with_none = assess_market_temperature(
            change_1d_pct=2.0, ma_alignment="정배열", volume_status="증가",
            rsi_14=None,
        )
        assert without == with_none


# --- helpers ---

def _base_indicators(
    ma5=55000, ma20=54000, ma60=53000,
    current_price=55000,
) -> dict:
    return {
        "current_date": "2026-03-21",
        "current_price": current_price,
        "ma5": ma5,
        "ma20": ma20,
        "ma60": ma60,
        "price_vs_ma5_pct": None,
        "price_vs_ma20_pct": None,
        "price_vs_ma60_pct": None,
        "change_1d_pct": 1.0,
        "change_5d_pct": 3.0,
        "change_20d_pct": 5.0,
        "volume_ratio_5d": 1.0,
        "rsi_14": 50.0,
    }


def _full_indicators(
    current_price=55000,
    change_1d_pct=1.0,
    ma5=55000, ma20=54000, ma60=53000,
    rsi_14=50.0,
) -> dict:
    return {
        "current_date": "2026-03-21",
        "current_price": current_price,
        "ma5": ma5,
        "ma20": ma20,
        "ma60": ma60,
        "price_vs_ma5_pct": 1.85 if ma5 else None,
        "price_vs_ma20_pct": 1.85 if ma20 else None,
        "price_vs_ma60_pct": 3.77 if ma60 else None,
        "change_1d_pct": change_1d_pct,
        "change_5d_pct": 3.0,
        "change_20d_pct": 5.0,
        "volume_ratio_5d": 1.2,
        "rsi_14": rsi_14,
        "macd": None,
        "macd_signal": None,
        "macd_histogram": None,
        "bb_upper": None,
        "bb_lower": None,
        "bb_width": None,
        "bb_pctb": None,
    }


def _exchange_rate_sample() -> dict:
    return {
        "current_date": "2026-03-21",
        "current_rate": 1380.5,
        "change_1d_pct": 0.35,
        "change_5d_pct": 1.2,
        "change_20d_pct": 2.5,
        "ma5": 1375.0,
        "ma20": 1360.0,
        "trend": "원화약세",
        "correlation_20d": -0.65,
    }


def _supply_demand_buy_dominant() -> dict:
    return {
        "foreign_consecutive_net_buy": 5,
        "foreign_consecutive_net_sell": 0,
        "institution_consecutive_net_buy": 3,
        "institution_consecutive_net_sell": 0,
        "foreign_cumulative_5d": 1500000,
        "foreign_cumulative_20d": 3000000,
        "institution_cumulative_5d": 800000,
        "institution_cumulative_20d": 1200000,
        "ownership_trend": "increasing",
        "ownership_change_pct": 0.3,
        "overall_judgment": "buy_dominant",
    }


def _supply_demand_sell_dominant() -> dict:
    return {
        "foreign_consecutive_net_buy": 0,
        "foreign_consecutive_net_sell": 4,
        "institution_consecutive_net_buy": 0,
        "institution_consecutive_net_sell": 6,
        "foreign_cumulative_5d": -2000000,
        "foreign_cumulative_20d": -5000000,
        "institution_cumulative_5d": -1000000,
        "institution_cumulative_20d": -3000000,
        "ownership_trend": "decreasing",
        "ownership_change_pct": -0.5,
        "overall_judgment": "sell_dominant",
    }


def _composite_signal_bullish() -> dict:
    return {
        "score": 45.0,
        "grade": "매수우세",
        "technical_score": 50.0,
        "supply_score": 60.0,
        "exchange_score": 10.0,
        "weights": {"technical": 40, "supply": 40, "exchange": 20},
    }


def _support_resistance_sample() -> dict:
    return {
        "pivot": {"pp": 55000.0, "s1": 54000.0, "s2": 53000.0, "r1": 56000.0, "r2": 57000.0},
        "swing_levels": [],
        "ma_levels": {"ma20": 54500.0, "ma60": 53500.0},
        "nearest_support": 54500.0,
        "nearest_resistance": 56000.0,
    }


def _support_resistance_none_levels() -> dict:
    return {
        "pivot": {"pp": None, "s1": None, "s2": None, "r1": None, "r2": None},
        "swing_levels": [],
        "ma_levels": {"ma20": None, "ma60": None},
        "nearest_support": None,
        "nearest_resistance": None,
    }


class TestSupportResistanceInReport:
    """지지/저항선이 리포트에 표시되는지 테스트."""

    def test_sr_section_absent_by_default(self):
        """support_resistance=None이면 지지/저항 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "지지/저항" not in report

    def test_sr_section_present(self):
        """support_resistance가 주어지면 섹션이 포함된다."""
        sr = _support_resistance_sample()
        report = generate_daily_report(_full_indicators(), support_resistance=sr)
        assert "지지/저항" in report

    def test_sr_pivot_points_displayed(self):
        """피봇 포인트(PP/S1/S2/R1/R2)가 표시된다."""
        sr = _support_resistance_sample()
        report = generate_daily_report(_full_indicators(), support_resistance=sr)
        assert "PP" in report
        assert "S1" in report
        assert "R1" in report

    def test_sr_nearest_support_displayed(self):
        """가장 가까운 지지선이 표시된다."""
        sr = _support_resistance_sample()
        report = generate_daily_report(_full_indicators(), support_resistance=sr)
        assert "54,500" in report

    def test_sr_nearest_resistance_displayed(self):
        """가장 가까운 저항선이 표시된다."""
        sr = _support_resistance_sample()
        report = generate_daily_report(_full_indicators(), support_resistance=sr)
        assert "56,000" in report

    def test_sr_distance_pct_displayed(self):
        """현재가 대비 거리(%)가 표시된다."""
        sr = _support_resistance_sample()
        report = generate_daily_report(
            _full_indicators(current_price=55000), support_resistance=sr,
        )
        assert "%" in report

    def test_sr_none_levels_no_crash(self):
        """피봇 등이 None이어도 에러 없이 동작."""
        sr = _support_resistance_none_levels()
        report = generate_daily_report(_full_indicators(), support_resistance=sr)
        assert isinstance(report, str)

    def test_sr_backward_compatible(self):
        """support_resistance 파라미터 없이도 기존 리포트 정상 생성."""
        report = generate_daily_report(_full_indicators())
        assert "삼성전자" in report


class TestAccuracyInReport:
    """시그널 정확도가 리포트에 표시되는지 테스트."""

    def test_accuracy_section_absent_by_default(self):
        """accuracy_summary=None이면 정확도 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "시그널 정확도" not in report

    def test_accuracy_section_present(self):
        """accuracy_summary가 충분한 데이터와 함께 주어지면 섹션이 포함된다."""
        acc = _accuracy_summary_sufficient()
        report = generate_daily_report(_full_indicators(), accuracy_summary=acc)
        assert "시그널 정확도" in report

    def test_accuracy_hit_rate_displayed(self):
        """적중률이 리포트에 표시된다."""
        acc = _accuracy_summary_sufficient()
        report = generate_daily_report(_full_indicators(), accuracy_summary=acc)
        assert "적중률" in report

    def test_accuracy_avg_return_displayed(self):
        """평균 수익률이 리포트에 표시된다."""
        acc = _accuracy_summary_sufficient()
        report = generate_daily_report(_full_indicators(), accuracy_summary=acc)
        assert "평균 수익률" in report

    def test_accuracy_insufficient_data(self):
        """evaluated_signals < 5이면 '데이터 축적 중' 메시지 표시."""
        acc = _accuracy_summary_insufficient()
        report = generate_daily_report(_full_indicators(), accuracy_summary=acc)
        assert "데이터 축적 중" in report

    def test_accuracy_after_support_resistance(self):
        """정확도 섹션이 지지/저항선 섹션 뒤에 위치한다."""
        sr = _support_resistance_sample()
        acc = _accuracy_summary_sufficient()
        report = generate_daily_report(
            _full_indicators(), support_resistance=sr, accuracy_summary=acc,
        )
        sr_pos = report.index("지지/저항")
        acc_pos = report.index("시그널 정확도")
        assert acc_pos > sr_pos

    def test_accuracy_total_signals_displayed(self):
        """총 평가 시그널 수가 표시된다."""
        acc = _accuracy_summary_sufficient()
        report = generate_daily_report(_full_indicators(), accuracy_summary=acc)
        assert "20" in report  # total_signals = 20

    def test_accuracy_per_axis_displayed(self):
        """per_axis 데이터가 있으면 축별 적중률이 출력에 포함된다."""
        acc = _accuracy_summary_sufficient()
        report = generate_daily_report(_full_indicators(), accuracy_summary=acc)
        assert "축별 5일 적중률" in report
        assert "기술적" in report  # technical_score → 기술적
        assert "수급" in report    # supply_score → 수급
        assert "환율" in report    # exchange_score → 환율

    def test_accuracy_per_axis_level_labels(self):
        """적중률 수준별 라벨이 올바르게 표시된다."""
        acc = _accuracy_summary_sufficient()
        report = generate_daily_report(_full_indicators(), accuracy_summary=acc)
        # technical_score: 75% → 🟢높음
        assert "🟢높음" in report
        # supply_score: 62% → 🟡보통
        assert "🟡보통" in report
        # exchange_score: 45% → 🔴낮음
        assert "🔴낮음" in report

    def test_accuracy_adapted_weights_shown(self):
        """composite_signal에 adapted_weights=True이면 표시된다."""
        acc = _accuracy_summary_sufficient()
        cs = _composite_signal_bullish()
        cs["adapted_weights"] = True
        report = generate_daily_report(
            _full_indicators(), accuracy_summary=acc, composite_signal=cs,
        )
        assert "적응형 가중치 활성" in report

    def test_accuracy_no_adapted_weights_label(self):
        """adapted_weights가 없으면 적응형 가중치 라벨이 없다."""
        acc = _accuracy_summary_sufficient()
        cs = _composite_signal_bullish()
        report = generate_daily_report(
            _full_indicators(), accuracy_summary=acc, composite_signal=cs,
        )
        assert "적응형 가중치 활성" not in report

    def test_accuracy_per_axis_skips_insufficient(self):
        """evaluated_5d < 5인 축은 표시되지 않는다."""
        acc = _accuracy_summary_sufficient()
        report = generate_daily_report(_full_indicators(), accuracy_summary=acc)
        # consensus_score has evaluated_5d=2, should not appear
        assert "컨센서스" not in report
        # fundamentals_score has evaluated_5d=0, should not appear
        assert "펀더멘털" not in report


class TestClassifyStochastic:
    """스토캐스틱 상태 판단 테스트."""

    def test_overbought(self):
        """%K >= 80 → 과매수."""
        assert classify_stochastic(85.0, 82.0) == "과매수"

    def test_oversold(self):
        """%K <= 20 → 과매도."""
        assert classify_stochastic(15.0, 18.0) == "과매도"

    def test_golden_cross(self):
        """%K > %D이고 20~80 → 골든크로스."""
        assert classify_stochastic(55.0, 50.0) == "골든크로스"

    def test_dead_cross(self):
        """%K < %D이고 20~80 → 데드크로스."""
        assert classify_stochastic(45.0, 50.0) == "데드크로스"

    def test_none_k(self):
        """%K가 None → N/A."""
        assert classify_stochastic(None, None) == "N/A"

    def test_none_d_only_k(self):
        """%D가 None이면 과매수/과매도만 판단."""
        assert classify_stochastic(85.0, None) == "과매수"
        assert classify_stochastic(15.0, None) == "과매도"
        assert classify_stochastic(50.0, None) == "N/A"


class TestStochasticInReport:
    """스토캐스틱이 리포트에 표시되는지 테스트."""

    def test_stochastic_section_present(self):
        """stoch_k/stoch_d가 있으면 스토캐스틱 섹션 포함."""
        ind = _full_indicators()
        ind["stoch_k"] = 45.0
        ind["stoch_d"] = 40.0
        report = generate_daily_report(ind)
        assert "Stoch" in report or "스토캐스틱" in report

    def test_stochastic_overbought_emoji(self):
        """과매수 시 이모지 표시."""
        ind = _full_indicators()
        ind["stoch_k"] = 85.0
        ind["stoch_d"] = 82.0
        report = generate_daily_report(ind)
        assert "과매수" in report

    def test_stochastic_oversold_emoji(self):
        """과매도 시 이모지 표시."""
        ind = _full_indicators()
        ind["stoch_k"] = 15.0
        ind["stoch_d"] = 18.0
        report = generate_daily_report(ind)
        assert "과매도" in report

    def test_stochastic_absent_when_none(self):
        """stoch_k가 None이면 섹션 없음."""
        ind = _full_indicators()
        ind["stoch_k"] = None
        ind["stoch_d"] = None
        report = generate_daily_report(ind)
        assert "Stoch(14,3)" not in report


class TestOBVDivergenceInReport:
    """OBV 다이버전스 리포트 표시 테스트."""

    def test_bearish_divergence_warning_in_report(self):
        """bearish divergence → 가격-거래량 괴리 경고 표시."""
        ind = _full_indicators()
        ind["obv_divergence"] = "bearish"
        ind["obv"] = 1000000
        ind["obv_ma20"] = 900000
        report = generate_daily_report(ind)
        assert "가격-거래량 괴리" in report or "OBV" in report

    def test_bullish_divergence_in_report(self):
        """bullish divergence → 거래량 선행 반등 표시."""
        ind = _full_indicators()
        ind["obv_divergence"] = "bullish"
        ind["obv"] = 1000000
        ind["obv_ma20"] = 900000
        report = generate_daily_report(ind)
        assert "거래량" in report or "OBV" in report

    def test_no_divergence_no_obv_section(self):
        """divergence 없으면 OBV 경고 섹션 없음."""
        ind = _full_indicators()
        ind["obv_divergence"] = None
        report = generate_daily_report(ind)
        assert "가격-거래량 괴리" not in report


def _accuracy_summary_sufficient() -> dict:
    return {
        "total_signals": 20,
        "hit_rate_1d": 65.0,
        "hit_rate_3d": 60.0,
        "hit_rate_5d": 55.0,
        "avg_return_1d": 0.35,
        "avg_return_3d": 0.80,
        "avg_return_5d": 1.20,
        "evaluated_signals_1d": 18,
        "evaluated_signals_3d": 15,
        "evaluated_signals_5d": 10,
        "per_axis": {
            "technical_score": {"hit_rate_5d": 75.0, "evaluated_5d": 8},
            "supply_score": {"hit_rate_5d": 62.0, "evaluated_5d": 8},
            "exchange_score": {"hit_rate_5d": 45.0, "evaluated_5d": 6},
            "fundamentals_score": {"hit_rate_5d": None, "evaluated_5d": 0},
            "news_score": {"hit_rate_5d": 55.0, "evaluated_5d": 5},
            "consensus_score": {"hit_rate_5d": None, "evaluated_5d": 2},
            "semiconductor_score": {"hit_rate_5d": 70.0, "evaluated_5d": 5},
            "volatility_score": {"hit_rate_5d": 50.0, "evaluated_5d": 5},
            "candlestick_score": {"hit_rate_5d": 40.0, "evaluated_5d": 5},
            "global_macro_score": {"hit_rate_5d": 80.0, "evaluated_5d": 5},
        },
    }


def _accuracy_summary_insufficient() -> dict:
    return {
        "total_signals": 3,
        "hit_rate_1d": None,
        "hit_rate_3d": None,
        "hit_rate_5d": None,
        "avg_return_1d": None,
        "avg_return_3d": None,
        "avg_return_5d": None,
        "evaluated_signals_1d": 3,
        "evaluated_signals_3d": 2,
        "evaluated_signals_5d": 0,
    }


def _supply_demand_neutral() -> dict:
    return {
        "foreign_consecutive_net_buy": 1,
        "foreign_consecutive_net_sell": 0,
        "institution_consecutive_net_buy": 0,
        "institution_consecutive_net_sell": 1,
        "foreign_cumulative_5d": 200000,
        "foreign_cumulative_20d": -100000,
        "institution_cumulative_5d": -50000,
        "institution_cumulative_20d": 300000,
        "ownership_trend": "sideways",
        "ownership_change_pct": 0.02,
        "overall_judgment": "neutral",
    }


class TestTrendReversalInReport:
    """추세 전환 감지 섹션이 리포트에 표시되는지 테스트."""

    def _reversal_strong_bullish(self) -> dict:
        return {
            "direction": "bullish",
            "convergence": "strong",
            "score": 85.0,
            "active_categories": 4,
            "category_signals": {
                "momentum": {"direction": "bullish", "strength": 90.0},
                "trend": {"direction": "bullish", "strength": 80.0},
                "volatility": {"direction": "bullish", "strength": 70.0},
                "volume": {"direction": "bullish", "strength": 60.0},
                "structure": {"direction": "neutral", "strength": 0.0},
            },
            "summary": "강한 강세 반전 신호 감지",
        }

    def _reversal_none_convergence(self) -> dict:
        return {
            "direction": "neutral",
            "convergence": "none",
            "score": 0.0,
            "active_categories": 0,
            "category_signals": {
                "momentum": {"direction": "neutral", "strength": 0.0},
                "trend": {"direction": "neutral", "strength": 0.0},
                "volatility": {"direction": "neutral", "strength": 0.0},
                "volume": {"direction": "neutral", "strength": 0.0},
                "structure": {"direction": "neutral", "strength": 0.0},
            },
            "summary": "현재 뚜렷한 추세 전환 신호가 감지되지 않습니다.",
        }

    def test_strong_reversal_section_present(self):
        """strong 컨버전스 시 추세 전환 섹션이 포함된다."""
        report = generate_daily_report(
            _full_indicators(),
            trend_reversal=self._reversal_strong_bullish(),
        )
        assert "추세 전환" in report
        assert "강세" in report
        assert "컨버전스" in report

    def test_none_convergence_no_section(self):
        """none 컨버전스 시 추세 전환 섹션이 생략된다."""
        report = generate_daily_report(
            _full_indicators(),
            trend_reversal=self._reversal_none_convergence(),
        )
        assert "추세 전환" not in report

    def test_no_reversal_param_backward_compat(self):
        """trend_reversal 미전달 시 기존 리포트와 동일하게 동작."""
        report = generate_daily_report(_full_indicators())
        assert "추세 전환" not in report

    def test_active_categories_shown(self):
        """활성 카테고리 정보가 표시된다."""
        report = generate_daily_report(
            _full_indicators(),
            trend_reversal=self._reversal_strong_bullish(),
        )
        assert "모멘텀" in report or "활성" in report

    def test_moderate_bearish_reversal(self):
        """moderate bearish 컨버전스도 섹션이 표시된다."""
        reversal = {
            "direction": "bearish",
            "convergence": "moderate",
            "score": 55.0,
            "active_categories": 3,
            "category_signals": {
                "momentum": {"direction": "bearish", "strength": 70.0},
                "trend": {"direction": "bearish", "strength": 60.0},
                "volatility": {"direction": "bearish", "strength": 50.0},
                "volume": {"direction": "neutral", "strength": 0.0},
                "structure": {"direction": "neutral", "strength": 0.0},
            },
            "summary": "중간 약세 반전 신호 감지",
        }
        report = generate_daily_report(
            _full_indicators(), trend_reversal=reversal,
        )
        assert "추세 전환" in report
        assert "약세" in report


class TestFundamentalsSection:
    """펀더멘털 분석 섹션 테스트."""

    def _fund(self, **overrides):
        base = {
            "per": 12.5, "eps": 4800, "estimated_per": 10.0, "estimated_eps": 6000,
            "pbr": 1.2, "bps": 45000, "dividend_yield": 2.0,
            "per_valuation": "적정", "pbr_valuation": "적정",
            "earnings_outlook": "개선", "dividend_attractiveness": "보통",
        }
        base.update(overrides)
        return base

    def test_no_fundamentals_no_section(self):
        """fundamentals=None이면 펀더멘털 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "펀더멘털" not in report

    def test_fundamentals_section_present(self):
        """fundamentals가 있으면 섹션이 포함됨."""
        report = generate_daily_report(_full_indicators(), fundamentals=self._fund())
        assert "펀더멘털 분석" in report

    def test_per_displayed(self):
        """PER 값이 리포트에 표시됨."""
        report = generate_daily_report(_full_indicators(), fundamentals=self._fund(per=12.5))
        assert "PER" in report
        assert "12.5" in report

    def test_pbr_displayed(self):
        """PBR 값이 리포트에 표시됨."""
        report = generate_daily_report(_full_indicators(), fundamentals=self._fund(pbr=1.20))
        assert "PBR" in report
        assert "1.20" in report

    def test_dividend_yield_displayed(self):
        """배당수익률이 리포트에 표시됨."""
        report = generate_daily_report(_full_indicators(), fundamentals=self._fund(dividend_yield=2.5))
        assert "배당수익률" in report
        assert "2.50%" in report

    def test_earnings_outlook_displayed(self):
        """실적 전망이 리포트에 표시됨."""
        report = generate_daily_report(_full_indicators(), fundamentals=self._fund(earnings_outlook="개선"))
        assert "실적 전망" in report
        assert "개선" in report

    def test_undervalued_emoji(self):
        """저평가 시 녹색 이모지."""
        report = generate_daily_report(_full_indicators(), fundamentals=self._fund(per_valuation="저평가"))
        assert "🟢" in report
        assert "저평가" in report

    def test_overvalued_emoji(self):
        """고평가 시 빨간 이모지."""
        report = generate_daily_report(_full_indicators(), fundamentals=self._fund(per_valuation="고평가"))
        assert "🔴" in report
        assert "고평가" in report

    def test_composite_signal_shows_fundamentals_score(self):
        """종합 시그널에 펀더멘털 점수가 표시됨."""
        sig = {
            "score": 30.0, "grade": "매수우세",
            "technical_score": 40.0, "supply_score": 30.0, "exchange_score": 10.0,
            "fundamentals_score": 25.0,
            "weights": {"technical": 30, "supply": 30, "exchange": 15,
                        "relative_strength": 10, "fundamentals": 15},
        }
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "펀더멘털" in report
        assert "15%" in report


class TestNewsSentimentSection:
    """뉴스 감정 분석 섹션 테스트."""

    def _news(self, **overrides):
        base = {
            "label": "bullish",
            "score": 3,
            "positive": 5,
            "negative": 2,
            "neutral": 3,
            "count": 10,
        }
        base.update(overrides)
        return base

    def _headlines(self):
        return [
            {"title": "삼성전자 실적 호실적 기대", "source": "한경", "date": "2026-03-29", "sentiment": "positive"},
            {"title": "반도체 업황 회복 신호", "source": "매일경제", "date": "2026-03-29", "sentiment": "positive"},
            {"title": "삼성전자 주가 하락 우려", "source": "조선일보", "date": "2026-03-29", "sentiment": "negative"},
        ]

    def test_no_news_no_section(self):
        """news_sentiment=None이면 뉴스 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "뉴스 심리" not in report

    def test_news_section_present(self):
        """news_sentiment가 있으면 뉴스 심리 섹션이 포함."""
        report = generate_daily_report(
            _full_indicators(),
            news_sentiment=self._news(),
            news_headlines=self._headlines(),
        )
        assert "뉴스 심리" in report

    def test_news_sentiment_counts(self):
        """긍정/부정/중립 건수가 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            news_sentiment=self._news(positive=5, negative=2, neutral=3),
        )
        assert "긍정 5" in report
        assert "부정 2" in report

    def test_news_headlines_shown(self):
        """주요 헤드라인이 최대 3개 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            news_sentiment=self._news(),
            news_headlines=self._headlines(),
        )
        assert "실적" in report or "반도체" in report

    def test_composite_signal_shows_news_score(self):
        """종합 시그널에 뉴스 점수가 표시됨."""
        sig = {
            "score": 30.0, "grade": "매수우세",
            "technical_score": 40.0, "supply_score": 30.0, "exchange_score": 10.0,
            "news_score": 20.0,
            "weights": {"technical": 25, "supply": 25, "exchange": 15,
                        "relative_strength": 10, "fundamentals": 15, "news": 10},
        }
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "뉴스" in report
        assert "10%" in report


class TestConsensusInReport:
    """증권사 컨센서스 섹션이 리포트에 포함되는지 테스트."""

    def _cons(self, **overrides):
        base = {
            "target_price": 252720,
            "current_price": 180000,
            "divergence_pct": 40.4,
            "valuation": "저평가",
            "recommendation": 4.2,
            "recommendation_label": "매수유지",
            "researches": [
                {"title": "삼성전자 목표가 상향", "broker": "삼성증권", "date": "2026-03-28"},
                {"title": "반도체 수요 회복 기대", "broker": "미래에셋", "date": "2026-03-27"},
            ],
            "research_tone": "긍정",
        }
        base.update(overrides)
        return base

    def test_no_consensus_no_section(self):
        """consensus=None이면 컨센서스 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "증권사 컨센서스" not in report

    def test_consensus_section_present(self):
        """consensus가 있으면 섹션이 포함."""
        report = generate_daily_report(
            _full_indicators(), consensus=self._cons(),
        )
        assert "증권사 컨센서스" in report

    def test_target_price_shown(self):
        """목표가가 표시됨."""
        report = generate_daily_report(
            _full_indicators(), consensus=self._cons(),
        )
        assert "252,720" in report

    def test_divergence_shown(self):
        """괴리율이 표시됨."""
        report = generate_daily_report(
            _full_indicators(), consensus=self._cons(),
        )
        assert "40.4%" in report or "+40.4%" in report

    def test_recommendation_shown(self):
        """투자의견이 표시됨."""
        report = generate_daily_report(
            _full_indicators(), consensus=self._cons(),
        )
        assert "매수유지" in report

    def test_researches_shown(self):
        """최근 리포트 제목이 최대 3건 표시됨."""
        report = generate_daily_report(
            _full_indicators(), consensus=self._cons(),
        )
        assert "목표가 상향" in report or "수요 회복" in report

    def test_composite_signal_shows_consensus_score(self):
        """종합 시그널에 컨센서스 점수가 표시됨."""
        sig = {
            "score": 30.0, "grade": "매수우세",
            "technical_score": 40.0, "supply_score": 30.0, "exchange_score": 10.0,
            "consensus_score": 25.0,
            "weights": {"technical": 36, "supply": 36, "exchange": 18, "consensus": 10},
        }
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "컨센서스" in report


# ── 주간 추이 요약 섹션 테스트 ───────────────────────────────────


def _weekly_summary_sample() -> dict:
    return {
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


class TestWeeklySummarySection:
    """주간 추이 요약 섹션 리포트 통합 테스트."""

    def test_weekly_summary_present(self):
        """weekly_summary가 주어지면 주간 추이 섹션이 포함된다."""
        report = generate_daily_report(
            _full_indicators(), weekly_summary=_weekly_summary_sample(),
        )
        assert "주간 추이" in report

    def test_weekly_summary_contains_dates(self):
        """주간 추이에 기간이 표시된다."""
        ws = _weekly_summary_sample()
        report = generate_daily_report(_full_indicators(), weekly_summary=ws)
        assert ws["start_date"] in report
        assert ws["end_date"] in report

    def test_weekly_summary_contains_change_pct(self):
        """주간 등락률이 표시된다."""
        report = generate_daily_report(
            _full_indicators(), weekly_summary=_weekly_summary_sample(),
        )
        assert "3.7" in report or "+3.7" in report

    def test_weekly_summary_contains_judgment(self):
        """주간 판정이 표시된다."""
        report = generate_daily_report(
            _full_indicators(), weekly_summary=_weekly_summary_sample(),
        )
        assert "상승 지속" in report

    def test_weekly_summary_contains_supply(self):
        """주간 수급 누적이 표시된다."""
        report = generate_daily_report(
            _full_indicators(), weekly_summary=_weekly_summary_sample(),
        )
        assert "외국인" in report or "기관" in report

    def test_weekly_summary_none_no_section(self):
        """weekly_summary=None이면 주간 추이 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "주간 추이" not in report

    def test_weekly_summary_signal_change(self):
        """시그널 변화가 표시된다."""
        report = generate_daily_report(
            _full_indicators(), weekly_summary=_weekly_summary_sample(),
        )
        assert "시그널" in report


# ── 반도체 업황 섹션 테스트 ───────────────────────────────────


def _rel_perf_sample(**overrides) -> dict:
    base = {
        "samsung_return_5d": 3.0,
        "hynix_return_5d": 1.5,
        "alpha_5d": 1.5,
        "samsung_return_20d": 5.0,
        "hynix_return_20d": 2.0,
        "alpha_20d": 3.0,
        "rs_current": 0.35,
        "rs_ma20": 0.34,
        "relative_trend": "outperform",
    }
    base.update(overrides)
    return base


def _sox_trend_sample(**overrides) -> dict:
    base = {
        "trend": "상승",
        "change_pct": 5.2,
        "ma20": 4800.0,
        "current": 5050.0,
        "strength": 0.5,
    }
    base.update(overrides)
    return base


class TestSemiconductorInReport:
    """반도체 업황 섹션이 리포트에 포함되는지 테스트."""

    def test_no_semiconductor_no_section(self):
        """반도체 데이터 없으면 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "반도체 업황" not in report

    def test_semiconductor_section_present(self):
        """반도체 데이터가 있으면 섹션이 포함."""
        report = generate_daily_report(
            _full_indicators(),
            rel_perf=_rel_perf_sample(),
            sox_trend=_sox_trend_sample(),
            semiconductor_momentum=45,
        )
        assert "반도체 업황" in report

    def test_semiconductor_shows_alpha(self):
        """alpha_5d, alpha_20d가 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            rel_perf=_rel_perf_sample(alpha_5d=1.5, alpha_20d=3.0),
            sox_trend=_sox_trend_sample(),
            semiconductor_momentum=45,
        )
        assert "1.5" in report or "+1.5" in report
        assert "3.0" in report or "+3.0" in report

    def test_semiconductor_shows_sox(self):
        """SOX 지수 정보가 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            rel_perf=_rel_perf_sample(),
            sox_trend=_sox_trend_sample(trend="상승", change_pct=5.2),
            semiconductor_momentum=45,
        )
        assert "SOX" in report
        assert "상승" in report

    def test_semiconductor_shows_momentum(self):
        """모멘텀 스코어가 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            rel_perf=_rel_perf_sample(),
            sox_trend=_sox_trend_sample(),
            semiconductor_momentum=45,
        )
        assert "45" in report or "모멘텀" in report

    def test_semiconductor_none_rel_perf(self):
        """rel_perf=None이면 반도체 섹션 없음."""
        report = generate_daily_report(
            _full_indicators(),
            rel_perf=None,
            sox_trend=_sox_trend_sample(),
            semiconductor_momentum=45,
        )
        assert "반도체 업황" not in report

    def test_semiconductor_none_sox(self):
        """sox_trend=None이면 반도체 섹션 없음."""
        report = generate_daily_report(
            _full_indicators(),
            rel_perf=_rel_perf_sample(),
            sox_trend=None,
            semiconductor_momentum=45,
        )
        assert "반도체 업황" not in report

    def test_composite_signal_shows_semiconductor_score(self):
        """종합 시그널에 반도체 점수가 표시됨."""
        sig = {
            "score": 30.0, "grade": "매수우세",
            "technical_score": 40.0, "supply_score": 30.0, "exchange_score": 10.0,
            "semiconductor_score": 35.0,
            "weights": {"technical": 36, "supply": 36, "exchange": 18, "semiconductor": 10},
        }
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "반도체" in report


class TestVolatilitySection:
    """변동성 분석 섹션 테스트."""

    def _vol_data(self, **overrides):
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

    def test_volatility_section_present(self):
        """변동성 데이터 전달 시 섹션이 포함됨."""
        report = generate_daily_report(
            _full_indicators(),
            volatility=self._vol_data(),
        )
        assert "변동성 분석" in report

    def test_volatility_section_shows_atr(self):
        """ATR 값이 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            volatility=self._vol_data(atr=1500.0, atr_pct=2.7),
        )
        assert "ATR" in report

    def test_volatility_section_shows_hv20(self):
        """HV20 연율화 값이 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            volatility=self._vol_data(hv20=0.25),
        )
        assert "HV20" in report or "25.0%" in report

    def test_volatility_section_shows_regime(self):
        """변동성 체제가 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            volatility=self._vol_data(volatility_regime="고변동성"),
        )
        assert "고변동성" in report

    def test_volatility_squeeze_shown(self):
        """밴드폭 수축이 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            volatility=self._vol_data(bandwidth_squeeze=True),
        )
        assert "수축" in report

    def test_no_volatility_no_section(self):
        """volatility=None이면 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "변동성 분석" not in report


class TestADXInReport:
    """ADX 추세 강도 섹션 테스트."""

    def _indicators_with_adx(self, adx=25.0, plus_di=20.0, minus_di=15.0):
        ind = _full_indicators()
        ind["adx"] = adx
        ind["plus_di"] = plus_di
        ind["minus_di"] = minus_di
        return ind

    def test_adx_section_present(self):
        """ADX 데이터 전달 시 섹션이 포함됨."""
        report = generate_daily_report(self._indicators_with_adx())
        assert "ADX" in report

    def test_adx_shows_values(self):
        """ADX, +DI, -DI 값이 표시됨."""
        report = generate_daily_report(self._indicators_with_adx(adx=28.5, plus_di=22.3, minus_di=14.7))
        assert "28.5" in report
        assert "+DI" in report
        assert "-DI" in report

    def test_adx_strong_trend_label(self):
        """ADX>25이면 강한 추세 표시."""
        report = generate_daily_report(self._indicators_with_adx(adx=30.0))
        assert "강한 추세" in report

    def test_adx_weak_trend_label(self):
        """ADX<20이면 추세 부재 표시."""
        report = generate_daily_report(self._indicators_with_adx(adx=15.0))
        assert "추세 부재" in report

    def test_adx_moderate_trend_label(self):
        """ADX 20~25이면 약한 추세 표시."""
        report = generate_daily_report(self._indicators_with_adx(adx=22.0))
        assert "약한 추세" in report

    def test_no_adx_no_section(self):
        """ADX=None이면 ADX 섹션 없음."""
        ind = _full_indicators()
        ind["adx"] = None
        report = generate_daily_report(ind)
        assert "ADX(14)" not in report


class TestCompositeSignalVolatilityCandlestick:
    """종합 시그널 섹션에 변동성·캔들스틱 점수 표시 테스트."""

    def test_composite_signal_shows_volatility_score(self):
        """종합 시그널에 변동성 점수가 표시됨."""
        sig = {
            "score": 30.0, "grade": "매수우세",
            "technical_score": 40.0, "supply_score": 30.0, "exchange_score": 10.0,
            "volatility_score": 15.0,
            "weights": {"technical": 36, "supply": 36, "exchange": 18, "volatility": 5, "candlestick": 5},
        }
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "변동성" in report
        assert "가중치 5%" in report

    def test_composite_signal_shows_candlestick_score(self):
        """종합 시그널에 캔들스틱 점수가 표시됨."""
        sig = {
            "score": 30.0, "grade": "매수우세",
            "technical_score": 40.0, "supply_score": 30.0, "exchange_score": 10.0,
            "candlestick_score": 20.0,
            "weights": {"technical": 36, "supply": 36, "exchange": 18, "candlestick": 5},
        }
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "캔들스틱" in report

    def test_composite_signal_shows_both_volatility_and_candlestick(self):
        """종합 시그널에 변동성과 캔들스틱 점수 모두 표시됨."""
        sig = {
            "score": 30.0, "grade": "매수우세",
            "technical_score": 40.0, "supply_score": 30.0, "exchange_score": 10.0,
            "volatility_score": 15.0, "candlestick_score": 20.0,
            "weights": {"technical": 34, "supply": 34, "exchange": 17, "volatility": 5, "candlestick": 5, "semiconductor": 5},
        }
        report = generate_daily_report(_full_indicators(), composite_signal=sig)
        assert "변동성: +15" in report
        assert "캔들스틱: +20" in report


class TestBuildExecutiveSummary:
    """핵심 요약(Executive Summary) 섹션 테스트."""

    def test_returns_empty_without_composite_signal(self):
        """composite_signal이 없으면 빈 리스트 반환."""
        result = _build_executive_summary(
            composite_signal=None,
            signal_trend=None,
            indicators=_full_indicators(),
        )
        assert result == []

    def test_shows_grade_and_score(self):
        """종합 등급과 점수가 한 줄로 표시된다."""
        sig = _composite_signal_bullish()
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=None,
            indicators=_full_indicators(),
        )
        text = "\n".join(result)
        assert "핵심 요약" in text
        assert "매수우세" in text
        assert "+45.0" in text

    def test_highlights_strongest_axes(self):
        """가장 강한 매수/매도 축 2개를 하이라이트한다."""
        sig = {
            "score": 45.0, "grade": "매수우세",
            "technical_score": 50.0, "supply_score": 60.0, "exchange_score": -10.0,
            "weights": {"technical": 40, "supply": 40, "exchange": 20},
        }
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=None,
            indicators=_full_indicators(),
        )
        text = "\n".join(result)
        assert "수급" in text
        assert "기술적" in text

    def test_shows_signal_direction_change(self):
        """signal_trend의 score_change로 방향 변화를 표시한다."""
        sig = _composite_signal_bullish()
        trend = {
            "direction": "개선",
            "score_change": 12.5,
            "days_available": 5,
            "consecutive_same_grade": 2,
            "latest_grade": "매수우세",
            "sparkline": "▂▃▅▆█",
            "scores": [20, 25, 30, 35, 45],
        }
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=trend,
            indicators=_full_indicators(),
        )
        text = "\n".join(result)
        assert "개선" in text
        assert "+12.5" in text

    def test_shows_deteriorating_direction(self):
        """악화 방향도 정상적으로 표시된다."""
        sig = {
            "score": -30.0, "grade": "매도우세",
            "technical_score": -40.0, "supply_score": -50.0, "exchange_score": 10.0,
            "weights": {"technical": 40, "supply": 40, "exchange": 20},
        }
        trend = {
            "direction": "악화",
            "score_change": -15.0,
            "days_available": 3,
            "consecutive_same_grade": 1,
            "latest_grade": "매도우세",
            "sparkline": "█▅▂",
            "scores": [10, -10, -30],
        }
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=trend,
            indicators=_full_indicators(),
        )
        text = "\n".join(result)
        assert "악화" in text
        assert "-15.0" in text

    def test_alerts_extreme_rsi(self):
        """극단적 RSI(과매수/과매도) 경고를 표시한다."""
        sig = _composite_signal_bullish()
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=None,
            indicators=_full_indicators(rsi_14=75.0),
        )
        text = "\n".join(result)
        assert "RSI" in text
        assert "과매수" in text

    def test_alerts_extreme_rsi_oversold(self):
        """RSI 과매도 경고."""
        sig = _composite_signal_bullish()
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=None,
            indicators=_full_indicators(rsi_14=25.0),
        )
        text = "\n".join(result)
        assert "과매도" in text

    def test_no_alert_normal_rsi(self):
        """RSI가 정상 범위이면 RSI 경고 없음."""
        sig = _composite_signal_bullish()
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=None,
            indicators=_full_indicators(rsi_14=50.0),
            support_resistance=None,
            trend_reversal=None,
        )
        text = "\n".join(result)
        assert "과매수" not in text
        assert "과매도" not in text

    def test_alert_support_nearby(self):
        """지지선 근접 경고."""
        sig = _composite_signal_bullish()
        sr = {
            "pivot": {"pp": 55000, "s1": 54000, "s2": 53000, "r1": 56000, "r2": 57000},
            "swing_levels": [],
            "ma_levels": {},
            "nearest_support": 54800,
            "nearest_resistance": 58000,
        }
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=None,
            indicators=_full_indicators(current_price=55000),
            support_resistance=sr,
        )
        text = "\n".join(result)
        assert "지지선" in text

    def test_alert_trend_reversal(self):
        """추세 전환 감지 경고."""
        sig = _composite_signal_bullish()
        tr = {
            "convergence": "strong",
            "direction": "bearish",
            "score": 80,
            "active_categories": 4,
            "category_signals": {},
        }
        result = _build_executive_summary(
            composite_signal=sig,
            signal_trend=None,
            indicators=_full_indicators(),
            trend_reversal=tr,
        )
        text = "\n".join(result)
        assert "추세 전환" in text

    def test_executive_summary_in_report(self):
        """generate_daily_report에 핵심 요약 섹션이 포함된다."""
        sig = _composite_signal_bullish()
        report = generate_daily_report(
            _full_indicators(),
            composite_signal=sig,
        )
        assert "핵심 요약" in report

    def test_executive_summary_before_composite_signal(self):
        """핵심 요약이 종합 판정 섹션보다 먼저 나온다."""
        sig = _composite_signal_bullish()
        report = generate_daily_report(
            _full_indicators(),
            composite_signal=sig,
        )
        summary_pos = report.find("핵심 요약")
        composite_pos = report.find("오늘의 종합 판정")
        assert summary_pos < composite_pos


class TestConvergenceSection:
    """수렴 분석 섹션 테스트."""

    def _convergence(self, **overrides):
        base = {
            "convergence_level": "strong",
            "dominant_direction": "bullish",
            "aligned_axes": ["technical_score", "supply_score", "exchange_score",
                             "fundamental_score", "news_score", "consensus_score",
                             "semiconductor_score"],
            "conflicting_axes": ["volatility_score"],
            "neutral_axes": ["candlestick_score"],
            "conviction": 78,
            "axis_directions": {
                "technical_score": "bullish", "supply_score": "bullish",
                "exchange_score": "bullish", "fundamental_score": "bullish",
                "news_score": "bullish", "consensus_score": "bullish",
                "semiconductor_score": "bullish",
                "volatility_score": "bearish", "candlestick_score": "neutral",
            },
        }
        base.update(overrides)
        return base

    def test_convergence_section_present(self):
        """수렴 분석 결과가 리포트에 섹션으로 포함된다."""
        report = generate_daily_report(
            _full_indicators(),
            convergence=self._convergence(),
        )
        assert "수렴 분석" in report

    def test_convergence_level_shown(self):
        """수렴 수준이 표시된다."""
        report = generate_daily_report(
            _full_indicators(),
            convergence=self._convergence(convergence_level="strong"),
        )
        assert "강한 수렴" in report or "strong" in report.lower()

    def test_dominant_direction_shown(self):
        """지배적 방향이 표시된다."""
        report = generate_daily_report(
            _full_indicators(),
            convergence=self._convergence(dominant_direction="bullish"),
        )
        assert "강세" in report

    def test_conviction_shown(self):
        """확신도가 표시된다."""
        report = generate_daily_report(
            _full_indicators(),
            convergence=self._convergence(conviction=78),
        )
        assert "78" in report

    def test_aligned_axes_shown(self):
        """일치 축이 표시된다."""
        report = generate_daily_report(
            _full_indicators(),
            convergence=self._convergence(),
        )
        assert "일치" in report or "7" in report

    def test_conflicting_axes_shown(self):
        """충돌 축이 표시된다."""
        report = generate_daily_report(
            _full_indicators(),
            convergence=self._convergence(conflicting_axes=["volatility_score"]),
        )
        assert "충돌" in report or "1" in report

    def test_no_convergence_no_section(self):
        """convergence=None이면 수렴 분석 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "수렴 분석" not in report


class TestGlobalMacroSection:
    """글로벌 매크로 리포트 섹션 테스트."""

    def test_no_macro_no_section(self):
        """매크로 데이터 없으면 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "글로벌 매크로" not in report

    def test_macro_section_present(self):
        """매크로 데이터가 있으면 섹션이 포함."""
        report = generate_daily_report(
            _full_indicators(),
            nasdaq_trend={"trend": "상승", "ma_position": "위", "change_pct": 1.2},
            vix_risk={"level": "안정", "value": 14.5},
            global_macro_score=35,
        )
        assert "글로벌 매크로" in report

    def test_nasdaq_trend_shown(self):
        """NASDAQ 추세 정보가 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            nasdaq_trend={"trend": "상승", "ma_position": "위", "change_pct": 1.2},
            vix_risk={"level": "안정", "value": 14.5},
            global_macro_score=35,
        )
        assert "NASDAQ" in report
        assert "상승" in report

    def test_vix_risk_shown(self):
        """VIX 리스크 수준이 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            nasdaq_trend={"trend": "하락", "ma_position": "아래", "change_pct": -2.0},
            vix_risk={"level": "공포", "value": 32.5},
            global_macro_score=-40,
        )
        assert "VIX" in report
        assert "공포" in report

    def test_macro_score_shown(self):
        """매크로 스코어가 표시됨."""
        report = generate_daily_report(
            _full_indicators(),
            nasdaq_trend={"trend": "보합", "ma_position": "근접", "change_pct": 0.1},
            vix_risk={"level": "경계", "value": 22.0},
            global_macro_score=-15,
        )
        assert "-15" in report

    def test_vix_extreme_level(self):
        """VIX 극단 수준 표시."""
        report = generate_daily_report(
            _full_indicators(),
            nasdaq_trend={"trend": "하락", "ma_position": "아래", "change_pct": -5.0},
            vix_risk={"level": "극단", "value": 45.0},
            global_macro_score=-80,
        )
        assert "극단" in report

    def test_partial_macro_none_nasdaq(self):
        """nasdaq_trend=None이면 섹션 없음."""
        report = generate_daily_report(
            _full_indicators(),
            nasdaq_trend=None,
            vix_risk={"level": "안정", "value": 14.5},
            global_macro_score=35,
        )
        assert "글로벌 매크로" not in report

    def test_partial_macro_none_vix(self):
        """vix_risk=None이면 섹션 없음."""
        report = generate_daily_report(
            _full_indicators(),
            nasdaq_trend={"trend": "상승", "ma_position": "위", "change_pct": 1.2},
            vix_risk=None,
            global_macro_score=35,
        )
        assert "글로벌 매크로" not in report

    def test_partial_macro_none_score(self):
        """global_macro_score=None이면 섹션 없음."""
        report = generate_daily_report(
            _full_indicators(),
            nasdaq_trend={"trend": "상승", "ma_position": "위", "change_pct": 1.2},
            vix_risk={"level": "안정", "value": 14.5},
            global_macro_score=None,
        )
        assert "글로벌 매크로" not in report

    def test_macro_after_semiconductor(self):
        """글로벌 매크로 섹션이 반도체 섹션 뒤에 위치."""
        report = generate_daily_report(
            _full_indicators(),
            rel_perf=_rel_perf_sample(),
            sox_trend=_sox_trend_sample(),
            semiconductor_momentum=45,
            nasdaq_trend={"trend": "상승", "ma_position": "위", "change_pct": 1.2},
            vix_risk={"level": "안정", "value": 14.5},
            global_macro_score=35,
        )
        semi_pos = report.index("반도체 업황")
        macro_pos = report.index("글로벌 매크로")
        assert macro_pos > semi_pos

    def test_macro_before_convergence(self):
        """글로벌 매크로 섹션이 수렴 분석 섹션 앞에 위치."""
        conv = {
            "convergence_level": "strong",
            "dominant_direction": "bullish",
            "conviction": 80,
            "aligned_axes": ["technical_score"],
            "conflicting_axes": [],
            "neutral_axes": [],
            "axis_directions": {},
        }
        report = generate_daily_report(
            _full_indicators(),
            convergence=conv,
            nasdaq_trend={"trend": "상승", "ma_position": "위", "change_pct": 1.2},
            vix_risk={"level": "안정", "value": 14.5},
            global_macro_score=35,
        )
        macro_pos = report.index("글로벌 매크로")
        conv_pos = report.index("수렴 분석")
        assert macro_pos < conv_pos


class TestTimeframeSection:
    """멀티타임프레임 분석 섹션 테스트."""

    def test_timeframe_section_present(self):
        """timeframe 데이터가 주어지면 주봉 섹션 포함."""
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
        report = generate_daily_report(
            _full_indicators(),
            timeframe_alignment=alignment,
            weekly_indicators=weekly_ind,
        )
        assert "멀티타임프레임" in report or "주봉" in report

    def test_timeframe_section_absent_when_none(self):
        """timeframe 데이터 없으면 섹션 없음."""
        report = generate_daily_report(_full_indicators())
        assert "멀티타임프레임" not in report

    def test_timeframe_section_shows_ma_values(self):
        """주봉 MA5w, MA13w 값이 표시됨."""
        alignment = {
            "alignment": "divergent_bullish",
            "interpretation": "주봉 상승 추세 유지",
            "score_modifier": 0.2,
        }
        weekly_ind = {
            "ma5w": 55000, "ma13w": 54000,
            "rsi_weekly": 55.0, "weekly_trend": "up",
            "weekly_close": 55500, "weekly_data_weeks": 15,
        }
        report = generate_daily_report(
            _full_indicators(),
            timeframe_alignment=alignment,
            weekly_indicators=weekly_ind,
        )
        assert "MA5w" in report
        assert "MA13w" in report

    def test_timeframe_alignment_displayed(self):
        """정합성 판정(aligned/divergent/neutral)이 리포트에 표시됨."""
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
        report = generate_daily_report(
            _full_indicators(),
            timeframe_alignment=alignment,
            weekly_indicators=weekly_ind,
        )
        assert "하락" in report or "bearish" in report or "약세" in report


class TestDailyDeltaSection:
    """daily_delta 섹션 렌더링 테스트."""

    def test_daily_delta_section_rendered(self):
        """daily_delta가 전달되면 '오늘의 변화' 섹션이 렌더링됨."""
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
        report = generate_daily_report(_full_indicators(), daily_delta=delta)
        assert "오늘의 변화" in report
        assert "⬆️" in report or "⬇️" in report or "🔄" in report

    def test_daily_delta_with_signal_flip(self):
        """방향 전환 축은 🔄로 표시됨."""
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
        report = generate_daily_report(_full_indicators(), daily_delta=delta)
        assert "🔄" in report

    def test_daily_delta_no_alerts(self):
        """알림이 없으면 '주요 변화 없음' 표시."""
        delta = {
            "axes_delta": {
                "technical_score": {"prev": 10, "curr": 12, "change": 2},
            },
            "alerts": [],
            "overall": {
                "prev_score": 30.0, "curr_score": 32.0, "change": 2.0,
                "prev_grade": "매수", "curr_grade": "매수",
            },
        }
        report = generate_daily_report(_full_indicators(), daily_delta=delta)
        assert "주요 변화 없음" in report

    def test_daily_delta_none_no_section(self):
        """daily_delta가 None이면 섹션이 없음."""
        report = generate_daily_report(_full_indicators())
        assert "오늘의 변화" not in report

    def test_risk_management_section_present(self):
        """risk_management가 주어지면 섹션이 표시됨."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "stop_level": {"price": 53875.0, "method": "지지선_ATR", "atr_multiplier": 1.5, "regime": "보통"},
            "target_levels": {
                "target_1": {"price": 58000.0, "basis": "최근접 저항선"},
                "target_2": {"price": 64750.0, "basis": "ATR 2.5배"},
                "direction": "상승",
            },
            "risk_reward": {"ratio": 1.8, "grade": "유리", "risk": 3000.0, "reward": 5400.0},
            "position_guide": {"level": "표준", "description": "보통 조건 — 기본 진입 구간", "score": 4},
            "summary": "R:R 1.8 — 유리. 표준 포지션.",
        }
        report = generate_daily_report(_full_indicators(), risk_management=rm)
        assert "리스크 관리" in report

    def test_risk_management_shows_entry_zone(self):
        """진입 구간이 표시됨."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "stop_level": {"price": 53875.0, "method": "ATR_배수", "atr_multiplier": 1.5, "regime": "보통"},
            "target_levels": {"target_1": {"price": 58000.0, "basis": "저항선"}, "target_2": {"price": 64750.0, "basis": "ATR"}, "direction": "상승"},
            "risk_reward": {"ratio": 1.8, "grade": "유리", "risk": 3000.0, "reward": 5400.0},
            "position_guide": {"level": "표준", "description": "기본", "score": 4},
            "summary": "test",
        }
        report = generate_daily_report(_full_indicators(), risk_management=rm)
        assert "매수" in report
        assert "57,100" in report

    def test_risk_management_shows_stop_level(self):
        """손절선이 표시됨."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "stop_level": {"price": 53875.0, "method": "지지선_ATR", "atr_multiplier": 1.5, "regime": "보통"},
            "target_levels": {"target_1": {"price": 58000.0, "basis": "저항선"}, "target_2": {"price": 64750.0, "basis": "ATR"}, "direction": "상승"},
            "risk_reward": {"ratio": 1.8, "grade": "유리", "risk": 3000.0, "reward": 5400.0},
            "position_guide": {"level": "표준", "description": "기본", "score": 4},
            "summary": "test",
        }
        report = generate_daily_report(_full_indicators(), risk_management=rm)
        assert "손절" in report
        assert "53,875" in report

    def test_risk_management_shows_rr_ratio(self):
        """R:R 비율이 표시됨."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "stop_level": {"price": 53875.0, "method": "ATR_배수", "atr_multiplier": 1.5, "regime": "보통"},
            "target_levels": {"target_1": {"price": 58000.0, "basis": "저항선"}, "target_2": {"price": 64750.0, "basis": "ATR"}, "direction": "상승"},
            "risk_reward": {"ratio": 1.8, "grade": "유리", "risk": 3000.0, "reward": 5400.0},
            "position_guide": {"level": "표준", "description": "기본", "score": 4},
            "summary": "test",
        }
        report = generate_daily_report(_full_indicators(), risk_management=rm)
        assert "R:R 1.8" in report
        assert "✅" in report

    def test_risk_management_shows_position_guide(self):
        """포지션 가이드가 표시됨."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "stop_level": {"price": 53875.0, "method": "ATR_배수", "atr_multiplier": 1.5, "regime": "보통"},
            "target_levels": {"target_1": {"price": 58000.0, "basis": "저항선"}, "target_2": {"price": 64750.0, "basis": "ATR"}, "direction": "상승"},
            "risk_reward": {"ratio": 0.5, "grade": "불리", "risk": 5000.0, "reward": 2500.0},
            "position_guide": {"level": "관망", "description": "불리 조건 다수 — 진입 대기", "score": 0},
            "summary": "test",
        }
        report = generate_daily_report(_full_indicators(), risk_management=rm)
        assert "관망" in report
        assert "🚫" in report

    def test_risk_management_none_no_section(self):
        """risk_management가 None이면 섹션이 없음."""
        report = generate_daily_report(_full_indicators())
        assert "리스크 관리" not in report

    def test_risk_management_in_executive_summary(self):
        """R:R이 핵심 요약에도 표시됨."""
        rm = {
            "entry_zone": {"lower": 57100.0, "upper": 61555.0, "direction": "매수", "basis": "test"},
            "stop_level": {"price": 53875.0, "method": "ATR_배수", "atr_multiplier": 1.5, "regime": "보통"},
            "target_levels": {"target_1": {"price": 58000.0, "basis": "저항선"}, "target_2": {"price": 64750.0, "basis": "ATR"}, "direction": "상승"},
            "risk_reward": {"ratio": 1.8, "grade": "유리", "risk": 3000.0, "reward": 5400.0},
            "position_guide": {"level": "표준", "description": "기본", "score": 4},
            "summary": "test",
        }
        sig = {"score": 35.0, "grade": "매수우세", "technical_score": 40.0, "supply_score": 50.0, "exchange_score": -10.0, "weights": {"technical": 40, "supply": 40, "exchange": 20}}
        report = generate_daily_report(_full_indicators(), composite_signal=sig, risk_management=rm)
        summary_end = report.find("핵심 관찰 포인트") if "핵심 관찰 포인트" in report else report.find("종합 투자 시그널")
        summary_section = report[:summary_end] if summary_end > 0 else report
        assert "포지션: 표준" in summary_section


class TestMarketRegimeSection:
    """시장 체제(Market Regime) 섹션 렌더링 테스트."""

    SAMPLE_REGIME = {
        "regime": "trending_up",
        "phase": "markup",
        "confidence": 75,
        "duration": 12,
        "interpretation_hints": {
            "rsi_thresholds": {"overbought": 80, "oversold": 20},
            "support_resistance_reliability": "low",
            "volume_confirmation_importance": "medium",
            "description": "추세장 — RSI 기준 완화, 지지/저항 신뢰도 하향",
        },
        "adx": 30.5,
        "ma_alignment": "bullish",
        "bb_pctb": 0.72,
    }

    def test_market_regime_section_present(self):
        report = generate_daily_report(_full_indicators(), market_regime=self.SAMPLE_REGIME)
        assert "시장 체제" in report

    def test_market_regime_shows_regime_name(self):
        report = generate_daily_report(_full_indicators(), market_regime=self.SAMPLE_REGIME)
        assert "추세상승" in report

    def test_market_regime_shows_phase(self):
        report = generate_daily_report(_full_indicators(), market_regime=self.SAMPLE_REGIME)
        assert "마크업" in report

    def test_market_regime_shows_confidence(self):
        report = generate_daily_report(_full_indicators(), market_regime=self.SAMPLE_REGIME)
        assert "75%" in report

    def test_market_regime_shows_duration(self):
        report = generate_daily_report(_full_indicators(), market_regime=self.SAMPLE_REGIME)
        assert "12일" in report

    def test_market_regime_shows_interpretation(self):
        report = generate_daily_report(_full_indicators(), market_regime=self.SAMPLE_REGIME)
        assert "RSI" in report

    def test_market_regime_none_no_section(self):
        report = generate_daily_report(_full_indicators(), market_regime=None)
        assert "시장 체제" not in report

    def test_market_regime_range_bound(self):
        regime = {**self.SAMPLE_REGIME, "regime": "range_bound", "phase": "accumulation"}
        report = generate_daily_report(_full_indicators(), market_regime=regime)
        assert "횡보" in report
        assert "매집" in report

    def test_market_regime_breakdown(self):
        regime = {**self.SAMPLE_REGIME, "regime": "breakdown", "phase": "markdown"}
        report = generate_daily_report(_full_indicators(), market_regime=regime)
        assert "붕괴" in report

    def test_market_regime_after_composite_signal(self):
        sig = {"score": 35.0, "grade": "매수우세", "technical_score": 40.0, "supply_score": 50.0, "exchange_score": -10.0, "weights": {"technical": 40, "supply": 40, "exchange": 20}}
        report = generate_daily_report(_full_indicators(), composite_signal=sig, market_regime=self.SAMPLE_REGIME)
        signal_pos = report.find("종합 판정")
        regime_pos = report.find("시장 체제")
        assert signal_pos < regime_pos

    def test_market_regime_shows_adjustment_explanation(self):
        """RSI 기준이 기본값과 다를 때 조정 이유가 표시됨."""
        report = generate_daily_report(_full_indicators(), market_regime=self.SAMPLE_REGIME)
        assert "조정" in report or "완화" in report or "강화" in report

    def test_market_regime_default_thresholds_no_adjustment(self):
        """RSI 기준이 기본값(70/30)이면 조정 설명 없음."""
        regime = {
            **self.SAMPLE_REGIME,
            "interpretation_hints": {
                "rsi_thresholds": {"overbought": 70, "oversold": 30},
                "support_resistance_reliability": "high",
                "description": "횡보장",
            },
        }
        report = generate_daily_report(_full_indicators(), market_regime=regime)
        assert "기본값" not in report


SAMPLE_FIBONACCI = {
    "retracement": {"0.0": 60000, "0.236": 58112, "0.382": 56952, "0.5": 56000, "0.618": 55048, "0.786": 53712, "1.0": 52000},
    "extension": {"1.0": 68000, "1.272": 70176, "1.618": 72944},
    "position": {"below": "0.618", "above": "0.5", "nearest_support": 55048, "nearest_resistance": 56000},
    "swing_high": {"price": 60000, "date": "2026-03-15", "index": 40},
    "swing_low": {"price": 52000, "date": "2026-03-01", "index": 10},
    "trend": "up",
}

SAMPLE_FIBONACCI_EMPTY = {
    "retracement": {},
    "extension": {},
    "position": {"below": None, "above": None, "nearest_support": None, "nearest_resistance": None},
    "swing_high": None,
    "swing_low": None,
    "trend": None,
}


class TestBuildFibonacciSection:
    """피보나치 되돌림 섹션 렌더링 테스트."""

    def test_section_returns_list_of_strings(self):
        result = _build_fibonacci_section(SAMPLE_FIBONACCI, 55500)
        assert isinstance(result, list)
        assert all(isinstance(line, str) for line in result)

    def test_section_contains_header(self):
        result = _build_fibonacci_section(SAMPLE_FIBONACCI, 55500)
        joined = "\n".join(result)
        assert "피보나치" in joined

    def test_section_shows_retracement_levels(self):
        result = _build_fibonacci_section(SAMPLE_FIBONACCI, 55500)
        joined = "\n".join(result)
        assert "0.382" in joined
        assert "0.618" in joined

    def test_section_shows_swing_points(self):
        result = _build_fibonacci_section(SAMPLE_FIBONACCI, 55500)
        joined = "\n".join(result)
        assert "60,000" in joined or "60000" in joined
        assert "52,000" in joined or "52000" in joined

    def test_section_shows_current_position(self):
        result = _build_fibonacci_section(SAMPLE_FIBONACCI, 55500)
        joined = "\n".join(result)
        assert "0.618" in joined or "0.5" in joined

    def test_section_shows_extension_levels(self):
        result = _build_fibonacci_section(SAMPLE_FIBONACCI, 55500)
        joined = "\n".join(result)
        assert "1.618" in joined or "확장" in joined

    def test_empty_fibonacci_returns_empty_or_minimal(self):
        result = _build_fibonacci_section(SAMPLE_FIBONACCI_EMPTY, 55500)
        assert len(result) <= 2

    def test_fibonacci_in_full_report(self):
        report = generate_daily_report(_full_indicators(), fibonacci=SAMPLE_FIBONACCI)
        assert "피보나치" in report

    def test_fibonacci_none_no_section(self):
        report = generate_daily_report(_full_indicators(), fibonacci=None)
        assert "피보나치" not in report

    def test_fibonacci_after_support_resistance(self):
        sr = {"pivot": {"pp": 55500, "s1": 55000, "s2": 54500, "r1": 56000, "r2": 56500}, "nearest_support": 55000, "nearest_resistance": 56000, "swing_levels": [], "ma_levels": {}}
        report = generate_daily_report(_full_indicators(), support_resistance=sr, fibonacci=SAMPLE_FIBONACCI)
        sr_pos = report.find("📐 지지/저항선")
        fib_pos = report.find("📐 피보나치 되돌림")
        assert sr_pos < fib_pos


# --- 백테스팅 성과 섹션 ---

SAMPLE_BACKTEST = {
    "grade_performance": {
        "강력매수": {"count": 5, "avg_return_1d": 1.2, "hit_rate_1d": 80.0, "avg_return_3d": 2.5, "hit_rate_3d": 75.0, "avg_return_5d": 3.0, "hit_rate_5d": 70.0},
        "매수우세": {"count": 10, "avg_return_1d": 0.5, "hit_rate_1d": 65.0, "avg_return_3d": 1.0, "hit_rate_3d": 60.0, "avg_return_5d": 1.5, "hit_rate_5d": 55.0},
        "중립": {"count": 8, "avg_return_1d": 0.0, "hit_rate_1d": 50.0, "avg_return_3d": 0.1, "hit_rate_3d": 48.0, "avg_return_5d": -0.1, "hit_rate_5d": 45.0},
    },
    "score_range_performance": [
        {"range_label": "강력매도 (-100~-60)", "count": 2, "avg_return_1d": -1.0, "hit_rate_1d": 60.0, "avg_return_3d": -2.0, "hit_rate_3d": 55.0, "avg_return_5d": -2.5, "hit_rate_5d": 50.0},
        {"range_label": "매도우세 (-60~-20)", "count": 3, "avg_return_1d": -0.5, "hit_rate_1d": 55.0, "avg_return_3d": -1.0, "hit_rate_3d": 50.0, "avg_return_5d": -1.2, "hit_rate_5d": 48.0},
        {"range_label": "중립 (-20~+20)", "count": 8, "avg_return_1d": 0.0, "hit_rate_1d": 50.0, "avg_return_3d": 0.1, "hit_rate_3d": 48.0, "avg_return_5d": -0.1, "hit_rate_5d": 45.0},
        {"range_label": "매수우세 (+20~+60)", "count": 10, "avg_return_1d": 0.5, "hit_rate_1d": 65.0, "avg_return_3d": 1.0, "hit_rate_3d": 60.0, "avg_return_5d": 1.5, "hit_rate_5d": 55.0},
        {"range_label": "강력매수 (+60~+100)", "count": 5, "avg_return_1d": 1.2, "hit_rate_1d": 80.0, "avg_return_3d": 2.5, "hit_rate_3d": 75.0, "avg_return_5d": 3.0, "hit_rate_5d": 70.0},
    ],
    "streak_analysis": {"max_win_streak": 7, "max_lose_streak": 3, "equity_curve": []},
    "axis_contribution": {
        "technical": {"correlation_1d": 0.45, "contribution_rank": 1},
        "supply": {"correlation_1d": 0.30, "contribution_rank": 2},
        "exchange": {"correlation_1d": 0.15, "contribution_rank": 3},
    },
}


class TestBuildBacktestSection:
    """백테스팅 성과 섹션 렌더링 테스트."""

    def test_section_contains_header(self):
        result = _build_backtest_section(SAMPLE_BACKTEST)
        joined = "\n".join(result)
        assert "백테스팅 성과" in joined

    def test_grade_performance_rendered(self):
        result = _build_backtest_section(SAMPLE_BACKTEST)
        joined = "\n".join(result)
        assert "강력매수" in joined
        assert "70.0%" in joined

    def test_score_range_rendered(self):
        result = _build_backtest_section(SAMPLE_BACKTEST)
        joined = "\n".join(result)
        assert "강력매도" in joined or "점수 구간" in joined

    def test_axis_contribution_rendered(self):
        result = _build_backtest_section(SAMPLE_BACKTEST)
        joined = "\n".join(result)
        assert "기여도" in joined or "상관" in joined

    def test_streak_rendered(self):
        result = _build_backtest_section(SAMPLE_BACKTEST)
        joined = "\n".join(result)
        assert "연승" in joined or "7" in joined

    def test_none_backtest_returns_empty(self):
        result = _build_backtest_section(None)
        assert result == []

    def test_empty_grade_performance(self):
        bt = {
            "grade_performance": {},
            "score_range_performance": [],
            "streak_analysis": {"max_win_streak": 0, "max_lose_streak": 0, "equity_curve": []},
            "axis_contribution": {},
        }
        result = _build_backtest_section(bt)
        joined = "\n".join(result)
        assert "백테스팅 성과" in joined

    def test_backtest_in_full_report(self):
        report = generate_daily_report(_full_indicators(), backtest=SAMPLE_BACKTEST)
        assert "백테스팅 성과" in report

    def test_backtest_none_no_section(self):
        report = generate_daily_report(_full_indicators(), backtest=None)
        assert "백테스팅 성과" not in report
