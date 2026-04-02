"""캔들스틱 패턴 인식 모듈 테스트."""

import pytest

from src.analysis.candlestick import detect_candlestick_patterns


def _make_rows(ohlcv_list: list[tuple]) -> list[dict]:
    """테스트용 OHLCV rows 생성.

    Args:
        ohlcv_list: [(open, high, low, close, volume), ...]
    """
    rows = []
    for i, (o, h, l, c, v) in enumerate(ohlcv_list):
        rows.append({
            "date": f"2026-03-{i + 1:02d}",
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
        })
    return rows


class TestInputValidation:
    """입력 검증 테스트."""

    def test_empty_rows_raises(self):
        with pytest.raises(ValueError):
            detect_candlestick_patterns([])

    def test_single_row_returns_result(self):
        rows = _make_rows([(50000, 51000, 49000, 50500, 1000000)])
        result = detect_candlestick_patterns(rows)
        assert "patterns" in result
        assert "signal" in result
        assert "score" in result


class TestDoji:
    """도지(Doji) 패턴 테스트."""

    def test_doji_detected(self):
        """시가 == 종가(또는 매우 근접) → 도지."""
        rows = _make_rows([(50000, 51000, 49000, 50000, 1000000)])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "doji" in names

    def test_no_doji_when_body_large(self):
        """몸통이 크면 도지가 아님."""
        rows = _make_rows([(50000, 52000, 49000, 52000, 1000000)])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "doji" not in names


class TestHammer:
    """해머(Hammer) 패턴 테스트."""

    def test_hammer_detected(self):
        """하락 추세 후 긴 아래꼬리 + 짧은 몸통 → 해머(강세 반전)."""
        # 하락 추세 선행 캔들 + 해머 캔들
        rows = _make_rows([
            (53000, 53500, 52500, 52500, 1000000),  # 하락
            (52000, 52300, 51800, 51500, 1000000),  # 하락
            (51000, 51200, 50800, 50500, 1000000),  # 하락
            # 해머: 몸통 300원, 아래꼬리 700원, 윗꼬리 0원
            (50500, 50500, 49500, 50200, 1000000),
        ])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "hammer" in names

    def test_no_hammer_without_lower_shadow(self):
        """아래꼬리가 짧으면 해머가 아님."""
        rows = _make_rows([
            (53000, 53500, 52500, 52500, 1000000),
            (52000, 52300, 51800, 51500, 1000000),
            (51000, 51200, 50800, 50500, 1000000),
            (50500, 51500, 50400, 51000, 1000000),  # 윗꼬리가 긴 경우
        ])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "hammer" not in names


class TestHangingMan:
    """행잉맨(Hanging Man) 패턴 테스트."""

    def test_hanging_man_detected(self):
        """상승 추세 후 긴 아래꼬리 + 짧은 몸통 → 행잉맨(약세 반전)."""
        rows = _make_rows([
            (50000, 50500, 49800, 50500, 1000000),  # 상승
            (50500, 51200, 50300, 51000, 1000000),  # 상승
            (51000, 51800, 50800, 51500, 1000000),  # 상승
            # 행잉맨: 몸통 300원, 아래꼬리 700원, 윗꼬리 0원
            (51500, 51500, 50500, 51200, 1000000),
        ])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "hanging_man" in names


class TestMarubozu:
    """마루보즈(Marubozu) 패턴 테스트."""

    def test_bullish_marubozu(self):
        """꼬리가 거의 없는 강한 양봉 → 강세 마루보즈."""
        rows = _make_rows([(50000, 52000, 50000, 52000, 1000000)])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "bullish_marubozu" in names

    def test_bearish_marubozu(self):
        """꼬리가 거의 없는 강한 음봉 → 약세 마루보즈."""
        rows = _make_rows([(52000, 52000, 50000, 50000, 1000000)])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "bearish_marubozu" in names


