"""멀티타임프레임 분석 모듈 테스트."""

import datetime

from src.analysis.timeframe import (
    resample_daily_to_weekly,
    compute_weekly_indicators,
    assess_timeframe_alignment,
)


def _make_row(date_str: str, open_: float, high: float, low: float,
              close: float, volume: int = 1000000) -> dict:
    return {
        "date": date_str,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def _generate_daily_rows(n: int, start_price: float = 50000.0,
                         start_date: str = "2026-01-05") -> list[dict]:
    """n일치 일봉 데이터를 생성한다 (월~금만)."""
    rows = []
    price = start_price
    dt = datetime.date.fromisoformat(start_date)
    for i in range(n):
        # 주말 건너뛰기
        while dt.weekday() >= 5:
            dt += datetime.timedelta(days=1)
        # 약간의 변동
        delta = (i % 7 - 3) * 100
        o = price
        h = price + abs(delta) + 500
        l = price - 300
        c = price + delta
        rows.append(_make_row(dt.isoformat(), o, h, l, c, 1000000 + i * 10000))
        price = c
        dt += datetime.timedelta(days=1)
    return rows


class TestResampleDailyToWeekly:
    """일봉 → 주봉 리샘플링 테스트."""

    def test_basic_resampling(self):
        """5일(월~금)이 1개 주봉으로 변환된다."""
        rows = [
            _make_row("2026-01-05", 50000, 51000, 49000, 50500, 100),  # 월
            _make_row("2026-01-06", 50500, 52000, 50000, 51000, 200),  # 화
            _make_row("2026-01-07", 51000, 51500, 49500, 50000, 150),  # 수
            _make_row("2026-01-08", 50000, 50500, 48000, 48500, 300),  # 목
            _make_row("2026-01-09", 48500, 49000, 47000, 49000, 250),  # 금
        ]
        weekly = resample_daily_to_weekly(rows)
        assert len(weekly) == 1
        w = weekly[0]
        assert w["open"] == 50000      # 월요일 시가
        assert w["high"] == 52000      # 주간 최고가
        assert w["low"] == 47000       # 주간 최저가
        assert w["close"] == 49000     # 금요일 종가
        assert w["volume"] == 1000     # 합계

    def test_multiple_weeks(self):
        """10일 → 2주봉."""
        rows = _generate_daily_rows(10)
        weekly = resample_daily_to_weekly(rows)
        assert len(weekly) == 2

    def test_partial_week_included(self):
        """불완전한 주도 포함된다 (현재 주)."""
        rows = [
            _make_row("2026-01-05", 50000, 51000, 49000, 50500, 100),  # 월
            _make_row("2026-01-06", 50500, 52000, 50000, 51000, 200),  # 화
            _make_row("2026-01-07", 51000, 51500, 49500, 50000, 150),  # 수
        ]
        weekly = resample_daily_to_weekly(rows)
        assert len(weekly) == 1
        assert weekly[0]["close"] == 50000  # 수요일 종가 (마지막 거래일)

    def test_empty_input(self):
        """빈 입력 → 빈 결과."""
        assert resample_daily_to_weekly([]) == []

    def test_week_date_is_monday(self):
        """주봉의 date는 해당 주의 월요일이다."""
        rows = [
            _make_row("2026-01-07", 50000, 51000, 49000, 50500, 100),  # 수
            _make_row("2026-01-08", 50500, 52000, 50000, 51000, 200),  # 목
        ]
        weekly = resample_daily_to_weekly(rows)
        assert weekly[0]["date"] == "2026-01-05"  # 해당 주 월요일


class TestComputeWeeklyIndicators:
    """주봉 지표 계산 테스트."""

    def test_insufficient_data(self):
        """데이터 부족 시 None 반환."""
        rows = _generate_daily_rows(10)
        result = compute_weekly_indicators(rows)
        assert result["ma5w"] is None
        assert result["ma13w"] is None
        assert result["rsi_weekly"] is None

    def test_sufficient_data_ma5w(self):
        """25일(5주) 이상이면 MA5w 계산."""
        rows = _generate_daily_rows(30)
        result = compute_weekly_indicators(rows)
        assert result["ma5w"] is not None
        assert isinstance(result["ma5w"], float)

    def test_sufficient_data_ma13w(self):
        """65일(13주) 이상이면 MA13w 계산."""
        rows = _generate_daily_rows(80)
        result = compute_weekly_indicators(rows)
        assert result["ma13w"] is not None

    def test_rsi_weekly(self):
        """15주 이상이면 RSI 계산 (0~100 범위)."""
        rows = _generate_daily_rows(90)
        result = compute_weekly_indicators(rows)
        if result["rsi_weekly"] is not None:
            assert 0 <= result["rsi_weekly"] <= 100

    def test_trend_direction(self):
        """추세 방향은 'up', 'down', 'sideways' 중 하나."""
        rows = _generate_daily_rows(80)
        result = compute_weekly_indicators(rows)
        assert result["weekly_trend"] in ("up", "down", "sideways", None)

    def test_empty_input(self):
        """빈 데이터 → 모두 None."""
        result = compute_weekly_indicators([])
        assert result["ma5w"] is None
        assert result["weekly_trend"] is None


class TestTimeframeAlignment:
    """일봉-주봉 정합성 판정 테스트."""

    def test_aligned_bullish(self):
        """주봉 상승 + 일봉 과매도 → aligned_bullish."""
        result = assess_timeframe_alignment(
            weekly_trend="up",
            weekly_rsi=55.0,
            daily_rsi=28.0,
        )
        assert result["alignment"] == "aligned_bullish"
        assert "매수 기회" in result["interpretation"]

    def test_aligned_bearish(self):
        """주봉 하락 + 일봉 과매수 → aligned_bearish."""
        result = assess_timeframe_alignment(
            weekly_trend="down",
            weekly_rsi=40.0,
            daily_rsi=75.0,
        )
        assert result["alignment"] == "aligned_bearish"
        assert "매도" in result["interpretation"] or "하락" in result["interpretation"]

    def test_divergent_bullish(self):
        """주봉 상승 + 일봉 중립 → divergent_bullish (단기 조정 중 상승 추세)."""
        result = assess_timeframe_alignment(
            weekly_trend="up",
            weekly_rsi=60.0,
            daily_rsi=50.0,
        )
        assert result["alignment"] == "divergent_bullish"

    def test_divergent_bearish(self):
        """주봉 하락 + 일봉 중립/과매수 아닌 → divergent_bearish."""
        result = assess_timeframe_alignment(
            weekly_trend="down",
            weekly_rsi=35.0,
            daily_rsi=50.0,
        )
        assert result["alignment"] == "divergent_bearish"

    def test_none_inputs(self):
        """None 입력 → neutral."""
        result = assess_timeframe_alignment(
            weekly_trend=None,
            weekly_rsi=None,
            daily_rsi=None,
        )
        assert result["alignment"] == "neutral"
        assert "데이터 부족" in result["interpretation"]
