"""기초 기술적 분석 모듈 테스트."""

import pytest

from src.analysis.technical import compute_technical_indicators, _ema, _macd, _obv, _obv_divergence


def _make_rows(prices: list[float], base_volume: int = 1_000_000) -> list[dict]:
    """테스트용 OHLCV rows 생성. close = price, volume = base_volume."""
    rows = []
    for i, p in enumerate(prices):
        rows.append({
            "date": f"2026-01-{i + 1:02d}",
            "open": p,
            "high": p + 100,
            "low": p - 100,
            "close": p,
            "volume": base_volume,
        })
    return rows


class TestMovingAverages:
    """이동평균선 계산 테스트."""

    def test_ma5(self):
        prices = [50000, 51000, 52000, 53000, 54000]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["ma5"] == 52000.0

    def test_ma20(self):
        prices = list(range(50000, 70000, 1000))  # 20개
        result = compute_technical_indicators(_make_rows(prices))
        assert result["ma20"] == sum(prices) / 20

    def test_ma60_insufficient_data(self):
        """60일 미만 데이터면 ma60은 None."""
        prices = [50000] * 30
        result = compute_technical_indicators(_make_rows(prices))
        assert result["ma60"] is None

    def test_ma60_sufficient_data(self):
        prices = [50000 + i * 100 for i in range(60)]
        result = compute_technical_indicators(_make_rows(prices))
        expected = sum(prices) / 60
        assert abs(result["ma60"] - expected) < 0.01


class TestPriceVsMA:
    """현재가 대비 이동평균 위치(%) 테스트."""

    def test_price_above_ma5(self):
        prices = [50000, 51000, 52000, 53000, 56000]
        result = compute_technical_indicators(_make_rows(prices))
        # ma5 = 52400, close = 56000 → (56000-52400)/52400 * 100
        expected = (56000 - 52400) / 52400 * 100
        assert abs(result["price_vs_ma5_pct"] - expected) < 0.01

    def test_price_below_ma20(self):
        prices = [60000 - i * 100 for i in range(20)]  # 하락 추세
        result = compute_technical_indicators(_make_rows(prices))
        assert result["price_vs_ma20_pct"] < 0  # 현재가가 MA20 아래


class TestPriceChange:
    """가격 변동률 테스트."""

    def test_change_1d(self):
        prices = [50000, 51000]
        result = compute_technical_indicators(_make_rows(prices))
        assert abs(result["change_1d_pct"] - 2.0) < 0.01

    def test_change_5d(self):
        prices = [50000, 51000, 52000, 53000, 54000, 55000]
        result = compute_technical_indicators(_make_rows(prices))
        # 5일전 close=50000, 현재 close=55000 → 10%
        assert abs(result["change_5d_pct"] - 10.0) < 0.01

    def test_change_20d_insufficient(self):
        prices = [50000] * 10
        result = compute_technical_indicators(_make_rows(prices))
        assert result["change_20d_pct"] is None


class TestVolumeChange:
    """거래량 변화율 테스트."""

    def test_volume_ratio_equal(self):
        """5일 평균과 동일 거래량이면 ratio = 1.0."""
        rows = _make_rows([50000] * 6, base_volume=1_000_000)
        result = compute_technical_indicators(rows)
        assert abs(result["volume_ratio_5d"] - 1.0) < 0.01

    def test_volume_spike(self):
        """당일 거래량이 5일 평균의 2배."""
        rows = _make_rows([50000] * 6, base_volume=1_000_000)
        rows[-1]["volume"] = 2_000_000  # 당일만 2배
        result = compute_technical_indicators(rows)
        assert abs(result["volume_ratio_5d"] - 2.0) < 0.01

    def test_insufficient_data(self):
        """데이터 1개면 volume_ratio_5d는 None."""
        rows = _make_rows([50000])
        result = compute_technical_indicators(rows)
        assert result["volume_ratio_5d"] is None


