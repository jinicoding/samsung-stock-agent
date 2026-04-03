"""핵심 관찰 포인트(Key Watchpoints) 모듈 테스트."""

import pytest

from src.analysis.watchpoints import (
    compute_scenario_levels,
    compute_daily_range,
    extract_risk_opportunity_factors,
    build_watchpoints,
)


# ── 헬퍼 ──────────────────────────────────────────────


def _make_rows(prices, base_volume=1_000_000):
    """테스트용 OHLCV 행 생성."""
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


# ── compute_scenario_levels ──────────────────────────


class TestScenarioLevels:
    """지지/저항선 기반 상승·하락 시나리오 테스트."""

    def test_basic_scenario(self):
        """가장 가까운 지지/저항 이탈 시 다음 레벨 제시."""
        sr = {
            "nearest_support": 55000,
            "nearest_resistance": 58000,
            "pivot": {"s1": 54000, "s2": 53200, "r1": 58000, "r2": 59500},
            "swing_levels": [
                {"type": "support", "price": 53200, "date": "2026-01-05"},
                {"type": "resistance", "price": 59500, "date": "2026-01-10"},
            ],
            "ma_levels": {"ma20": 56000, "ma60": 54500},
        }
        result = compute_scenario_levels(sr, current_price=56500)
        assert result["nearest_support"] == 55000
        assert result["nearest_resistance"] == 58000
        # 지지 이탈 시 다음 지지 목표가 있어야 함
        assert result["next_support"] is not None
        assert result["next_support"] < 55000
        # 저항 돌파 시 다음 저항 목표가 있어야 함
        assert result["next_resistance"] is not None
        assert result["next_resistance"] > 58000

    def test_no_support_resistance(self):
        """지지/저항 데이터 없을 때 None 반환."""
        sr = {
            "nearest_support": None,
            "nearest_resistance": None,
            "pivot": {"s1": None, "s2": None, "r1": None, "r2": None},
            "swing_levels": [],
            "ma_levels": {"ma20": None, "ma60": None},
        }
        result = compute_scenario_levels(sr, current_price=56500)
        assert result["nearest_support"] is None
        assert result["nearest_resistance"] is None
        assert result["next_support"] is None
        assert result["next_resistance"] is None

    def test_only_one_support_level(self):
        """지지선이 하나만 있을 때 next_support는 None."""
        sr = {
            "nearest_support": 55000,
            "nearest_resistance": 58000,
            "pivot": {"s1": None, "s2": None, "r1": None, "r2": None},
            "swing_levels": [],
            "ma_levels": {"ma20": None, "ma60": None},
        }
        result = compute_scenario_levels(sr, current_price=56500)
        assert result["nearest_support"] == 55000
        assert result["next_support"] is None


# ── compute_daily_range ──────────────────────────────


class TestDailyRange:
    """ATR 기반 예상 일일 변동 범위 테스트."""

    def test_basic_range(self):
        """ATR이 있을 때 예상 고/저 범위 계산."""
        vol = {"atr": 1500.0, "atr_pct": 2.5}
        result = compute_daily_range(current_price=60000, volatility=vol)
        assert result["expected_high"] == 61500  # 60000 + 1500
        assert result["expected_low"] == 58500   # 60000 - 1500
        assert result["atr"] == 1500.0
        assert result["atr_pct"] == 2.5

    def test_none_volatility(self):
        """변동성 데이터 없을 때 모두 None."""
        result = compute_daily_range(current_price=60000, volatility=None)
        assert result["expected_high"] is None
        assert result["expected_low"] is None

    def test_none_atr(self):
        """ATR이 None일 때 모두 None."""
        vol = {"atr": None, "atr_pct": None}
        result = compute_daily_range(current_price=60000, volatility=vol)
        assert result["expected_high"] is None
        assert result["expected_low"] is None


# ── extract_risk_opportunity_factors ─────────────────


