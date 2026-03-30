"""일일 분석 리포트 생성기 테스트."""

import pytest

from src.analysis.report import generate_daily_report, classify_ma_alignment, assess_volume, assess_market_temperature, classify_macd, classify_bb_position, classify_stochastic


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
