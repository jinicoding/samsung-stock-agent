"""Tests for src/analysis/accuracy.py — 시그널 정확도 추적 모듈."""

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


def _seed_data(db):
    """10일치 주가 + 시그널 시드 데이터를 삽입한다."""
    # 주가: 2026-03-10 ~ 2026-03-21 (주말 제외 10일)
    prices = [
        ("2026-03-10", 58000, 58500, 57500, 58200, 1000000),
        ("2026-03-11", 58200, 58800, 58000, 58600, 1100000),
        ("2026-03-12", 58600, 59200, 58400, 59000, 1200000),
        ("2026-03-13", 59000, 59500, 58800, 59400, 1300000),
        ("2026-03-14", 59400, 60000, 59200, 59800, 1400000),
        ("2026-03-17", 59800, 60200, 59600, 60000, 1500000),
        ("2026-03-18", 60000, 60500, 59800, 60200, 1600000),
        ("2026-03-19", 60200, 60800, 60000, 60400, 1700000),
        ("2026-03-20", 60400, 61000, 60200, 60600, 1800000),
        ("2026-03-21", 60600, 61200, 60400, 60800, 1900000),
    ]
    for p in prices:
        db.upsert_daily(*p)

    # 시그널: 매수(+30) on 03-10, 매도(-40) on 03-13, 중립(0) on 03-17
    db.upsert_signal_history("2026-03-10", 30.0, "매수우세", 12.0, 10.0, 8.0, 58200)
    db.upsert_signal_history("2026-03-13", -40.0, "매도우세", -16.0, -14.0, -10.0, 59400)
    db.upsert_signal_history("2026-03-17", 0.0, "중립", 0.0, 0.0, 0.0, 60000)


class TestCalculateForwardReturns:
    """시그널별 N일 후 수익률 계산 테스트."""

    def test_forward_returns_1day(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        # 03-10 시그널: price=58200, 1일후(03-11)=58600 → +0.687%
        sig_0310 = [s for s in result["details"] if s["date"] == "2026-03-10"][0]
        assert sig_0310["forward_return_1d"] == pytest.approx(
            (58600 - 58200) / 58200 * 100, abs=0.01
        )

    def test_forward_returns_3day(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        # 03-10 시그널: price=58200, 3일후(03-13)=59400 → +2.06%
        sig_0310 = [s for s in result["details"] if s["date"] == "2026-03-10"][0]
        assert sig_0310["forward_return_3d"] == pytest.approx(
            (59400 - 58200) / 58200 * 100, abs=0.01
        )

    def test_forward_returns_5day(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        # 03-10 시그널: price=58200, 5거래일후(03-17)=60000 → +3.09%
        sig_0310 = [s for s in result["details"] if s["date"] == "2026-03-10"][0]
        assert sig_0310["forward_return_5d"] == pytest.approx(
            (60000 - 58200) / 58200 * 100, abs=0.01
        )

    def test_missing_forward_data_is_none(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        # 03-17 시그널: 5일후 데이터 부족 → None
        sig_0317 = [s for s in result["details"] if s["date"] == "2026-03-17"][0]
        assert sig_0317["forward_return_5d"] is None


class TestDirectionAccuracy:
    """시그널 방향과 실제 주가 방향 일치 여부 테스트."""

    def test_buy_signal_with_price_up_is_hit(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        sig_0310 = [s for s in result["details"] if s["date"] == "2026-03-10"][0]
        # score=+30 (매수), 1일후 상승 → hit
        assert sig_0310["hit_1d"] is True

    def test_sell_signal_with_price_up_is_miss(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        sig_0313 = [s for s in result["details"] if s["date"] == "2026-03-13"][0]
        # score=-40 (매도), 1일후(03-14) 59800 > 59400 상승 → miss
        assert sig_0313["hit_1d"] is False

    def test_neutral_signal_excluded_from_hit(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        sig_0317 = [s for s in result["details"] if s["date"] == "2026-03-17"][0]
        # score=0 (중립) → hit 판정 제외 (None)
        assert sig_0317["hit_1d"] is None


class TestSummaryStats:
    """전체 적중률·평균 수익률 통계 테스트."""

    def test_summary_hit_rate(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        summary = result["summary"]
        # 1d: 매수(hit) + 매도(miss) = 1/2 = 50%
        assert summary["hit_rate_1d"] == pytest.approx(50.0, abs=0.1)

    def test_summary_avg_return(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        summary = result["summary"]
        assert "avg_return_1d" in summary
        assert isinstance(summary["avg_return_1d"], float)

    def test_summary_signal_count(self, temp_db):
        _, db = temp_db
        _seed_data(db)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        assert result["summary"]["total_signals"] == 3
        # 중립 제외한 판정 가능 시그널
        assert result["summary"]["evaluated_signals_1d"] == 2


class TestEmptyData:
    """데이터가 없을 때의 처리 테스트."""

    def test_no_signals_returns_empty(self, temp_db):
        _, db = temp_db
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        assert result["details"] == []
        assert result["summary"]["total_signals"] == 0

    def test_no_prices_returns_none_returns(self, temp_db):
        _, db = temp_db
        db.upsert_signal_history("2026-03-10", 30.0, "매수우세", 12.0, 10.0, 8.0, 58200)
        from src.analysis.accuracy import evaluate_signals
        result = evaluate_signals(db)
        assert result["details"][0]["forward_return_1d"] is None
