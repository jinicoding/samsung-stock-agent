"""Tests for daily delta analysis module."""

import pytest
from unittest.mock import patch

from src.analysis.daily_delta import compute_daily_delta


AXES = [
    "technical_score", "supply_score", "exchange_score",
    "fundamentals_score", "news_score", "consensus_score",
    "semiconductor_score", "volatility_score", "candlestick_score",
    "global_macro_score",
]


def _make_signal(date: str, score: float, grade: str, price: float = 55000,
                 **axis_scores) -> dict:
    base = {
        "date": date, "score": score, "grade": grade, "price": price,
    }
    for ax in AXES:
        base[ax] = axis_scores.get(ax)
    return base


class TestComputeDailyDelta:
    """compute_daily_delta 함수 테스트."""

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_empty_history_returns_none(self, mock_hist):
        mock_hist.return_value = []
        result = compute_daily_delta()
        assert result is None

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_single_day_returns_none(self, mock_hist):
        mock_hist.return_value = [
            _make_signal("2026-04-11", 30, "매수우세", technical_score=40, supply_score=20),
        ]
        result = compute_daily_delta()
        assert result is None

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_basic_delta_calculation(self, mock_hist):
        prev = _make_signal("2026-04-11", 25, "매수우세",
                            technical_score=30, supply_score=20, exchange_score=10)
        curr = _make_signal("2026-04-12", 35, "매수우세",
                            technical_score=50, supply_score=15, exchange_score=10)
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()

        assert result is not None
        assert result["axes_delta"]["technical_score"]["prev"] == 30
        assert result["axes_delta"]["technical_score"]["curr"] == 50
        assert result["axes_delta"]["technical_score"]["change"] == 20
        assert result["axes_delta"]["supply_score"]["change"] == -5
        assert result["axes_delta"]["exchange_score"]["change"] == 0

        assert result["overall"]["prev_score"] == 25
        assert result["overall"]["curr_score"] == 35
        assert result["overall"]["change"] == 10
        assert result["overall"]["prev_grade"] == "매수우세"
        assert result["overall"]["curr_grade"] == "매수우세"

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_signal_flip_alert(self, mock_hist):
        """점수가 0을 교차하면 signal_flip 알림."""
        prev = _make_signal("2026-04-11", -10, "중립",
                            technical_score=-20, supply_score=10)
        curr = _make_signal("2026-04-12", 15, "중립",
                            technical_score=25, supply_score=-5)
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()
        alert_types = {(a["type"], a["axis"]) for a in result["alerts"]}

        assert ("signal_flip", "technical_score") in alert_types
        assert ("signal_flip", "supply_score") in alert_types

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_no_flip_when_both_positive(self, mock_hist):
        """같은 부호이면 signal_flip 없음."""
        prev = _make_signal("2026-04-11", 20, "매수우세",
                            technical_score=10, supply_score=30)
        curr = _make_signal("2026-04-12", 30, "매수우세",
                            technical_score=25, supply_score=40)
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()
        flip_alerts = [a for a in result["alerts"] if a["type"] == "signal_flip"]
        assert len(flip_alerts) == 0

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_significant_move_alert(self, mock_hist):
        """±15점 이상 변동 시 significant_move 알림."""
        prev = _make_signal("2026-04-11", 10, "중립",
                            technical_score=10, supply_score=50)
        curr = _make_signal("2026-04-12", 30, "매수우세",
                            technical_score=30, supply_score=50)
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()
        sig_moves = [a for a in result["alerts"] if a["type"] == "significant_move"]
        axes_with_moves = {a["axis"] for a in sig_moves}

        assert "technical_score" in axes_with_moves
        assert "overall" in axes_with_moves

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_no_significant_move_small_change(self, mock_hist):
        """변동 14점이면 significant_move 없음."""
        prev = _make_signal("2026-04-11", 10, "중립",
                            technical_score=10)
        curr = _make_signal("2026-04-12", 24, "매수우세",
                            technical_score=24)
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()
        sig_moves = [a for a in result["alerts"]
                     if a["type"] == "significant_move" and a["axis"] == "technical_score"]
        assert len(sig_moves) == 0

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_grade_change_alert(self, mock_hist):
        """등급 변동 시 grade_change 알림."""
        prev = _make_signal("2026-04-11", 15, "중립",
                            technical_score=15)
        curr = _make_signal("2026-04-12", 25, "매수우세",
                            technical_score=25)
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()
        grade_alerts = [a for a in result["alerts"] if a["type"] == "grade_change"]
        assert len(grade_alerts) == 1
        assert grade_alerts[0]["detail"] == "중립 → 매수우세"

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_no_grade_change_same_grade(self, mock_hist):
        prev = _make_signal("2026-04-11", 25, "매수우세")
        curr = _make_signal("2026-04-12", 35, "매수우세")
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()
        grade_alerts = [a for a in result["alerts"] if a["type"] == "grade_change"]
        assert len(grade_alerts) == 0

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_none_axes_handled(self, mock_hist):
        """None 값인 축은 axes_delta에서 제외."""
        prev = _make_signal("2026-04-11", 20, "매수우세",
                            technical_score=30)
        curr = _make_signal("2026-04-12", 25, "매수우세",
                            technical_score=40)
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()
        assert "fundamentals_score" not in result["axes_delta"]
        assert "technical_score" in result["axes_delta"]

    @patch("src.analysis.daily_delta.get_signal_history")
    def test_overall_signal_flip(self, mock_hist):
        """종합 점수의 방향 전환도 signal_flip으로 감지."""
        prev = _make_signal("2026-04-11", -25, "매도우세",
                            technical_score=-30)
        curr = _make_signal("2026-04-12", 10, "중립",
                            technical_score=15)
        mock_hist.return_value = [prev, curr]

        result = compute_daily_delta()
        overall_flips = [a for a in result["alerts"]
                         if a["type"] == "signal_flip" and a["axis"] == "overall"]
        assert len(overall_flips) == 1
