"""Tests for src/analysis/backtest.py — 시그널 성과 백테스팅 모듈."""

import os
import tempfile

import pytest


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database file and patch DB_FILE."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    monkeypatch.setattr("src.data.config.DB_FILE", db_path)
    import importlib
    import src.data.database as db_mod
    importlib.reload(db_mod)
    db_mod.init_db()
    yield db_path, db_mod
    os.unlink(db_path)


def _seed_20days(db):
    """20거래일 주가 + 다양한 등급 시그널을 삽입한다."""
    # 주가: 상승 → 하락 → 상승 패턴
    base_prices = [
        ("2026-03-02", 55000, 55500, 54500, 55200, 1000000),
        ("2026-03-03", 55200, 55800, 55000, 55600, 1100000),
        ("2026-03-04", 55600, 56200, 55400, 56000, 1200000),
        ("2026-03-05", 56000, 56600, 55800, 56400, 1300000),
        ("2026-03-06", 56400, 57000, 56200, 56800, 1400000),
        ("2026-03-09", 56800, 57200, 56600, 57000, 1500000),
        ("2026-03-10", 57000, 57400, 56800, 57200, 1600000),
        ("2026-03-11", 57200, 57600, 57000, 57400, 1700000),
        # 하락 시작
        ("2026-03-12", 57400, 57600, 56800, 56900, 1800000),
        ("2026-03-13", 56900, 57000, 56200, 56400, 1900000),
        ("2026-03-16", 56400, 56600, 55800, 55900, 2000000),
        ("2026-03-17", 55900, 56000, 55200, 55400, 2100000),
        ("2026-03-18", 55400, 55600, 54800, 55000, 2200000),
        # 반등
        ("2026-03-19", 55000, 55800, 54900, 55600, 2300000),
        ("2026-03-20", 55600, 56200, 55400, 56000, 2400000),
        ("2026-03-23", 56000, 56800, 55800, 56600, 2500000),
        ("2026-03-24", 56600, 57200, 56400, 57000, 2600000),
        ("2026-03-25", 57000, 57600, 56800, 57400, 2700000),
        ("2026-03-26", 57400, 58000, 57200, 57800, 2800000),
        ("2026-03-27", 57800, 58400, 57600, 58200, 2900000),
    ]
    for p in base_prices:
        db.upsert_daily(*p)

    # 시그널: 다양한 등급
    # 강력매수(+70): 상승 구간 → hit
    db.upsert_signal_history(
        "2026-03-02", 70.0, "강력매수신호", 30.0, 25.0, 15.0, 55200,
        fundamentals_score=10.0, semiconductor_score=8.0,
    )
    # 매수(+30): 상승 구간 → hit
    db.upsert_signal_history(
        "2026-03-04", 30.0, "매수우세", 12.0, 10.0, 8.0, 56000,
        fundamentals_score=5.0, semiconductor_score=3.0,
    )
    # 매수(+25): 하락 직전 → miss (3d, 5d)
    db.upsert_signal_history(
        "2026-03-10", 25.0, "매수우세", 10.0, 8.0, 7.0, 57200,
        fundamentals_score=4.0, semiconductor_score=-2.0,
    )
    # 중립(0): 방향 판정 제외
    db.upsert_signal_history(
        "2026-03-11", 0.0, "중립", 0.0, 0.0, 0.0, 57400,
    )
    # 매도(-35): 하락 구간 → hit
    db.upsert_signal_history(
        "2026-03-12", -35.0, "매도우세", -14.0, -12.0, -9.0, 56900,
        fundamentals_score=-6.0, semiconductor_score=-5.0,
    )
    # 강력매도(-65): 하락 구간 → hit
    db.upsert_signal_history(
        "2026-03-13", -65.0, "강력매도신호", -26.0, -22.0, -17.0, 56400,
        fundamentals_score=-10.0, semiconductor_score=-8.0,
    )
    # 매도(-30): 반등 구간 → miss
    db.upsert_signal_history(
        "2026-03-17", -30.0, "매도우세", -12.0, -10.0, -8.0, 55400,
        fundamentals_score=-5.0, semiconductor_score=3.0,
    )
    # 매수(+40): 반등 구간 → hit
    db.upsert_signal_history(
        "2026-03-19", 40.0, "매수우세", 16.0, 14.0, 10.0, 55600,
        fundamentals_score=7.0, semiconductor_score=6.0,
    )


# ── Grade Performance ──────────────────────────────────────────