class TestEngulfing:
    """인걸핑(Engulfing) 패턴 테스트."""

    def test_bullish_engulfing(self):
        """작은 음봉 후 큰 양봉이 감싸면 → 강세 인걸핑."""
        rows = _make_rows([
            (51000, 51200, 50500, 50600, 1000000),  # 작은 음봉
            (50400, 51500, 50300, 51400, 1000000),  # 큰 양봉이 감싸기
        ])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "bullish_engulfing" in names

    def test_bearish_engulfing(self):
        """작은 양봉 후 큰 음봉이 감싸면 → 약세 인걸핑."""
        rows = _make_rows([
            (50500, 51000, 50300, 50800, 1000000),  # 작은 양봉
            (51000, 51100, 50200, 50300, 1000000),  # 큰 음봉이 감싸기
        ])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "bearish_engulfing" in names


class TestMorningStar:
    """모닝스타(Morning Star) 패턴 테스트."""

    def test_morning_star_detected(self):
        """큰 음봉 + 작은 몸통(갭다운) + 큰 양봉 → 모닝스타."""
        rows = _make_rows([
            (52000, 52200, 50500, 50600, 1000000),  # 큰 음봉
            (50400, 50500, 50000, 50200, 1000000),  # 작은 몸통 (갭다운)
            (50300, 52000, 50200, 51800, 1000000),  # 큰 양봉
        ])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "morning_star" in names


class TestEveningStar:
    """이브닝스타(Evening Star) 패턴 테스트."""

    def test_evening_star_detected(self):
        """큰 양봉 + 작은 몸통(갭업) + 큰 음봉 → 이브닝스타."""
        rows = _make_rows([
            (50000, 51800, 49800, 51700, 1000000),  # 큰 양봉
            (51800, 52100, 51700, 51900, 1000000),  # 작은 몸통 (갭업)
            (51800, 51900, 50200, 50300, 1000000),  # 큰 음봉
        ])
        result = detect_candlestick_patterns(rows)
        names = [p["name"] for p in result["patterns"]]
        assert "evening_star" in names


class TestCompositeScore:
    """종합 패턴 시그널 점수 테스트."""

    def test_score_range(self):
        """점수는 -100~+100 범위."""
        rows = _make_rows([(50000, 51000, 49000, 50000, 1000000)])
        result = detect_candlestick_patterns(rows)
        assert -100 <= result["score"] <= 100

    def test_bullish_signal(self):
        """강세 패턴이면 signal=bullish, score > 0."""
        rows = _make_rows([
            (51000, 51200, 50500, 50600, 1000000),  # 작은 음봉
            (50400, 51500, 50300, 51400, 1000000),  # 강세 인걸핑
        ])
        result = detect_candlestick_patterns(rows)
        assert result["signal"] == "bullish"
        assert result["score"] > 0

    def test_bearish_signal(self):
        """약세 패턴이면 signal=bearish, score < 0."""
        rows = _make_rows([
            (50500, 51000, 50300, 50800, 1000000),  # 작은 양봉
            (51000, 51100, 50200, 50300, 1000000),  # 약세 인걸핑
        ])
        result = detect_candlestick_patterns(rows)
        assert result["signal"] == "bearish"
        assert result["score"] < 0

    def test_neutral_signal_when_no_pattern(self):
        """패턴이 없으면 signal=neutral, score=0."""
        # 중간 크기 몸통, 적절한 꼬리 → 어떤 패턴에도 해당하지 않음
        rows = _make_rows([
            (50000, 50800, 49500, 50500, 1000000),
            (50500, 51200, 50000, 50800, 1000000),
            (50800, 51500, 50200, 51000, 1000000),
        ])
        result = detect_candlestick_patterns(rows)
        if not result["patterns"]:
            assert result["signal"] == "neutral"
            assert result["score"] == 0

    def test_pattern_has_required_fields(self):
        """각 패턴 딕셔너리에 필수 필드가 포함."""
        rows = _make_rows([(50000, 51000, 49000, 50000, 1000000)])
        result = detect_candlestick_patterns(rows)
        for p in result["patterns"]:
            assert "name" in p
            assert "direction" in p  # bullish / bearish
            assert "weight" in p     # 신뢰도 가중치
