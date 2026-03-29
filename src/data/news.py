"""Naver 모바일 증권 API를 활용한 삼성전자 뉴스 헤드라인 수집 및 감정 분류."""

import html
import logging

import requests

logger = logging.getLogger(__name__)

STOCK_CODE = "005930"
NAVER_NEWS_URL = f"https://m.stock.naver.com/api/news/stock/{STOCK_CODE}"

# --- 감정 분류 키워드 사전 ---

POSITIVE_KEYWORDS = [
    "실적개선", "상승", "반등", "목표가상향", "호실적",
    "최고", "성장", "개선", "흑자", "수혜",
    "강세", "돌파", "매수", "회복", "확대",
]

NEGATIVE_KEYWORDS = [
    "하락", "매도", "적자", "리스크", "전쟁",
    "약세", "우려", "감소", "둔화", "위기",
    "손실", "폭락", "급락", "하향", "부진",
]


def classify_sentiment(title: str) -> str:
    """헤드라인 제목에서 키워드 기반 감정을 분류한다.

    Returns:
        "positive", "negative", 또는 "neutral"
    """
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in title)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in title)

    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


def fetch_news_headlines(count: int = 20) -> list[dict]:
    """삼성전자 뉴스 헤드라인을 수집하고 감정을 분류한다.

    Args:
        count: 가져올 뉴스 개수 (기본 20)

    Returns:
        [{"title", "source", "date", "sentiment"}, ...] 또는 실패 시 []
    """
    try:
        resp = requests.get(
            NAVER_NEWS_URL,
            params={"pageSize": count, "page": 1},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("뉴스 수집 실패: %s", e)
        return []

    items = data.get("items", [])
    headlines = []
    for item in items:
        title = html.unescape(item.get("title", ""))
        headlines.append({
            "title": title,
            "source": item.get("officeName", ""),
            "date": item.get("datetime", ""),
            "sentiment": classify_sentiment(title),
        })

    return headlines


def summarize_sentiment(headlines: list[dict]) -> dict:
    """헤드라인 리스트의 전체 감정을 요약한다.

    Returns:
        {"label": "bullish"|"bearish"|"neutral",
         "score": int, "positive": int, "negative": int, "neutral": int, "count": int}
    """
    if not headlines:
        return {"label": "neutral", "score": 0, "positive": 0, "negative": 0, "neutral": 0, "count": 0}

    pos = sum(1 for h in headlines if h.get("sentiment") == "positive")
    neg = sum(1 for h in headlines if h.get("sentiment") == "negative")
    neu = sum(1 for h in headlines if h.get("sentiment") == "neutral")
    score = pos - neg

    if score > 0:
        label = "bullish"
    elif score < 0:
        label = "bearish"
    else:
        label = "neutral"

    return {
        "label": label,
        "score": score,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "count": len(headlines),
    }