class TestRSI:
    """RSI(상대강도지수) 계산 테스트."""

    def test_rsi_normal(self):
        """14일 이상 데이터로 정상 RSI 계산."""
        # 상승·하락 혼재 20일 데이터
        prices = [50000 + (i % 3 - 1) * 500 + i * 100 for i in range(20)]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["rsi_14"] is not None
        assert 0 <= result["rsi_14"] <= 100

    def test_rsi_insufficient_data(self):
        """14일 미만 데이터면 RSI는 None."""
        prices = [50000 + i * 100 for i in range(10)]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["rsi_14"] is None

    def test_rsi_all_up(self):
        """전부 상승이면 RSI ≈ 100."""
        prices = [50000 + i * 100 for i in range(20)]  # 매일 +100
        result = compute_technical_indicators(_make_rows(prices))
        assert result["rsi_14"] is not None
        assert result["rsi_14"] > 99

    def test_rsi_all_down(self):
        """전부 하락이면 RSI ≈ 0."""
        prices = [60000 - i * 100 for i in range(20)]  # 매일 -100
        result = compute_technical_indicators(_make_rows(prices))
        assert result["rsi_14"] is not None
        assert result["rsi_14"] < 1

    def test_rsi_half_and_half(self):
        """상승·하락 반반이면 RSI ≈ 50."""
        # 교대로 +500, -500
        prices = [50000]
        for i in range(19):
            delta = 500 if i % 2 == 0 else -500
            prices.append(prices[-1] + delta)
        result = compute_technical_indicators(_make_rows(prices))
        assert result["rsi_14"] is not None
        assert 40 <= result["rsi_14"] <= 60


class TestEMA:
    """지수이동평균(EMA) 계산 정확성 테스트."""

    def test_ema_basic(self):
        """간단한 EMA 계산."""
        closes = [10.0, 11.0, 12.0, 13.0, 14.0]
        result = _ema(closes, 3)
        # EMA3: 첫 SMA = (10+11+12)/3 = 11.0
        # k = 2/4 = 0.5
        # EMA[3] = 13*0.5 + 11.0*0.5 = 12.0
        # EMA[4] = 14*0.5 + 12.0*0.5 = 13.0
        assert len(result) == 5
        assert abs(result[-1] - 13.0) < 0.01

    def test_ema_insufficient_data(self):
        """데이터가 window 미만이면 빈 리스트."""
        result = _ema([10.0, 11.0], 5)
        assert result == []


class TestMACD:
    """MACD(12,26,9) 계산 테스트."""

    def test_macd_with_sufficient_data(self):
        """26일 이상 데이터로 MACD 계산."""
        prices = [50000 + i * 100 for i in range(35)]
        macd_line, signal_line, histogram = _macd(prices)
        assert macd_line is not None
        assert signal_line is not None
        assert histogram is not None

    def test_macd_insufficient_data(self):
        """26일 미만 데이터면 모두 None."""
        prices = [50000 + i * 100 for i in range(20)]
        macd_line, signal_line, histogram = _macd(prices)
        assert macd_line is None
        assert signal_line is None
        assert histogram is None

    def test_macd_signal_insufficient(self):
        """26일 이상이지만 시그널(9일) 계산 불가 시 signal=None."""
        # 정확히 26일: MACD 값 1개뿐이라 시그널 EMA9 불가
        prices = [50000 + i * 100 for i in range(26)]
        macd_line, signal_line, histogram = _macd(prices)
        assert macd_line is not None
        assert signal_line is None
        assert histogram is None

    def test_macd_golden_cross(self):
        """상승 추세에서 MACD > Signal (골든크로스)."""
        # 급상승 추세 → MACD가 시그널 위
        prices = [50000] * 30 + [50000 + i * 500 for i in range(1, 16)]
        macd_line, signal_line, histogram = _macd(prices)
        if signal_line is not None:
            assert histogram > 0  # MACD > Signal

    def test_macd_dead_cross(self):
        """하락 추세에서 MACD < Signal (데드크로스)."""
        prices = [60000] * 30 + [60000 - i * 500 for i in range(1, 16)]
        macd_line, signal_line, histogram = _macd(prices)
        if signal_line is not None:
            assert histogram < 0  # MACD < Signal

    def test_macd_histogram_sign(self):
        """히스토그램 = MACD - Signal."""
        prices = [50000 + i * 100 for i in range(45)]
        macd_line, signal_line, histogram = _macd(prices)
        if signal_line is not None:
            assert abs(histogram - (macd_line - signal_line)) < 0.01

    def test_compute_indicators_includes_macd(self):
        """compute_technical_indicators에 MACD 키가 포함된다."""
        prices = [50000 + i * 100 for i in range(45)]
        result = compute_technical_indicators(_make_rows(prices))
        assert "macd" in result
        assert "macd_signal" in result
        assert "macd_histogram" in result

    def test_compute_indicators_macd_none_insufficient(self):
        """데이터 부족 시 MACD 키는 None."""
        prices = [50000] * 10
        result = compute_technical_indicators(_make_rows(prices))
        assert result["macd"] is None
        assert result["macd_signal"] is None
        assert result["macd_histogram"] is None