class TestGradePerformance:
    """등급별(강력매수~강력매도) 평균 수익률과 적중률 테스트."""

    def test_grade_performance_keys(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        gp = result["grade_performance"]
        assert "강력매수신호" in gp
        assert "매수우세" in gp
        assert "중립" in gp
        assert "매도우세" in gp
        assert "강력매도신호" in gp

    def test_grade_has_return_and_hit_rate(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        for grade_stats in result["grade_performance"].values():
            for n in (1, 3, 5):
                assert f"avg_return_{n}d" in grade_stats
                assert f"hit_rate_{n}d" in grade_stats
                assert f"count" in grade_stats

    def test_strong_buy_positive_return(self, temp_db):
        """강력매수신호(03-02): 상승 구간이므로 양수 수익률."""
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        sb = result["grade_performance"]["강력매수신호"]
        assert sb["count"] == 1
        # 1d: (55600-55200)/55200*100 > 0
        assert sb["avg_return_1d"] > 0

    def test_strong_sell_hit(self, temp_db):
        """강력매도신호(03-13): 하락 구간이므로 hit."""
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        ss = result["grade_performance"]["강력매도신호"]
        assert ss["count"] == 1
        assert ss["hit_rate_1d"] == 100.0

    def test_neutral_excluded_from_hit_rate(self, temp_db):
        """중립 등급은 hit_rate가 None이어야 한다."""
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        neutral = result["grade_performance"]["중립"]
        assert neutral["hit_rate_1d"] is None


# ── Score Range Performance ────────────────────────────────────


class TestScoreRangePerformance:
    """점수 구간별 성과 통계 테스트."""

    def test_score_ranges_exist(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        sr = result["score_range_performance"]
        assert isinstance(sr, list)
        assert len(sr) > 0

    def test_score_range_structure(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        for entry in result["score_range_performance"]:
            assert "range_label" in entry
            assert "count" in entry
            assert "avg_return_1d" in entry
            assert "hit_rate_1d" in entry

    def test_all_signals_covered(self, temp_db):
        """모든 시그널이 하나의 구간에 속해야 한다."""
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        total = sum(e["count"] for e in result["score_range_performance"])
        assert total == 8  # 8개 시그널


# ── Streak Analysis ────────────────────────────────────────────


class TestStreakAnalysis:
    """연속 성과 분석 테스트."""

    def test_streak_keys(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        sa = result["streak_analysis"]
        assert "max_win_streak" in sa
        assert "max_lose_streak" in sa
        assert "equity_curve" in sa

    def test_equity_curve_length(self, temp_db):
        """equity_curve 길이 = 판정 가능한 시그널 수."""
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        curve = result["streak_analysis"]["equity_curve"]
        assert isinstance(curve, list)
        assert len(curve) > 0

    def test_equity_curve_structure(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        for point in result["streak_analysis"]["equity_curve"]:
            assert "date" in point
            assert "cumulative_return" in point

    def test_max_streaks_non_negative(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        assert result["streak_analysis"]["max_win_streak"] >= 0
        assert result["streak_analysis"]["max_lose_streak"] >= 0


# ── Axis Contribution ─────────────────────────────────────────


class TestAxisContribution:
    """축별 기여도 분석 테스트."""

    def test_axis_contribution_keys(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        ac = result["axis_contribution"]
        assert isinstance(ac, dict)

    def test_axis_contribution_has_correlation(self, temp_db):
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        for axis, stats in result["axis_contribution"].items():
            assert "correlation_1d" in stats
            assert "contribution_rank" in stats

    def test_correlation_range(self, temp_db):
        """상관계수는 -1 ~ +1 범위."""
        _, db = temp_db
        _seed_20days(db)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        for axis, stats in result["axis_contribution"].items():
            corr = stats["correlation_1d"]
            if corr is not None:
                assert -1.0 <= corr <= 1.0


# ── Empty Data ─────────────────────────────────────────────────


class TestEmptyBacktest:
    """데이터가 없을 때의 처리."""

    def test_no_signals(self, temp_db):
        _, db = temp_db
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        assert result["grade_performance"] == {}
        assert all(e["count"] == 0 for e in result["score_range_performance"])
        assert result["streak_analysis"]["max_win_streak"] == 0
        assert result["streak_analysis"]["max_lose_streak"] == 0
        assert result["axis_contribution"] == {}

    def test_signals_without_prices(self, temp_db):
        _, db = temp_db
        db.upsert_signal_history("2026-03-10", 30.0, "매수우세", 12.0, 10.0, 8.0, 58200)
        from src.analysis.backtest import run_backtest
        result = run_backtest(db)
        assert result["grade_performance"]["매수우세"]["count"] == 1
        assert result["grade_performance"]["매수우세"]["avg_return_1d"] is None
