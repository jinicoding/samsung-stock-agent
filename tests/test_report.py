"""일일 분석 리포트 생성기 테스트."""

import pytest

from src.analysis.report import generate_daily_report, classify_ma_alignment, assess_volume, assess_market_temperature, classify_macd, classify_bb_position


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
