"""Tests for multi-axis convergence analysis module."""

import pytest
from src.analysis.convergence import classify_direction, analyze_convergence


class TestClassifyDirection:
    """Test direction classification with ±15 threshold."""

    def test_bullish(self):
        assert classify_direction(20) == "bullish"
        assert classify_direction(100) == "bullish"
        assert classify_direction(15.1) == "bullish"

    def test_bearish(self):
        assert classify_direction(-20) == "bearish"
        assert classify_direction(-100) == "bearish"
        assert classify_direction(-15.1) == "bearish"

    def test_neutral(self):
        assert classify_direction(0) == "neutral"
        assert classify_direction(15) == "neutral"
        assert classify_direction(-15) == "neutral"
        assert classify_direction(14.9) == "neutral"
        assert classify_direction(-14.9) == "neutral"


class TestAnalyzeConvergence:
    """Test multi-axis convergence analysis."""

    def _make_scores(self, **overrides):
        """Helper: all neutral by default, override specific axes."""
        defaults = {
            "technical_score": 0,
            "supply_score": 0,
            "exchange_score": 0,
            "fundamental_score": 0,
            "news_score": 0,
            "consensus_score": 0,
            "semiconductor_score": 0,
            "volatility_score": 0,
            "candlestick_score": 0,
        }
        defaults.update(overrides)
        return defaults

    def test_strong_bullish_convergence(self):
        """7+ axes pointing bullish → strong convergence."""
        scores = self._make_scores(
            technical_score=50,
            supply_score=40,
            exchange_score=30,
            fundamental_score=25,
            news_score=20,
            consensus_score=35,
            semiconductor_score=45,
        )
        result = analyze_convergence(scores)
        assert result["convergence_level"] == "strong"
        assert result["dominant_direction"] == "bullish"
        assert len(result["aligned_axes"]) >= 7
        assert result["conviction"] >= 70

    def test_strong_bearish_convergence(self):
        """7+ axes pointing bearish → strong convergence."""
        scores = self._make_scores(
            technical_score=-50,
            supply_score=-40,
            exchange_score=-30,
            fundamental_score=-25,
            news_score=-20,
            consensus_score=-35,
            semiconductor_score=-45,
        )
        result = analyze_convergence(scores)
        assert result["convergence_level"] == "strong"
        assert result["dominant_direction"] == "bearish"
        assert len(result["aligned_axes"]) >= 7

    def test_moderate_convergence(self):
        """5-6 axes same direction → moderate."""
        scores = self._make_scores(
            technical_score=50,
            supply_score=40,
            exchange_score=30,
            fundamental_score=25,
            news_score=20,
        )
        result = analyze_convergence(scores)
        assert result["convergence_level"] == "moderate"
        assert result["dominant_direction"] == "bullish"
        assert len(result["aligned_axes"]) == 5

    def test_weak_convergence(self):
        """3-4 axes same direction → weak."""
        scores = self._make_scores(
            technical_score=50,
            supply_score=40,
            exchange_score=30,
        )
        result = analyze_convergence(scores)
        assert result["convergence_level"] == "weak"

    def test_mixed_convergence(self):
        """≤2 axes agree → mixed."""
        scores = self._make_scores(
            technical_score=50,
            supply_score=-40,
            exchange_score=30,
            fundamental_score=-25,
        )
        result = analyze_convergence(scores)
        assert result["convergence_level"] == "mixed"

    def test_conflicting_axes_listed(self):
        """Conflicting axes should be listed."""
        scores = self._make_scores(
            technical_score=50,
            supply_score=-40,
            exchange_score=30,
        )
        result = analyze_convergence(scores)
        assert "supply_score" in result["conflicting_axes"]

    def test_all_neutral(self):
        """All neutral scores → mixed, neutral direction."""
        scores = self._make_scores()
        result = analyze_convergence(scores)
        assert result["convergence_level"] == "mixed"
        assert result["dominant_direction"] == "neutral"
        assert result["conviction"] == 0

    def test_conviction_range(self):
        """Conviction should always be 0-100."""
        scores = self._make_scores(
            technical_score=100,
            supply_score=100,
            exchange_score=100,
            fundamental_score=100,
            news_score=100,
            consensus_score=100,
            semiconductor_score=100,
            volatility_score=100,
            candlestick_score=100,
        )
        result = analyze_convergence(scores)
        assert 0 <= result["conviction"] <= 100

    def test_result_keys(self):
        """Result should contain all expected keys."""
        scores = self._make_scores(technical_score=50)
        result = analyze_convergence(scores)
        expected_keys = {
            "convergence_level",
            "dominant_direction",
            "aligned_axes",
            "conflicting_axes",
            "neutral_axes",
            "conviction",
            "axis_directions",
        }
        assert expected_keys == set(result.keys())

    def test_optional_axes_missing(self):
        """Should work with only some axes provided."""
        scores = {
            "technical_score": 50,
            "supply_score": 40,
            "exchange_score": 30,
        }
        result = analyze_convergence(scores)
        assert result["convergence_level"] in ("weak", "moderate", "strong")
        assert len(result["aligned_axes"]) == 3

    def test_six_axes_moderate(self):
        """Exactly 6 axes same direction → moderate."""
        scores = self._make_scores(
            technical_score=50,
            supply_score=40,
            exchange_score=30,
            fundamental_score=25,
            news_score=20,
            consensus_score=35,
        )
        result = analyze_convergence(scores)
        assert result["convergence_level"] == "moderate"
        assert len(result["aligned_axes"]) == 6


class TestConvergencePipeline:
    """Test that main.py conv_scores construction includes all optional axes."""

    def test_rs_score_included_in_convergence(self):
        """rs_score가 sig에 존재하면 conv_scores에 포함되어야 한다.

        main.py의 conv_scores 구성 로직을 재현하여 rs_score 누락 버그를 검증.
        """
        sig = {
            "technical_score": 30,
            "supply_score": 20,
            "exchange_score": 10,
            "rs_score": 45,
            "news_score": -10,
        }
        # main.py의 conv_scores 구성 로직 재현
        conv_scores = {
            "technical_score": sig["technical_score"],
            "supply_score": sig["supply_score"],
            "exchange_score": sig["exchange_score"],
        }
        for key in ("fundamentals_score", "news_score", "consensus_score",
                     "semiconductor_score", "volatility_score", "candlestick_score",
                     "global_macro_score", "rs_score"):
            if key in sig:
                conv_scores[key] = sig[key]

        assert "rs_score" in conv_scores, "rs_score가 conv_scores에 포함되어야 함"
        assert conv_scores["rs_score"] == 45

        result = analyze_convergence(conv_scores)
        # rs_score(45)는 bullish이므로 aligned_axes에 포함되어야 함
        assert "rs_score" in result["aligned_axes"]

    def test_rs_score_absent_no_error(self):
        """rs_score가 sig에 없으면 conv_scores에도 없어야 하며 에러 없이 동작."""
        sig = {
            "technical_score": 30,
            "supply_score": 20,
            "exchange_score": 10,
        }
        conv_scores = {
            "technical_score": sig["technical_score"],
            "supply_score": sig["supply_score"],
            "exchange_score": sig["exchange_score"],
        }
        for key in ("fundamentals_score", "news_score", "consensus_score",
                     "semiconductor_score", "volatility_score", "candlestick_score",
                     "global_macro_score", "rs_score"):
            if key in sig:
                conv_scores[key] = sig[key]

        assert "rs_score" not in conv_scores
        result = analyze_convergence(conv_scores)
        assert "rs_score" not in result["aligned_axes"]
