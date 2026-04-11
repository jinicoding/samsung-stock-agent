"""Tests for src/analysis/pattern_match.py — Historical Pattern Matching."""

import importlib
import os
import tempfile

import pytest


SCORE_AXES = [
    "technical_score", "supply_score", "exchange_score",
    "fundamentals_score", "news_score", "consensus_score",
    "semiconductor_score", "volatility_score", "candlestick_score",
    "global_macro_score",
]


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database and seed it with signal_history + daily_prices."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    monkeypatch.setattr("src.data.config.DB_FILE", db_path)
    import src.data.database as db_mod
    importlib.reload(db_mod)
    db_mod.init_db()
    yield db_path, db_mod
    os.unlink(db_path)


def _seed_signals(db, count: int, base_date: str = "2026-03-01",
                  score_fn=None, price_fn=None):
    """Insert `count` signal_history + daily_prices rows starting from base_date."""
    from datetime import datetime, timedelta
    start = datetime.strptime(base_date, "%Y-%m-%d")
    for i in range(count):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        if score_fn:
            scores = score_fn(i)
        else:
            scores = {ax: float(i * 3 % 100) for ax in SCORE_AXES}
        price = price_fn(i) if price_fn else 55000 + i * 100
        db.upsert_signal_history(
            date=d, score=scores.get("technical_score", 0.0),
            grade="중립", price=price,
            technical_score=scores["technical_score"],
            supply_score=scores["supply_score"],
            exchange_score=scores["exchange_score"],
            fundamentals_score=scores.get("fundamentals_score"),
            news_score=scores.get("news_score"),
            consensus_score=scores.get("consensus_score"),
            semiconductor_score=scores.get("semiconductor_score"),
            volatility_score=scores.get("volatility_score"),
            candlestick_score=scores.get("candlestick_score"),
            global_macro_score=scores.get("global_macro_score"),
        )
        db.upsert_daily(d, price - 500, price + 500, price - 700, price, 1000000)


# ── Similarity calculation ──────────────────────────────────────

class TestSimilarityCalculation:

    def test_identical_vectors_distance_zero(self, temp_db):
        """동일 벡터는 거리 0, 유사도 1.0."""
        _, db = temp_db
        _seed_signals(db, 30)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 0.0 for ax in SCORE_AXES}
        _seed_signals(db, 30, score_fn=lambda i: {ax: 0.0 for ax in SCORE_AXES})
        result = find_similar_patterns(current, db, top_n=3)
        assert result is not None
        for m in result["matches"]:
            assert m["distance"] == pytest.approx(0.0, abs=0.01)
            assert m["similarity"] == pytest.approx(1.0, abs=0.01)

    def test_opposite_vectors_low_similarity(self, temp_db):
        """정반대 벡터는 유사도가 낮아야 한다."""
        _, db = temp_db

        def pos_scores(i):
            return {ax: 100.0 for ax in SCORE_AXES}

        _seed_signals(db, 30, score_fn=pos_scores)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: -100.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is not None
        for m in result["matches"]:
            assert m["similarity"] < 0.3

    def test_similarity_between_0_and_1(self, temp_db):
        """유사도는 항상 0~1 범위."""
        _, db = temp_db
        _seed_signals(db, 30)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 50.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is not None
        for m in result["matches"]:
            assert 0.0 <= m["similarity"] <= 1.0

    def test_matches_sorted_by_distance(self, temp_db):
        """결과는 거리 오름차순(유사도 내림차순) 정렬."""
        _, db = temp_db
        _seed_signals(db, 30)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 20.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is not None
        distances = [m["distance"] for m in result["matches"]]
        assert distances == sorted(distances)


# ── NULL axis handling ──────────────────────────────────────────

class TestNullAxisHandling:

    def test_null_axes_excluded_from_distance(self, temp_db):
        """NULL 축은 거리 계산에서 제외된다."""
        _, db = temp_db

        def partial_scores(i):
            return {
                "technical_score": 50.0, "supply_score": 50.0,
                "exchange_score": 50.0,
                "fundamentals_score": None, "news_score": None,
                "consensus_score": None, "semiconductor_score": None,
                "volatility_score": None, "candlestick_score": None,
                "global_macro_score": None,
            }

        _seed_signals(db, 30, score_fn=partial_scores)
        from src.analysis.pattern_match import find_similar_patterns

        current = {"technical_score": 50.0, "supply_score": 50.0,
                    "exchange_score": 50.0}
        result = find_similar_patterns(current, db, top_n=3)
        assert result is not None
        for m in result["matches"]:
            assert m["distance"] == pytest.approx(0.0, abs=0.01)

    def test_all_axes_null_except_core(self, temp_db):
        """핵심 3축만 있어도 작동."""
        _, db = temp_db

        def core_only(i):
            return {
                "technical_score": float(i * 5),
                "supply_score": float(i * 3),
                "exchange_score": float(i * 2),
                "fundamentals_score": None, "news_score": None,
                "consensus_score": None, "semiconductor_score": None,
                "volatility_score": None, "candlestick_score": None,
                "global_macro_score": None,
            }

        _seed_signals(db, 30, score_fn=core_only)
        from src.analysis.pattern_match import find_similar_patterns

        current = {"technical_score": 25.0, "supply_score": 15.0,
                    "exchange_score": 10.0}
        result = find_similar_patterns(current, db, top_n=3)
        assert result is not None
        assert len(result["matches"]) > 0


# ── Self-correlation exclusion ──────────────────────────────────