class TestBollingerBands:
    """볼린저 밴드(20,2) 계산 테스트."""

    def test_bb_keys_present(self):
        """20일 이상 데이터면 BB 키가 모두 존재."""
        prices = [50000 + i * 100 for i in range(25)]
        result = compute_technical_indicators(_make_rows(prices))
        assert "bb_upper" in result
        assert "bb_lower" in result
        assert "bb_width" in result
        assert "bb_pctb" in result

    def test_bb_none_insufficient_data(self):
        """20일 미만 데이터면 BB 키는 모두 None."""
        prices = [50000] * 10
        result = compute_technical_indicators(_make_rows(prices))
        assert result["bb_upper"] is None
        assert result["bb_lower"] is None
        assert result["bb_width"] is None
        assert result["bb_pctb"] is None

    def test_bb_upper_above_lower(self):
        """상단 밴드는 항상 하단 밴드 위."""
        prices = [50000 + (i % 5 - 2) * 300 for i in range(25)]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["bb_upper"] > result["bb_lower"]

    def test_bb_width_positive(self):
        """밴드폭은 양수."""
        prices = [50000 + (i % 5 - 2) * 300 for i in range(25)]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["bb_width"] > 0

    def test_bb_pctb_middle(self):
        """종가가 MA20과 같으면 %B ≈ 0.5."""
        # 모든 가격이 같으면 σ=0이라 나눗셈 에러 → 약간의 변동 필요
        # 대신 대칭 데이터로 마지막 값이 평균에 오도록 설계
        prices = [50000] * 20
        result = compute_technical_indicators(_make_rows(prices))
        # 모든 값이 같으면 σ=0 → %B=0.5 (특수 처리)
        assert result["bb_pctb"] == 0.5

    def test_bb_pctb_above_one(self):
        """종가가 상단 밴드 위면 %B > 1.0."""
        # 안정적인 가격 후 급등
        prices = [50000] * 19 + [60000]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["bb_pctb"] > 1.0

    def test_bb_pctb_below_zero(self):
        """종가가 하단 밴드 아래면 %B < 0."""
        # 안정적인 가격 후 급락
        prices = [50000] * 19 + [40000]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["bb_pctb"] < 0

    def test_bb_formula_correctness(self):
        """BB 공식 검증: upper = ma20 + 2σ, lower = ma20 - 2σ."""
        prices = [50000 + i * 100 for i in range(20)]
        result = compute_technical_indicators(_make_rows(prices))
        ma20 = result["ma20"]
        # 수동 계산
        mean = sum(prices) / 20
        variance = sum((p - mean) ** 2 for p in prices) / 20
        std = variance ** 0.5
        assert abs(result["bb_upper"] - (ma20 + 2 * std)) < 0.01
        assert abs(result["bb_lower"] - (ma20 - 2 * std)) < 0.01


class TestOBV:
    """OBV(On-Balance Volume) 계산 테스트."""

    def test_obv_basic(self):
        """상승일 +volume, 하락일 -volume, 보합 ±0."""
        closes = [100, 110, 105, 105, 120]
        volumes = [1000, 2000, 1500, 1000, 3000]
        obv = _obv(closes, volumes)
        # day0: 0 (시작)
        # day1: 110>100 → +2000 = 2000
        # day2: 105<110 → -1500 = 500
        # day3: 105==105 → +0 = 500
        # day4: 120>105 → +3000 = 3500
        assert obv == [0, 2000, 500, 500, 3500]

    def test_obv_all_up(self):
        """매일 상승이면 OBV = 누적 거래량."""
        closes = [100, 110, 120, 130]
        volumes = [1000, 1000, 1000, 1000]
        obv = _obv(closes, volumes)
        assert obv == [0, 1000, 2000, 3000]

    def test_obv_all_down(self):
        """매일 하락이면 OBV = 음수 누적."""
        closes = [130, 120, 110, 100]
        volumes = [1000, 1000, 1000, 1000]
        obv = _obv(closes, volumes)
        assert obv == [0, -1000, -2000, -3000]

    def test_obv_single_point(self):
        """데이터 1개면 OBV = [0]."""
        assert _obv([100], [1000]) == [0]

    def test_obv_empty(self):
        """빈 데이터면 빈 리스트."""
        assert _obv([], []) == []