class TestRiskOpportunityFactors:
    """핵심 리스크/기회 요인 추출 테스트."""

    def test_high_volatility_factor(self):
        """고변동성 체제일 때 리스크 요인으로 포함."""
        factors = extract_risk_opportunity_factors(
            volatility={"volatility_regime": "고변동성", "bandwidth_squeeze": False},
        )
        risk_texts = [f["text"] for f in factors if f["type"] == "risk"]
        assert any("고변동성" in t for t in risk_texts)

    def test_bandwidth_squeeze_factor(self):
        """밴드폭 수축 시 기회 요인으로 포함."""
        factors = extract_risk_opportunity_factors(
            volatility={"volatility_regime": "저변동성", "bandwidth_squeeze": True},
        )
        opp_texts = [f["text"] for f in factors if f["type"] == "opportunity"]
        assert any("수축" in t or "변동성 확대" in t for t in opp_texts)

    def test_trend_reversal_bullish(self):
        """강세 전환 감지 시 기회 요인."""
        factors = extract_risk_opportunity_factors(
            trend_reversal={"convergence": "strong", "direction": "bullish"},
        )
        opp_texts = [f["text"] for f in factors if f["type"] == "opportunity"]
        assert any("강세" in t or "전환" in t for t in opp_texts)

    def test_trend_reversal_bearish(self):
        """약세 전환 감지 시 리스크 요인."""
        factors = extract_risk_opportunity_factors(
            trend_reversal={"convergence": "strong", "direction": "bearish"},
        )
        risk_texts = [f["text"] for f in factors if f["type"] == "risk"]
        assert any("약세" in t or "전환" in t for t in risk_texts)

    def test_supply_demand_buy(self):
        """수급 매수 우세 시 기회 요인."""
        factors = extract_risk_opportunity_factors(
            supply_demand={"overall_judgment": "buy_dominant", "foreign_consecutive_net_buy": 5},
        )
        opp_texts = [f["text"] for f in factors if f["type"] == "opportunity"]
        assert any("매수" in t or "수급" in t for t in opp_texts)

    def test_supply_demand_sell(self):
        """수급 매도 우세 시 리스크 요인."""
        factors = extract_risk_opportunity_factors(
            supply_demand={"overall_judgment": "sell_dominant", "foreign_consecutive_net_sell": 4},
        )
        risk_texts = [f["text"] for f in factors if f["type"] == "risk"]
        assert any("매도" in t or "수급" in t for t in risk_texts)

    def test_no_data_returns_empty(self):
        """데이터가 없으면 빈 리스트."""
        factors = extract_risk_opportunity_factors()
        assert factors == []

    def test_max_factors_limit(self):
        """최대 3개 요인만 반환."""
        factors = extract_risk_opportunity_factors(
            volatility={"volatility_regime": "고변동성", "bandwidth_squeeze": True},
            trend_reversal={"convergence": "strong", "direction": "bearish"},
            supply_demand={"overall_judgment": "sell_dominant", "foreign_consecutive_net_sell": 5},
            news_sentiment={"overall": "bearish"},
        )
        assert len(factors) <= 3


# ── build_watchpoints (통합) ─────────────────────────


class TestBuildWatchpoints:
    """build_watchpoints 통합 테스트."""

    def test_full_watchpoints(self):
        """모든 데이터가 있을 때 완전한 watchpoints dict 반환."""
        sr = {
            "nearest_support": 55000,
            "nearest_resistance": 58000,
            "pivot": {"s1": 54000, "s2": 53200, "r1": 58000, "r2": 59500},
            "swing_levels": [],
            "ma_levels": {"ma20": 56000, "ma60": 54500},
        }
        vol = {"atr": 1500.0, "atr_pct": 2.5, "volatility_regime": "보통", "bandwidth_squeeze": False}
        result = build_watchpoints(
            current_price=56500,
            support_resistance=sr,
            volatility=vol,
        )
        assert "scenarios" in result
        assert "daily_range" in result
        assert "factors" in result

    def test_minimal_watchpoints(self):
        """최소 데이터(current_price만)로도 에러 없이 반환."""
        result = build_watchpoints(current_price=56500)
        assert "scenarios" in result
        assert "daily_range" in result
        assert "factors" in result

    def test_none_sr_and_vol(self):
        """sr, vol이 None이어도 정상 동작."""
        result = build_watchpoints(
            current_price=56500,
            support_resistance=None,
            volatility=None,
        )
        assert result["scenarios"]["nearest_support"] is None
        assert result["daily_range"]["expected_high"] is None
        assert result["factors"] == []
