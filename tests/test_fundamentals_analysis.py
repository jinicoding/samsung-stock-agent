"""기본적 분석 모듈 테스트."""

import pytest

from src.analysis.fundamentals import analyze_fundamentals


def _make_data(**overrides) -> dict:
    """테스트용 기본 데이터 생성."""
    base = {
        "per": 12.0,
        "eps": 5000,
        "estimated_per": 10.0,
        "estimated_eps": 6000,
        "pbr": 1.2,
        "bps": 50000,
        "dividend_yield": 2.5,
    }
    base.update(overrides)
    return base


class TestPERValuation:
    """PER 기반 밸류에이션 판정."""

    def test_per_undervalued(self):
        """PER < 10 → 저평가."""
        result = analyze_fundamentals(_make_data(per=8.0))
        assert result["per_valuation"] == "저평가"

    def test_per_fair(self):
        """10 <= PER <= 15 → 적정."""
        result = analyze_fundamentals(_make_data(per=12.0))
        assert result["per_valuation"] == "적정"

    def test_per_overvalued(self):
        """PER > 15 → 고평가."""
        result = analyze_fundamentals(_make_data(per=20.0))
        assert result["per_valuation"] == "고평가"

    def test_per_none(self):
        """PER이 None이면 판정 불가."""
        result = analyze_fundamentals(_make_data(per=None))
        assert result["per_valuation"] == "판정불가"


class TestPBRValuation:
    """PBR 기반 밸류에이션 판정."""

    def test_pbr_undervalued(self):
        """PBR < 1.0 → 저평가."""
        result = analyze_fundamentals(_make_data(pbr=0.8))
        assert result["pbr_valuation"] == "저평가"

    def test_pbr_fair(self):
        """1.0 <= PBR <= 1.5 → 적정."""
        result = analyze_fundamentals(_make_data(pbr=1.2))
        assert result["pbr_valuation"] == "적정"

    def test_pbr_overvalued(self):
        """PBR > 1.5 → 고평가."""
        result = analyze_fundamentals(_make_data(pbr=2.5))
        assert result["pbr_valuation"] == "고평가"

    def test_pbr_none(self):
        result = analyze_fundamentals(_make_data(pbr=None))
        assert result["pbr_valuation"] == "판정불가"


class TestEarningsOutlook:
    """trailing PER vs 추정PER 비교 — 실적 전망."""

    def test_earnings_improving(self):
        """추정PER < trailing PER → 실적 개선 전망."""
        result = analyze_fundamentals(_make_data(per=15.0, estimated_per=10.0))
        assert result["earnings_outlook"] == "개선"

    def test_earnings_stable(self):
        """추정PER ≈ trailing PER → 실적 유지."""
        result = analyze_fundamentals(_make_data(per=12.0, estimated_per=11.5))
        assert result["earnings_outlook"] == "유지"

    def test_earnings_deteriorating(self):
        """추정PER > trailing PER → 실적 악화 전망."""
        result = analyze_fundamentals(_make_data(per=10.0, estimated_per=15.0))
        assert result["earnings_outlook"] == "악화"

    def test_earnings_missing_data(self):
        """데이터 없으면 판정불가."""
        result = analyze_fundamentals(_make_data(per=None, estimated_per=10.0))
        assert result["earnings_outlook"] == "판정불가"

    def test_earnings_missing_estimated(self):
        result = analyze_fundamentals(_make_data(per=12.0, estimated_per=None))
        assert result["earnings_outlook"] == "판정불가"


class TestDividendAttractiveness:
    """배당수익률 매력도 판정."""

    def test_high_dividend(self):
        """배당수익률 >= 3% → 매력적."""
        result = analyze_fundamentals(_make_data(dividend_yield=3.5))
        assert result["dividend_attractiveness"] == "매력적"

    def test_moderate_dividend(self):
        """1.5% <= 배당수익률 < 3% → 보통."""
        result = analyze_fundamentals(_make_data(dividend_yield=2.0))
        assert result["dividend_attractiveness"] == "보통"

    def test_low_dividend(self):
        """배당수익률 < 1.5% → 낮음."""
        result = analyze_fundamentals(_make_data(dividend_yield=0.5))
        assert result["dividend_attractiveness"] == "낮음"

    def test_dividend_none(self):
        result = analyze_fundamentals(_make_data(dividend_yield=None))
        assert result["dividend_attractiveness"] == "판정불가"


class TestOutputStructure:
    """분석 결과 구조 확인."""

    def test_all_keys_present(self):
        result = analyze_fundamentals(_make_data())
        expected_keys = {
            "per", "eps", "estimated_per", "estimated_eps",
            "pbr", "bps", "dividend_yield",
            "per_valuation", "pbr_valuation",
            "earnings_outlook", "dividend_attractiveness",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_raw_values_passed_through(self):
        data = _make_data(per=12.5, eps=5500)
        result = analyze_fundamentals(data)
        assert result["per"] == 12.5
        assert result["eps"] == 5500