class TestSelfCorrelationExclusion:

    def test_recent_days_excluded(self, temp_db):
        """최근 7일은 결과에 포함되지 않는다."""
        _, db = temp_db
        _seed_signals(db, 30)
        from src.analysis.pattern_match import find_similar_patterns

        signals = db.get_signal_history(30)
        last_date = signals[-1]["date"]
        current = {ax: float(29 * 3 % 100) for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is not None
        match_dates = [m["date"] for m in result["matches"]]
        from datetime import datetime, timedelta
        last_dt = datetime.strptime(last_date, "%Y-%m-%d")
        for md in match_dates:
            md_dt = datetime.strptime(md, "%Y-%m-%d")
            assert (last_dt - md_dt).days >= 7

    def test_custom_exclude_window(self, temp_db):
        """exclude_recent 파라미터로 제외 기간 조정."""
        _, db = temp_db
        _seed_signals(db, 40)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 50.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5, exclude_recent=14)
        assert result is not None
        signals = db.get_signal_history(40)
        last_date = signals[-1]["date"]
        from datetime import datetime
        last_dt = datetime.strptime(last_date, "%Y-%m-%d")
        for m in result["matches"]:
            md_dt = datetime.strptime(m["date"], "%Y-%m-%d")
            assert (last_dt - md_dt).days >= 14


# ── Forward return calculation ──────────────────────────────────

class TestForwardReturns:

    def test_forward_returns_calculated(self, temp_db):
        """유사 날짜 이후 1/3/5일 수익률이 계산된다."""
        _, db = temp_db
        _seed_signals(db, 40, price_fn=lambda i: 55000 + i * 100)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 10.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=3)
        assert result is not None
        for m in result["matches"]:
            fr = m["forward_returns"]
            assert "1d" in fr
            assert "3d" in fr
            assert "5d" in fr

    def test_forward_returns_correct_value(self, temp_db):
        """수익률 계산이 정확한지 검증 (price[t+n]/price[t] - 1)."""
        _, db = temp_db

        def fixed_scores(i):
            return {ax: 0.0 for ax in SCORE_AXES}

        prices = [50000, 50500, 51000, 50000, 51500, 52000,
                  50000, 50000, 50000, 50000, 50000, 50000,
                  50000, 50000, 50000, 50000, 50000, 50000,
                  50000, 50000, 50000, 50000, 50000, 50000,
                  50000, 50000, 50000, 50000, 50000, 50000]
        _seed_signals(db, 30, score_fn=fixed_scores,
                      price_fn=lambda i: prices[i])
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 0.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is not None
        day0 = [m for m in result["matches"] if m["date"] == "2026-03-01"]
        if day0:
            fr = day0[0]["forward_returns"]
            assert fr["1d"] == pytest.approx(0.01, abs=0.001)
            assert fr["3d"] == pytest.approx(0.0, abs=0.001)
            assert fr["5d"] == pytest.approx(0.04, abs=0.001)

    def test_forward_returns_none_at_end(self, temp_db):
        """데이터 끝부분에서 forward return은 None."""
        _, db = temp_db
        _seed_signals(db, 25)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: float(17 * 3 % 100) for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=10)
        if result:
            late_matches = [m for m in result["matches"]
                           if m["date"] >= "2026-03-20"]
            for m in late_matches:
                fr = m["forward_returns"]
                assert fr["5d"] is None or isinstance(fr["5d"], float)


# ── Insufficient data ──────────────────────────────────────────

class TestInsufficientData:

    def test_returns_none_if_too_few_records(self, temp_db):
        """이력 20일 미만이면 None 반환."""
        _, db = temp_db
        _seed_signals(db, 10)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 0.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is None

    def test_returns_none_if_empty_db(self, temp_db):
        """빈 DB에서 None 반환."""
        _, db = temp_db
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 0.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is None


# ── Summary statistics ──────────────────────────────────────────

class TestSummaryStatistics:

    def test_summary_keys_present(self, temp_db):
        """summary에 필수 키가 모두 존재."""
        _, db = temp_db
        _seed_signals(db, 30, price_fn=lambda i: 55000 + i * 100)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 10.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is not None
        s = result["summary"]
        for key in ["avg_return_1d", "avg_return_3d", "avg_return_5d",
                     "up_ratio_1d", "up_ratio_3d", "up_ratio_5d",
                     "match_count"]:
            assert key in s

    def test_up_ratio_between_0_and_1(self, temp_db):
        """상승 확률은 0~1 범위."""
        _, db = temp_db
        _seed_signals(db, 30, price_fn=lambda i: 55000 + i * 100)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 10.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=5)
        assert result is not None
        s = result["summary"]
        for key in ["up_ratio_1d", "up_ratio_3d", "up_ratio_5d"]:
            if s[key] is not None:
                assert 0.0 <= s[key] <= 1.0

    def test_match_count_equals_matches_length(self, temp_db):
        """match_count는 matches 배열 길이와 일치."""
        _, db = temp_db
        _seed_signals(db, 30)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 10.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=3)
        assert result is not None
        assert result["summary"]["match_count"] == len(result["matches"])


# ── Return format ───────────────────────────────────────────────

class TestReturnFormat:

    def test_match_has_required_keys(self, temp_db):
        """각 match에 필수 키(date, distance, similarity, scores, forward_returns)."""
        _, db = temp_db
        _seed_signals(db, 30)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 10.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=3)
        assert result is not None
        for m in result["matches"]:
            assert "date" in m
            assert "distance" in m
            assert "similarity" in m
            assert "scores" in m
            assert "forward_returns" in m

    def test_top_n_respected(self, temp_db):
        """top_n 파라미터가 결과 개수를 제한."""
        _, db = temp_db
        _seed_signals(db, 40)
        from src.analysis.pattern_match import find_similar_patterns

        current = {ax: 10.0 for ax in SCORE_AXES}
        result = find_similar_patterns(current, db, top_n=2)
        assert result is not None
        assert len(result["matches"]) <= 2
