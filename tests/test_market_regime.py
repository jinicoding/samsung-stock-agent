"""시장 체제(Market Regime) 인식 모듈 테스트."""

from unittest.mock import patch

from src.analysis.market_regime import compute_market_regime


def _make_row(date: str, open_: float, high: float, low: float,
              close: float, volume: int) -> dict:
    return {
        "date": date, "open": open_, "high": high,
        "low": low, "close": close, "volume": volume,
    }


def _generate_trending_up(n: int = 60) -> list[dict]:
    """꾸준히 상승하는 60일 데이터 (정배열, 높은 ADX)."""
    rows = []
    base = 50000
    for i in range(n):
        c = base + i * 200
        rows.append(_make_row(
            f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
            c - 100, c + 150, c - 200, c, 1000000 + i * 10000,
        ))
    return rows


def _generate_trending_down(n: int = 60) -> list[dict]:
    """꾸준히 하락하는 60일 데이터 (역배열, 높은 ADX)."""
    rows = []
    base = 70000
    for i in range(n):
        c = base - i * 200
        rows.append(_make_row(
            f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
            c + 100, c + 200, c - 150, c, 1000000 + i * 10000,
        ))
    return rows


def _generate_range_bound(n: int = 60) -> list[dict]:
    """횡보장 데이터 — 좁은 범위에서 진동."""
    rows = []
    base = 55000
    for i in range(n):
        offset = 300 * (1 if i % 2 == 0 else -1)
        c = base + offset
        rows.append(_make_row(
            f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
            c - 50, c + 100, c - 100, c, 800000,
        ))
    return rows


def _generate_breakout(n: int = 60) -> list[dict]:
    """횡보 후 상단 돌파 — 마지막 15일 강한 상승 + 거래량 폭증."""
    rows = []
    base = 55000
    for i in range(n - 15):
        offset = 100 * (1 if i % 2 == 0 else -1)
        c = base + offset
        rows.append(_make_row(
            f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
            c - 50, c + 80, c - 80, c, 800000,
        ))
    for i in range(15):
        c = base + 1000 + i * 400
        rows.append(_make_row(
            f"2026-03-{i + 1:02d}",
            c - 100, c + 300, c - 50, c, 3000000 + i * 300000,
        ))
    return rows


class TestComputeMarketRegime:

    @patch("src.analysis.market_regime.get_prices")
    def test_insufficient_data_returns_none(self, mock_prices):
        mock_prices.return_value = [_make_row("2026-01-01", 50000, 51000, 49000, 50500, 1000000)]
        result = compute_market_regime()
        assert result is None

    @patch("src.analysis.market_regime.get_prices")
    def test_trending_up(self, mock_prices):
        mock_prices.return_value = _generate_trending_up()
        result = compute_market_regime()
        assert result is not None
        assert result["regime"] in ("trending_up", "breakout")
        assert result["phase"] in ("markup", "accumulation")
        assert 0 <= result["confidence"] <= 100
        assert result["duration"] >= 1
        assert "interpretation_hints" in result

    @patch("src.analysis.market_regime.get_prices")
    def test_trending_down(self, mock_prices):
        mock_prices.return_value = _generate_trending_down()
        result = compute_market_regime()
        assert result is not None
        assert result["regime"] in ("trending_down", "breakdown")
        assert result["phase"] in ("markdown", "distribution")

    @patch("src.analysis.market_regime.get_prices")
    def test_range_bound(self, mock_prices):
        mock_prices.return_value = _generate_range_bound()
        result = compute_market_regime()
        assert result is not None
        assert result["regime"] == "range_bound"
        assert result["confidence"] >= 0

    @patch("src.analysis.market_regime.get_prices")
    def test_breakout(self, mock_prices):
        mock_prices.return_value = _generate_breakout()
        result = compute_market_regime()
        assert result is not None
        assert result["regime"] in ("breakout", "trending_up")

    @patch("src.analysis.market_regime.get_prices")
    def test_output_structure(self, mock_prices):
        mock_prices.return_value = _generate_trending_up()
        result = compute_market_regime()
        assert result is not None
        required_keys = {"regime", "phase", "confidence", "duration", "interpretation_hints"}
        assert required_keys.issubset(result.keys())
        assert result["regime"] in (
            "trending_up", "trending_down", "range_bound", "breakout", "breakdown",
        )
        assert result["phase"] in (
            "accumulation", "markup", "distribution", "markdown",
        )
        hints = result["interpretation_hints"]
        assert "rsi_thresholds" in hints
        assert "support_resistance_reliability" in hints

    @patch("src.analysis.market_regime.get_prices")
    def test_interpretation_hints_trending(self, mock_prices):
        mock_prices.return_value = _generate_trending_up()
        result = compute_market_regime()
        assert result is not None
        hints = result["interpretation_hints"]
        if result["regime"] == "trending_up":
            assert hints["rsi_thresholds"]["overbought"] >= 75

    @patch("src.analysis.market_regime.get_prices")
    def test_interpretation_hints_range(self, mock_prices):
        mock_prices.return_value = _generate_range_bound()
        result = compute_market_regime()
        assert result is not None
        hints = result["interpretation_hints"]
        if result["regime"] == "range_bound":
            assert hints["rsi_thresholds"]["overbought"] <= 75
            assert hints["support_resistance_reliability"] in ("high", "very_high")
