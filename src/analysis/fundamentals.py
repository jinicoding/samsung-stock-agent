"""기본적 분석 모듈 — PER/PBR/배당수익률 기반 밸류에이션 판정.

삼성전자의 PER, PBR, 배당수익률, 추정PER을 해석하여
저평가/적정/고평가 판정과 실적 전망을 도출한다.

삼성전자 반도체 섹터 기준:
- PER: < 10 저평가, 10~15 적정, > 15 고평가
- PBR: < 1.0 저평가, 1.0~1.5 적정, > 1.5 고평가
- 배당수익률: >= 3% 매력적, 1.5~3% 보통, < 1.5% 낮음
"""


def _per_valuation(per: float | None) -> str:
    """PER 기반 밸류에이션 판정."""
    if per is None:
        return "판정불가"
    if per < 10:
        return "저평가"
    if per <= 15:
        return "적정"
    return "고평가"


def _pbr_valuation(pbr: float | None) -> str:
    """PBR 기반 밸류에이션 판정."""
    if pbr is None:
        return "판정불가"
    if pbr < 1.0:
        return "저평가"
    if pbr <= 1.5:
        return "적정"
    return "고평가"


def _earnings_outlook(per: float | None, estimated_per: float | None) -> str:
    """trailing PER vs 추정PER 비교로 실적 전망 도출.

    추정PER이 trailing PER보다 낮으면 → 실적 개선 (EPS 증가 전망)
    추정PER이 trailing PER보다 높으면 → 실적 악화 (EPS 감소 전망)
    차이가 10% 이내면 → 유지
    """
    if per is None or estimated_per is None:
        return "판정불가"
    ratio = estimated_per / per
    if ratio < 0.9:
        return "개선"
    if ratio > 1.1:
        return "악화"
    return "유지"


def _dividend_attractiveness(dividend_yield: float | None) -> str:
    """배당수익률 매력도 판정."""
    if dividend_yield is None:
        return "판정불가"
    if dividend_yield >= 3.0:
        return "매력적"
    if dividend_yield >= 1.5:
        return "보통"
    return "낮음"


def analyze_fundamentals(data: dict) -> dict:
    """기본적 분석 지표를 해석하여 밸류에이션 판정을 수행한다.

    Args:
        data: fetch_fundamentals()가 반환하는 dict
              {"per", "eps", "estimated_per", "estimated_eps",
               "pbr", "bps", "dividend_yield"}

    Returns:
        입력 데이터 + 판정 결과:
        {"per_valuation", "pbr_valuation", "earnings_outlook",
         "dividend_attractiveness"}
    """
    per = data.get("per")
    pbr = data.get("pbr")
    estimated_per = data.get("estimated_per")
    dividend_yield = data.get("dividend_yield")

    return {
        **data,
        "per_valuation": _per_valuation(per),
        "pbr_valuation": _pbr_valuation(pbr),
        "earnings_outlook": _earnings_outlook(per, estimated_per),
        "dividend_attractiveness": _dividend_attractiveness(dividend_yield),
    }
