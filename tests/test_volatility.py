"""변동성 분석 모듈 테스트."""

import math

import pytest

from src.analysis.volatility import compute_volatility


def _make_rows(prices: list[float], base_volume: int = 1_000_000) -> list[dict]:
    """테스트용 OHLCV rows 생성. close = price, high = price+100, low = price-100."""
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


class TestATR:
    """ATR(14) 계산 테스트."""

    def test_atr_basic(self):
        """14일 이상 데이터로 ATR 계산."""
        prices = [50000 + i * 100 for i in range(20)]
        result = compute_volatility(_make_rows(prices))
        assert result["atr"] is not None
        assert result["atr"] > 0

    def test_atr_flat_price(self):
        """가격이 일정하면 ATR = high - low = 200 (전일종가-당일고/저 차이도 200)."""
        prices = [50000] * 20
        rows = _make_rows(prices)
        result = compute_volatility(rows)
        # True Range: max(H-L, |H-prev_C|, |prev_C-L|)
        # H-L=200, |H-prev_C|=100, |prev_C-L|=100 → TR=200
        assert abs(result["atr"] - 200.0) < 0.01

    def test_atr_pct(self):
        """ATR 백분율 = ATR / 종가 * 100."""
        prices = [50000] * 20
        result = compute_volatility(_make_rows(prices))
        expected_pct = result["atr"] / prices[-1] * 100
        assert abs(result["atr_pct"] - expected_pct) < 0.01

    def test_atr_insufficient_data(self):
        """14일 미만 데이터면 ATR은 None."""
        prices = [50000] * 10
        result = compute_volatility(_make_rows(prices))
        assert result["atr"] is None
        assert result["atr_pct"] is None

    def test_atr_true_range_uses_prev_close(self):
        """갭이 있으면 True Range가 H-L보다 커진다."""
        # 전일 종가 50000, 당일 갭업 52000 (high=52100, low=51900)
        rows = _make_rows([50000] * 14)
        rows[-1] = {
            "date": "2026-01-14",
            "open": 52000, "high": 52100, "low": 51900,
            "close": 52000, "volume": 1_000_000,
        }
        result = compute_volatility(rows)
        # TR of last day: max(52100-51900=200, |52100-50000|=2100, |50000-51900|=1900) = 2100
        # ATR(14)는 이전 13일 TR=200과 마지막 TR=2100의 평균
        assert result["atr"] > 200  # 갭으로 인해 평균 TR 증가


class TestHistoricalVolatility:
    """역사적 변동성(HV20) 테스트."""

    def test_hv20_basic(self):
        """20일 이상 데이터로 HV20 계산."""
        prices = [50000 + i * 100 for i in range(25)]
        result = compute_volatility(_make_rows(prices))
        assert result["hv20"] is not None
        assert result["hv20"] > 0

    def test_hv20_flat_price(self):
        """가격 동일하면 HV20 = 0."""
        prices = [50000] * 25
        result = compute_volatility(_make_rows(prices))
        assert result["hv20"] == 0.0

    def test_hv20_insufficient_data(self):
        """21일 미만 데이터면 HV20은 None (로그수익률 20개 필요)."""
        prices = [50000 + i * 100 for i in range(15)]
        result = compute_volatility(_make_rows(prices))
        assert result["hv20"] is None

    def test_hv20_annualized(self):
        """HV20은 연율화(× sqrt(252))."""
        # 교대로 +1%, -1% 변동 → 일일 로그수익률 std ≈ |log(1.01)| ≈ 0.00995
        prices = [50000.0]
        for i in range(24):
            factor = 1.01 if i % 2 == 0 else 0.99
            prices.append(prices[-1] * factor)
        result = compute_volatility(_make_rows(prices))
        assert result["hv20"] is not None
        daily_std = abs(math.log(1.01))  # ≈ 0.00995
        expected_hv = daily_std * math.sqrt(252)
        assert abs(result["hv20"] - expected_hv) < 0.02