class TestOBVDivergence:
    """가격-OBV 다이버전스 감지 테스트."""

    def test_bearish_divergence(self):
        """가격 상승 + OBV 하락 = 약세 다이버전스."""
        # 가격은 고점 갱신하지만 OBV는 하락
        # 최근 구간: 가격 상승 추세, OBV 하락 추세
        closes_rising = [100 + i for i in range(25)]
        # OBV가 하락하려면: 상승일 거래량 < 하락일 거래량이어야 하지만
        # 가격이 계속 오르므로 OBV도 오름 → 직접 OBV 리스트로 테스트
        obv_falling = list(range(3000, 3000 - 25, -1))  # 3000, 2999, ...
        result = _obv_divergence(closes_rising, obv_falling, window=20)
        assert result == "bearish"

    def test_bullish_divergence(self):
        """가격 하락 + OBV 상승 = 강세 다이버전스."""
        closes_falling = [200 - i for i in range(25)]
        obv_rising = list(range(0, 25))
        result = _obv_divergence(closes_falling, obv_rising, window=20)
        assert result == "bullish"

    def test_no_divergence_both_up(self):
        """가격·OBV 모두 상승 = 다이버전스 없음."""
        closes_up = [100 + i for i in range(25)]
        obv_up = [i * 100 for i in range(25)]
        result = _obv_divergence(closes_up, obv_up, window=20)
        assert result is None

    def test_no_divergence_both_down(self):
        """가격·OBV 모두 하락 = 다이버전스 없음."""
        closes_down = [200 - i for i in range(25)]
        obv_down = [2400 - i * 100 for i in range(25)]
        result = _obv_divergence(closes_down, obv_down, window=20)
        assert result is None

    def test_insufficient_data(self):
        """데이터 부족 시 None."""
        result = _obv_divergence([100, 110], [0, 1000], window=20)
        assert result is None


class TestOBVIntegration:
    """compute_technical_indicators에 OBV 필드 통합 테스트."""

    def test_obv_keys_present(self):
        """충분한 데이터일 때 obv, obv_ma20, obv_divergence 키 존재."""
        prices = [50000 + i * 100 for i in range(30)]
        result = compute_technical_indicators(_make_rows(prices))
        assert "obv" in result
        assert "obv_ma20" in result
        assert "obv_divergence" in result

    def test_obv_value_is_latest(self):
        """obv는 최신 OBV 값."""
        prices = [50000 + i * 100 for i in range(10)]
        rows = _make_rows(prices)
        result = compute_technical_indicators(rows)
        assert result["obv"] is not None
        assert isinstance(result["obv"], (int, float))

    def test_obv_ma20_none_insufficient(self):
        """20일 미만 데이터면 obv_ma20은 None."""
        prices = [50000] * 10
        result = compute_technical_indicators(_make_rows(prices))
        assert result["obv_ma20"] is None

    def test_obv_ma20_present(self):
        """20일 이상 데이터면 obv_ma20 계산됨."""
        prices = [50000 + i * 100 for i in range(25)]
        result = compute_technical_indicators(_make_rows(prices))
        assert result["obv_ma20"] is not None

    def test_obv_divergence_none_short_data(self):
        """데이터 짧으면 다이버전스 None."""
        prices = [50000] * 5
        result = compute_technical_indicators(_make_rows(prices))
        assert result["obv_divergence"] is None


class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_empty_input(self):
        with pytest.raises(ValueError):
            compute_technical_indicators([])

    def test_single_row(self):
        result = compute_technical_indicators(_make_rows([50000]))
        assert result["ma5"] is None
        assert result["change_1d_pct"] is None

    def test_result_has_current_price(self):
        result = compute_technical_indicators(_make_rows([50000, 51000]))
        assert result["current_price"] == 51000
        assert result["current_date"] == "2026-01-02"
