"""시그널 추이 분석 모듈 테스트."""

import types

import pytest

from src.analysis.signal_trend import (
    analyze_signal_trend,
    _sparkline,
    _classify_direction,
)


# ---------------------------------------------------------------------------
# Helpers: fake db_module
# ---------------------------------------------------------------------------

def _make_db(rows: list[dict]):
    """get_signal_history(days) 를 가짜로 구현하는 모듈 객체를 반환."""
    mod = types.ModuleType("fake_db")
    mod.get_signal_history = lambda days: rows[-days:] if len(rows) >= days else rows
    return mod


# ---------------------------------------------------------------------------
# _sparkline
# ---------------------------------------------------------------------------

class TestSparkline:
    def test_empty(self):
        assert _sparkline([]) == ""

    def test_single(self):
        assert len(_sparkline([50.0])) == 1

    def test_ascending(self):
        result = _sparkline([10, 30, 50, 70, 90])
        # 오름차순이면 뒤로 갈수록 높은 문자
        assert result[0] <= result[-1]

    def test_all_same(self):
        result = _sparkline([50, 50, 50])
        assert len(set(result)) == 1  # 모두 같은 문자


# ---------------------------------------------------------------------------
# _classify_direction
# ---------------------------------------------------------------------------

class TestClassifyDirection:
    def test_improving(self):
        scores = [10, 20, 30, 40, 50]
        assert _classify_direction(scores) == "개선"

    def test_worsening(self):
        scores = [50, 40, 30, 20, 10]
        assert _classify_direction(scores) == "악화"

    def test_sideways(self):
        scores = [30, 32, 29, 31, 30]
        assert _classify_direction(scores) == "횡보"

    def test_two_points_up(self):
        assert _classify_direction([20, 40]) == "개선"

    def test_single_point(self):
        assert _classify_direction([50]) == "횡보"


# ---------------------------------------------------------------------------
# analyze_signal_trend
# ---------------------------------------------------------------------------

class TestAnalyzeSignalTrend:
    def test_no_data_returns_none(self):
        db = _make_db([])
        assert analyze_signal_trend(db) is None

    def test_single_day(self):
        db = _make_db([
            {"date": "2026-03-28", "score": 42.0, "grade": "매수우세",
             "technical_score": 30, "supply_score": 50, "exchange_score": 20, "price": 55000},
        ])
        result = analyze_signal_trend(db, days=5)
        assert result is not None
        assert result["direction"] == "횡보"
        assert result["days_available"] == 1
        assert result["consecutive_same_grade"] >= 1

    def test_five_days_improving(self):
        rows = [
            {"date": f"2026-03-{24+i}", "score": 10 + i * 15, "grade": "중립" if i < 3 else "매수우세",
             "technical_score": 10, "supply_score": 10, "exchange_score": 10, "price": 55000 + i * 100}
            for i in range(5)
        ]
        db = _make_db(rows)
        result = analyze_signal_trend(db, days=5)

        assert result["direction"] == "개선"
        assert result["days_available"] == 5
        assert len(result["scores"]) == 5
        assert len(result["grades"]) == 5
        assert result["score_range"] > 0
        assert "sparkline" in result
        assert isinstance(result["latest_score"], float)
        assert isinstance(result["latest_grade"], str)

    def test_consecutive_same_grade(self):
        rows = [
            {"date": f"2026-03-{24+i}", "score": 25 + i, "grade": "매수우세",
             "technical_score": 10, "supply_score": 10, "exchange_score": 10, "price": 55000}
            for i in range(5)
        ]
        db = _make_db(rows)
        result = analyze_signal_trend(db, days=5)
        assert result["consecutive_same_grade"] == 5

    def test_grade_change_resets_count(self):
        grades = ["중립", "중립", "매수우세", "매수우세", "매수우세"]
        rows = [
            {"date": f"2026-03-{24+i}", "score": 20 + i * 5, "grade": grades[i],
             "technical_score": 10, "supply_score": 10, "exchange_score": 10, "price": 55000}
            for i in range(5)
        ]
        db = _make_db(rows)
        result = analyze_signal_trend(db, days=5)
        assert result["consecutive_same_grade"] == 3  # 최근 3일 매수우세

    def test_worsening_direction(self):
        rows = [
            {"date": f"2026-03-{24+i}", "score": 70 - i * 20, "grade": "매수우세",
             "technical_score": 10, "supply_score": 10, "exchange_score": 10, "price": 55000}
            for i in range(5)
        ]
        db = _make_db(rows)
        result = analyze_signal_trend(db, days=5)
        assert result["direction"] == "악화"

    def test_score_change(self):
        rows = [
            {"date": f"2026-03-{24+i}", "score": 20 + i * 10, "grade": "매수우세",
             "technical_score": 10, "supply_score": 10, "exchange_score": 10, "price": 55000}
            for i in range(5)
        ]
        db = _make_db(rows)
        result = analyze_signal_trend(db, days=5)
        assert result["score_change"] == pytest.approx(40.0)  # 60 - 20

    def test_custom_days(self):
        rows = [
            {"date": f"2026-03-{20+i}", "score": 10 + i * 5, "grade": "중립",
             "technical_score": 10, "supply_score": 10, "exchange_score": 10, "price": 55000}
            for i in range(10)
        ]
        db = _make_db(rows)
        result = analyze_signal_trend(db, days=3)
        assert result["days_available"] == 3
