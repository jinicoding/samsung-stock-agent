"""뉴스 헤드라인 수집기 테스트 — API 모킹으로 오프라인 실행 보장."""

import json
from unittest.mock import patch, MagicMock

import pytest

from src.data.news import (
    fetch_news_headlines,
    classify_sentiment,
    summarize_sentiment,
    POSITIVE_KEYWORDS,
    NEGATIVE_KEYWORDS,
)


# --- 모킹용 샘플 응답 ---

SAMPLE_API_RESPONSE = {
    "items": [
        {
            "title": "삼성전자, 1분기 실적개선 기대감에 상승",
            "officeName": "한국경제",
            "datetime": "2026-03-29 09:00:00",
        },
        {
            "title": "삼성전자 목표가상향... 증권사 &quot;긍정적&quot;",
            "officeName": "매일경제",
            "datetime": "2026-03-29 08:30:00",
        },
        {
            "title": "반도체 업황 리스크 확대, 삼성전자 하락 우려",
            "officeName": "조선비즈",
            "datetime": "2026-03-29 08:00:00",
        },
        {
            "title": "삼성전자, 갤럭시 신제품 공개 일정 확정",
            "officeName": "전자신문",
            "datetime": "2026-03-28 17:00:00",
        },
    ]
}


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


class TestClassifySentiment:
    """개별 헤드라인 감정 분류 테스트."""

    def test_positive(self):
        assert classify_sentiment("삼성전자 실적개선 기대") == "positive"

    def test_negative(self):
        assert classify_sentiment("삼성전자 하락 리스크 확대") == "negative"

    def test_neutral(self):
        assert classify_sentiment("삼성전자 갤럭시 신제품 공개") == "neutral"

    def test_mixed_defaults_to_stronger(self):
        # 부정이 더 많으면 negative
        result = classify_sentiment("하락 리스크 속 반등 기대")
        # 긍정: 반등(1), 부정: 하락, 리스크(2) → negative
        assert result == "negative"

    def test_mixed_equal_is_neutral(self):
        # 긍정과 부정이 같으면 neutral
        result = classify_sentiment("상승 기대 vs 하락 전망")
        # 긍정: 상승(1), 부정: 하락(1) → neutral
        assert result == "neutral"


class TestFetchNewsHeadlines:
    """뉴스 헤드라인 가져오기 테스트."""

    @patch("src.data.news.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_API_RESPONSE)
        headlines = fetch_news_headlines()

        assert len(headlines) == 4
        assert headlines[0]["title"] == "삼성전자, 1분기 실적개선 기대감에 상승"
        assert headlines[0]["source"] == "한국경제"
        assert headlines[0]["date"] == "2026-03-29 09:00:00"
        assert headlines[0]["sentiment"] in ("positive", "negative", "neutral")

    @patch("src.data.news.requests.get")
    def test_html_entity_decoding(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_API_RESPONSE)
        headlines = fetch_news_headlines()

        # &quot; → "
        assert "&quot;" not in headlines[1]["title"]
        assert '"' in headlines[1]["title"]

    @patch("src.data.news.requests.get")
    def test_api_failure_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        headlines = fetch_news_headlines()
        assert headlines == []

    @patch("src.data.news.requests.get")
    def test_list_response_format(self, mock_get):
        """실제 Naver API는 [{"total": N, "items": [...]}] 형태를 반환한다."""
        list_response = [{"total": 4, "items": SAMPLE_API_RESPONSE["items"]}]
        mock_get.return_value = _mock_response(list_response)
        headlines = fetch_news_headlines()
        assert len(headlines) == 4
        assert headlines[0]["title"] == "삼성전자, 1분기 실적개선 기대감에 상승"

    @patch("src.data.news.requests.get")
    def test_custom_count(self, mock_get):
        mock_get.return_value = _mock_response(SAMPLE_API_RESPONSE)
        fetch_news_headlines(count=10)
        call_params = mock_get.call_args
        assert "10" in str(call_params) or 10 in call_params[1].get("params", {}).values()


class TestSummarizeSentiment:
    """전체 감정 요약 테스트."""

    def test_bullish(self):
        headlines = [
            {"sentiment": "positive"},
            {"sentiment": "positive"},
            {"sentiment": "positive"},
            {"sentiment": "neutral"},
        ]
        summary = summarize_sentiment(headlines)
        assert summary["label"] == "bullish"
        assert summary["score"] > 0

    def test_bearish(self):
        headlines = [
            {"sentiment": "negative"},
            {"sentiment": "negative"},
            {"sentiment": "negative"},
            {"sentiment": "neutral"},
        ]
        summary = summarize_sentiment(headlines)
        assert summary["label"] == "bearish"
        assert summary["score"] < 0

    def test_neutral(self):
        headlines = [
            {"sentiment": "positive"},
            {"sentiment": "negative"},
        ]
        summary = summarize_sentiment(headlines)
        assert summary["label"] == "neutral"
        assert summary["score"] == 0

    def test_empty(self):
        summary = summarize_sentiment([])
        assert summary["label"] == "neutral"
        assert summary["score"] == 0
        assert summary["count"] == 0

    def test_counts(self):
        headlines = [
            {"sentiment": "positive"},
            {"sentiment": "negative"},
            {"sentiment": "neutral"},
        ]
        summary = summarize_sentiment(headlines)
        assert summary["positive"] == 1
        assert summary["negative"] == 1
        assert summary["neutral"] == 1
        assert summary["count"] == 3


class TestKeywords:
    """키워드 사전 존재 확인."""

    def test_positive_keywords_exist(self):
        assert len(POSITIVE_KEYWORDS) >= 5

    def test_negative_keywords_exist(self):
        assert len(NEGATIVE_KEYWORDS) >= 5