class TestVolatilityPercentile:
    """변동성 백분위 테스트."""

    def test_percentile_basic(self):
        """60일 이상 데이터로 백분위 계산."""
        # ATR(14) 계산에 14일 + 60일 window = 최소 74일
        prices = [50000 + i * 50 for i in range(80)]
        result = compute_volatility(_make_rows(prices))
        assert result["volatility_percentile"] is not None
        assert 0 <= result["volatility_percentile"] <= 100

    def test_percentile_insufficient_data(self):
        """데이터 부족 시 None."""
        prices = [50000] * 20
        result = compute_volatility(_make_rows(prices))
        assert result["volatility_percentile"] is None

    def test_percentile_high_after_spike(self):
        """변동성 급등 후 백분위가 높다."""
        # 안정적인 가격 후 마지막에 큰 변동
        prices = [50000] * 75
        # 마지막 몇 일 큰 변동
        for i in range(5):
            prices.append(50000 + ((-1) ** i) * 3000)
        rows = _make_rows(prices)
        # 마지막 일들의 high/low를 극단적으로 설정
        for i in range(-5, 0):
            rows[i]["high"] = rows[i]["close"] + 3000
            rows[i]["low"] = rows[i]["close"] - 3000
        result = compute_volatility(rows)
        if result["volatility_percentile"] is not None:
            assert result["volatility_percentile"] > 50


class TestVolatilityRegime:
    """변동성 체제 판정 테스트."""

    def test_regime_keys(self):
        """결과에 volatility_regime 키 존재."""
        prices = [50000] * 80
        result = compute_volatility(_make_rows(prices))
        assert "volatility_regime" in result

    def test_regime_values(self):
        """체제는 고변동성/저변동성/보통 중 하나 또는 None."""
        prices = [50000] * 80
        result = compute_volatility(_make_rows(prices))
        assert result["volatility_regime"] in ("고변동성", "저변동성", "보통", None)

    def test_regime_none_insufficient(self):
        """데이터 부족 시 None."""
        prices = [50000] * 10
        result = compute_volatility(_make_rows(prices))
        assert result["volatility_regime"] is None


class TestBandwidthSqueeze:
    """볼린저 밴드폭 수축 감지 테스트."""

    def test_squeeze_keys(self):
        """결과에 bandwidth_squeeze 키 존재."""
        prices = [50000] * 80
        result = compute_volatility(_make_rows(prices))
        assert "bandwidth_squeeze" in result

    def test_squeeze_after_contraction(self):
        """변동 감소 → bandwidth 축소 → squeeze = True."""
        # 큰 변동 후 좁은 변동
        prices = []
        for i in range(40):
            prices.append(50000 + ((-1) ** i) * 2000)  # 큰 변동
        for i in range(40):
            prices.append(50000 + ((-1) ** i) * 50)  # 작은 변동
        rows = _make_rows(prices)
        # high/low도 변동에 맞게
        for i in range(40):
            rows[i]["high"] = rows[i]["close"] + 2000
            rows[i]["low"] = rows[i]["close"] - 2000
        for i in range(40, 80):
            rows[i]["high"] = rows[i]["close"] + 50
            rows[i]["low"] = rows[i]["close"] - 50
        result = compute_volatility(rows)
        assert result["bandwidth_squeeze"] is True

    def test_no_squeeze_after_expansion(self):
        """변동 확대 → squeeze = False."""
        # 좁은 변동 후 큰 변동
        prices = []
        for i in range(40):
            prices.append(50000 + ((-1) ** i) * 50)
        for i in range(40):
            prices.append(50000 + ((-1) ** i) * 2000)
        rows = _make_rows(prices)
        for i in range(40):
            rows[i]["high"] = rows[i]["close"] + 50
            rows[i]["low"] = rows[i]["close"] - 50
        for i in range(40, 80):
            rows[i]["high"] = rows[i]["close"] + 2000
            rows[i]["low"] = rows[i]["close"] - 2000
        result = compute_volatility(rows)
        assert result["bandwidth_squeeze"] is False

    def test_squeeze_none_insufficient(self):
        """데이터 부족 시 None."""
        prices = [50000] * 10
        result = compute_volatility(_make_rows(prices))
        assert result["bandwidth_squeeze"] is None


class TestComputeVolatility:
    """compute_volatility 전체 반환값 테스트."""

    def test_all_keys_present(self):
        """모든 키가 결과에 존재."""
        prices = [50000 + i * 50 for i in range(80)]
        result = compute_volatility(_make_rows(prices))
        expected_keys = {
            "atr", "atr_pct", "hv20",
            "volatility_percentile", "volatility_regime",
            "bandwidth_squeeze",
        }
        assert expected_keys.issubset(result.keys())

    def test_empty_input(self):
        """빈 입력 시 ValueError."""
        with pytest.raises(ValueError):
            compute_volatility([])

    def test_single_row(self):
        """데이터 1개면 모두 None."""
        result = compute_volatility(_make_rows([50000]))
        assert result["atr"] is None
        assert result["hv20"] is None
        assert result["volatility_percentile"] is None
        assert result["volatility_regime"] is None
        assert result["bandwidth_squeeze"] is None
