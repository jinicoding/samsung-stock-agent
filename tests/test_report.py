"""일일 분석 리포트 생성기 테스트."""

import pytest

from src.analysis.report import generate_daily_report, classify_ma_alignment, assess_volume, assess_market_temperature


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
