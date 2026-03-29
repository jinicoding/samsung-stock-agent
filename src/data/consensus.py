"""네이버 증권 통합 API를 활용한 증권사 컨센서스 데이터 수집 및 분석."""

import logging

import requests

logger = logging.getLogger(__name__)

STOCK_CODE = "005930"
NAVER_INTEGRATION_URL = f"https://m.stock.naver.com/api/stock/{STOCK_CODE}/integration"

# --- 리포트 제목 톤 분류 키워드 ---

POSITIVE_KEYWORDS = [
    "상향", "호실적", "성장", "개선", "회복",
    "확대", "상승", "강세", "수혜", "기대",
]

NEGATIVE_KEYWORDS = [
    "하향", "부진", "둔화", "감소", "우려",
    "하락", "약세", "리스크", "위기", "축소",
]


def classify_research_tone(researches: list[dict]) -> str:
    """리포트 제목 키워드로 증권가 톤을 파악한다.

    Returns:
        "긍정", "부정", 또는 "중립"
    """
    if not researches:
        return "중립"

    pos = 0
    neg = 0
    for r in researches:
        title = r.get("title", "")
        pos += sum(1 for kw in POSITIVE_KEYWORDS if kw in title)
        neg += sum(1 for kw in NEGATIVE_KEYWORDS if kw in title)

    if pos > neg:
        return "긍정"
    elif neg > pos:
        return "부정"
    return "중립"


def fetch_consensus() -> dict | None:
    """네이버 증권 통합 API에서 컨센서스 데이터를 수집한다.

    Returns:
        {"target_price": float, "recommendation": float, "researches": list[dict]}
        또는 실패 시 None.
    """
    try:
        resp = requests.get(
            NAVER_INTEGRATION_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("컨센서스 수집 실패: %s", e)
        return None

    consensus_info = data.get("consensusInfo")
    if not consensus_info:
        return None

    try:
        target_price = float(consensus_info.get("priceTargetMean", 0))
        recommendation = float(consensus_info.get("recommMean", 0))
    except (ValueError, TypeError):
        logger.warning("컨센서스 데이터 파싱 실패")
        return None

    if target_price == 0:
        return None

    raw_researches = data.get("researches", [])
    researches = []
    for r in raw_researches[:5]:
        researches.append({
            "title": r.get("title", ""),
            "broker": r.get("brokerName", ""),
            "date": r.get("date", ""),
        })

    return {
        "target_price": target_price,
        "recommendation": recommendation,
        "researches": researches,
    }


def analyze_consensus(raw: dict | None, current_price: float) -> dict | None:
    """컨센서스 데이터를 분석한다.

    Args:
        raw: fetch_consensus() 반환값.
        current_price: 현재 주가.

    Returns:
        분석 결과 dict 또는 None.
    """
    if raw is None or current_price <= 0:
        return None

    target = raw["target_price"]
    recommendation = raw["recommendation"]
    researches = raw.get("researches", [])

    # 목표가 괴리율 (%)
    divergence_pct = (target - current_price) / current_price * 100

    # 밸류에이션 판단
    if divergence_pct > 30:
        valuation = "저평가"
    elif divergence_pct >= 10:
        valuation = "적정하단"
    elif divergence_pct >= -10:
        valuation = "적정"
    else:
        valuation = "고평가"

    # 투자의견 해석
    if recommendation >= 4.5:
        recommendation_label = "매수"
    elif recommendation >= 3.5:
        recommendation_label = "매수유지"
    elif recommendation >= 2.5:
        recommendation_label = "중립"
    else:
        recommendation_label = "매도"

    # 리포트 톤
    research_tone = classify_research_tone(researches)

    return {
        "target_price": target,
        "current_price": current_price,
        "divergence_pct": divergence_pct,
        "valuation": valuation,
        "recommendation": recommendation,
        "recommendation_label": recommendation_label,
        "researches": researches,
        "research_tone": research_tone,
    }
