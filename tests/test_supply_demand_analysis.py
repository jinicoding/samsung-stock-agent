"""수급 분석 모듈 테스트."""

import pytest

from src.analysis.supply_demand import analyze_supply_demand


def _make_trading_rows(
    foreign_vals: list[int],
    institution_vals: list[int] | None = None,
) -> list[dict]:
    """테스트용 foreign_trading rows 생성.

    Args:
        foreign_vals: 외국인 순매수 값 리스트 (날짜 오름차순).
        institution_vals: 기관 순매수 값 리스트. None이면 foreign의 부호 반전.
    """
    if institution_vals is None:
        institution_vals = [-v for v in foreign_vals]
    rows = []
    for i, (f, inst) in enumerate(zip(foreign_vals, institution_vals)):
        rows.append({
            "date": f"2026-03-{i + 1:02d}",
            "institution": inst,
            "foreign_total": f,
            "individual": -(f + inst),
            "other_corp": 0,
        })
    return rows


def _make_ownership_rows(pcts: list[float], base_shares: int = 3_000_000_000) -> list[dict]:
    """테스트용 foreign_ownership rows 생성."""
    rows = []
    for i, pct in enumerate(pcts):
        rows.append({
            "date": f"2026-03-{i + 1:02d}",
            "ownership_pct": pct,
            "foreign_shares": int(base_shares * pct / 100),
            "listed_shares": base_shares,
            "limit_shares": base_shares,
            "exhaustion_pct": pct,
        })
    return rows


class TestConsecutiveDays:
    """외국인/기관 연속 순매수/순매도 카운트 테스트."""

    def test_foreign_consecutive_buy(self):
        """외국인 5일 연속 순매수."""
        trading = _make_trading_rows([100, 200, 300, 400, 500])
        result = analyze_supply_demand(trading, [])
        assert result["foreign_consecutive_net_buy"] == 5
        assert result["foreign_consecutive_net_sell"] == 0

    def test_foreign_consecutive_sell(self):
        """외국인 3일 연속 순매도."""
        trading = _make_trading_rows([-100, -200, -300])
        result = analyze_supply_demand(trading, [])
        assert result["foreign_consecutive_net_buy"] == 0
        assert result["foreign_consecutive_net_sell"] == 3

    def test_institution_consecutive_buy(self):
        """기관 4일 연속 순매수."""
        trading = _make_trading_rows(
            [0, 0, 0, 0],
            institution_vals=[100, 200, 300, 400],
        )
        result = analyze_supply_demand(trading, [])
        assert result["institution_consecutive_net_buy"] == 4
        assert result["institution_consecutive_net_sell"] == 0

    def test_mixed_pattern(self):
        """매수/매도 혼재 시 마지막 연속 구간만 카운트."""
        # 외국인: 매수, 매수, 매도, 매수, 매수 → 연속 매수 2일
        trading = _make_trading_rows([100, 200, -50, 100, 200])
        result = analyze_supply_demand(trading, [])
        assert result["foreign_consecutive_net_buy"] == 2
        assert result["foreign_consecutive_net_sell"] == 0

    def test_zero_is_neutral(self):
        """순매수 0은 연속 구간을 끊는다."""
        trading = _make_trading_rows([100, 200, 0, 100])
        result = analyze_supply_demand(trading, [])
        assert result["foreign_consecutive_net_buy"] == 1


class TestCumulativeNetTrading:
    """N일 누적 순매매 합계 테스트."""

    def test_cumulative_5d(self):
        trading = _make_trading_rows([100, -200, 300, -400, 500])
        result = analyze_supply_demand(trading, [])
        assert result["foreign_cumulative_5d"] == 300  # 100-200+300-400+500
        assert result["institution_cumulative_5d"] == -300

    def test_cumulative_20d_insufficient(self):
        """20일 미만 데이터면 None."""
        trading = _make_trading_rows([100] * 10)
        result = analyze_supply_demand(trading, [])
        assert result["foreign_cumulative_20d"] is None

    def test_cumulative_20d(self):
        trading = _make_trading_rows([100] * 20)
        result = analyze_supply_demand(trading, [])
        assert result["foreign_cumulative_20d"] == 2000
        assert result["institution_cumulative_20d"] == -2000


class TestOwnershipTrend:
    """외국인 보유비율 변화 추이 테스트."""

    def test_increasing(self):
        ownership = _make_ownership_rows([50.0, 50.1, 50.2, 50.3, 50.4])
        result = analyze_supply_demand([], ownership)
        assert result["ownership_trend"] == "increasing"

    def test_decreasing(self):
        ownership = _make_ownership_rows([50.4, 50.3, 50.2, 50.1, 50.0])
        result = analyze_supply_demand([], ownership)
        assert result["ownership_trend"] == "decreasing"

    def test_sideways(self):
        ownership = _make_ownership_rows([50.0, 50.1, 50.0, 50.1, 50.0])
        result = analyze_supply_demand([], ownership)
        assert result["ownership_trend"] == "sideways"

    def test_empty_ownership(self):
        result = analyze_supply_demand([], [])
        assert result["ownership_trend"] is None

    def test_ownership_change(self):
        """보유비율 변화량 계산."""
        ownership = _make_ownership_rows([50.0, 50.5])
        result = analyze_supply_demand([], ownership)
        assert abs(result["ownership_change_pct"] - 0.5) < 0.01


class TestOverallJudgment:
    """수급 종합 판정 테스트."""

    def test_buy_dominant(self):
        """외국인+기관 모두 순매수 → 매수 우위."""
        trading = _make_trading_rows(
            [500, 500, 500, 500, 500],
            institution_vals=[300, 300, 300, 300, 300],
        )
        ownership = _make_ownership_rows([50.0, 50.1, 50.2, 50.3, 50.4])
        result = analyze_supply_demand(trading, ownership)
        assert result["overall_judgment"] == "buy_dominant"

    def test_sell_dominant(self):
        """외국인+기관 모두 순매도 → 매도 우위."""
        trading = _make_trading_rows(
            [-500, -500, -500, -500, -500],
            institution_vals=[-300, -300, -300, -300, -300],
        )
        ownership = _make_ownership_rows([50.4, 50.3, 50.2, 50.1, 50.0])
        result = analyze_supply_demand(trading, ownership)
        assert result["overall_judgment"] == "sell_dominant"

    def test_neutral(self):
        """외국인 매수, 기관 매도 → 중립."""
        trading = _make_trading_rows(
            [500, 500, 500, 500, 500],
            institution_vals=[-500, -500, -500, -500, -500],
        )
        result = analyze_supply_demand(trading, [])
        assert result["overall_judgment"] == "neutral"


class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_empty_trading(self):
        result = analyze_supply_demand([], [])
        assert result["foreign_consecutive_net_buy"] == 0
        assert result["foreign_consecutive_net_sell"] == 0
        assert result["foreign_cumulative_5d"] is None
        assert result["overall_judgment"] == "neutral"

    def test_single_row(self):
        trading = _make_trading_rows([100])
        result = analyze_supply_demand(trading, [])
        assert result["foreign_consecutive_net_buy"] == 1
        assert result["foreign_cumulative_5d"] is None  # 5일 미만
