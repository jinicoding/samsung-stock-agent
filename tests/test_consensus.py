"""증권사 컨센서스 데이터 수집 모듈 테스트."""

import pytest
from unittest.mock import patch, MagicMock

from src.data.consensus import (
    fetch_consensus,
    analyze_consensus,
    classify_research_tone,
)


# ---------------------------------------------------------------------------
# analyze_consensus 테스트
# ---------------------------------------------------------------------------

class TestAnalyzeConsensus:
    """컨센서스 분석 로직 테스트."""

    def test_divergence_calculation(self):
        """목표가 괴리율 계산이 정확해야 한다."""
        raw = {"target_price": 250000, "recommendation": 4.0, "researches": []}
        result = analyze_consensus(raw, current_price=200000)
        assert result["divergence_pct"] == pytest.approx(25.0)

    def test_valuation_undervalued(self):
        """괴리율 >30% → 저평가."""
        raw = {"target_price": 260000, "recommendation": 4.0, "researches": []}
        result = analyze_consensus(raw, current_price=180000)
        assert result["divergence_pct"] > 30
        assert result["valuation"] == "저평가"

    def test_valuation_fair_low(self):
        """괴리율 10~30% → 적정하단."""
        raw = {"target_price": 220000, "recommendation": 4.0, "researches": []}
        result = analyze_consensus(raw, current_price=200000)
        assert 10 <= result["divergence_pct"] <= 30
        assert result["valuation"] == "적정하단"

    def test_valuation_fair(self):
        """괴리율 -10~10% → 적정."""
        raw = {"target_price": 205000, "recommendation": 4.0, "researches": []}
        result = analyze_consensus(raw, current_price=200000)
        assert -10 <= result["divergence_pct"] <= 10
        assert result["valuation"] == "적정"

    def test_valuation_overvalued(self):
        """괴리율 <-10% → 고평가."""
        raw = {"target_price": 170000, "recommendation": 4.0, "researches": []}
        result = analyze_consensus(raw, current_price=200000)
        assert result["divergence_pct"] < -10
        assert result["valuation"] == "고평가"

    def test_recommendation_strong_buy(self):
        """추천 ≥4.5 → 매수."""
        raw = {"target_price": 250000, "recommendation": 4.7, "researches": []}
        result = analyze_consensus(raw, current_price=200000)
        assert result["recommendation_label"] == "매수"

    def test_recommendation_buy(self):
        """추천 3.5~4.5 → 매수유지."""
        raw = {"target_price": 250000, "recommendation": 4.0, "researches": []}
        result = analyze_consensus(raw, current_price=200000)
        assert result["recommendation_label"] == "매수유지"

    def test_recommendation_neutral(self):
        """추천 2.5~3.5 → 중립."""
        raw = {"target_price": 250000, "recommendation": 3.0, "researches": []}
        result = analyze_consensus(raw, current_price=200000)
        assert result["recommendation_label"] == "중립"

    def test_recommendation_sell(self):
        """추천 <2.5 → 매도."""
        raw = {"target_price": 250000, "recommendation": 2.0, "researches": []}
        result = analyze_consensus(raw, current_price=200000)
        assert result["recommendation_label"] == "매도"

    def test_zero_current_price_returns_none(self):
        """현재가 0이면 None 반환."""
        raw = {"target_price": 250000, "recommendation": 4.0, "researches": []}
        result = analyze_consensus(raw, current_price=0)
        assert result is None

    def test_none_raw_returns_none(self):
        """raw가 None이면 None 반환."""
        result = analyze_consensus(None, current_price=200000)
        assert result is None

    def test_researches_passed_through(self):
        """리서치 리스트가 결과에 포함된다."""
        researches = [
            {"title": "삼성전자 실적 개선", "broker": "삼성증권", "date": "2026-03-28"},
        ]
        raw = {"target_price": 250000, "recommendation": 4.0, "researches": researches}
        result = analyze_consensus(raw, current_price=200000)
        assert len(result["researches"]) == 1
        assert result["researches"][0]["title"] == "삼성전자 실적 개선"


# ---------------------------------------------------------------------------
# classify_research_tone 테스트
# ---------------------------------------------------------------------------

class TestClassifyResearchTone:
    """리포트 제목 키워드 기반 톤 분류 테스트."""

    def test_positive_keywords(self):
        """긍정 키워드가 있으면 긍정."""
        researches = [
            {"title": "삼성전자 실적 상향 기대"},
            {"title": "목표가 상향"},
        ]
        assert classify_research_tone(researches) == "긍정"

    def test_negative_keywords(self):
        """부정 키워드가 있으면 부정."""
        researches = [
            {"title": "삼성전자 하향 조정"},
            {"title": "실적 부진 우려"},
        ]
        assert classify_research_tone(researches) == "부정"

    def test_neutral(self):
        """긍정·부정 키워드가 없으면 중립."""
        researches = [
            {"title": "삼성전자 분기 실적 발표"},
        ]
        assert classify_research_tone(researches) == "중립"

    def test_empty_researches(self):
        """빈 리스트면 중립."""
        assert classify_research_tone([]) == "중립"


# ---------------------------------------------------------------------------
# fetch_consensus 테스트 (API 모킹)
# ---------------------------------------------------------------------------

class TestFetchConsensus:
    """네이버 API 호출 모킹 테스트."""

    @patch("src.data.consensus.requests.get")
    def test_fetch_success(self, mock_get):
        """정상 응답 시 파싱된 dict를 반환."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "consensusInfo": {
                "priceTargetMean": "252720",
                "recommMean": "4.20",
            },
            "researches": [
                {"title": "삼성전자 목표가 상향", "brokerName": "삼성증권", "date": "2026-03-28"},
                {"title": "반도체 수요 회복", "brokerName": "미래에셋", "date": "2026-03-27"},
            ],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_consensus()
        assert result is not None
        assert result["target_price"] == 252720.0
        assert result["recommendation"] == pytest.approx(4.20)
        assert len(result["researches"]) == 2

    @patch("src.data.consensus.requests.get")
    def test_fetch_comma_separated_price(self, mock_get):
        """실제 API는 '288,000' 형태의 쉼표 포함 문자열을 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "consensusInfo": {
                "priceTargetMean": "288,000",
                "recommMean": "4.00",
            },
            "researches": [],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_consensus()
        assert result is not None
        assert result["target_price"] == 288000.0
        assert result["recommendation"] == 4.0

    @patch("src.data.consensus.requests.get")
    def test_fetch_failure_returns_none(self, mock_get):
        """API 실패 시 None 반환."""
        mock_get.side_effect = Exception("네트워크 오류")
        result = fetch_consensus()
        assert result is None

    @patch("src.data.consensus.requests.get")
    def test_fetch_missing_consensus_info(self, mock_get):
        """consensusInfo 없으면 None 반환."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_consensus()
        assert result is None
