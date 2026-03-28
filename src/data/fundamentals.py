"""삼성전자(005930) 기본적 분석 지표를 Naver Finance에서 수집한다.

PER, 추정PER, PBR, 배당수익률, EPS, BPS를 스크래핑한다.
"""

import re

import requests

STOCK_CODE = "005930"
MAIN_URL = "https://finance.naver.com/item/main.naver"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def _parse_em_by_id(html: str, em_id: str) -> str | None:
    """id 속성으로 em 태그 값을 추출한다."""
    pattern = rf'<em\s+id="{em_id}"[^>]*>(.*?)</em>'
    m = re.search(pattern, html)
    if m:
        return m.group(1).strip()
    return None


def _parse_float(text: str | None) -> float | None:
    """문자열을 float로 변환. N/A나 빈 값은 None."""
    if not text or text.strip() in ("N/A", "-", ""):
        return None
    cleaned = text.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_int(text: str | None) -> int | None:
    """문자열을 int로 변환. N/A나 빈 값은 None."""
    if not text or text.strip() in ("N/A", "-", ""):
        return None
    cleaned = text.replace(",", "")
    try:
        return int(cleaned)
    except ValueError:
        return None


def _parse_bps(html: str) -> int | None:
    """PBR/BPS 행에서 BPS 값을 추출한다.

    BPS는 id가 없는 em 태그로, PBR 행의 두 번째 em에 위치한다.
    """
    # PBR/BPS 섹션 찾기
    pbr_match = re.search(r'PBR.*?BPS.*?<td>(.*?)</td>', html, re.S)
    if not pbr_match:
        return None
    td_content = pbr_match.group(1)
    # td 안의 모든 em 태그 추출
    ems = re.findall(r'<em[^>]*>(.*?)</em>', td_content)
    if len(ems) >= 2:
        return _parse_int(ems[1])
    return None


def parse_fundamentals_html(html: str) -> dict:
    """HTML에서 기본적 분석 지표를 파싱한다.

    Returns:
        {"per", "eps", "estimated_per", "estimated_eps",
         "pbr", "bps", "dividend_yield"} — 값이 없으면 None.
    """
    return {
        "per": _parse_float(_parse_em_by_id(html, "_per")),
        "eps": _parse_int(_parse_em_by_id(html, "_eps")),
        "estimated_per": _parse_float(_parse_em_by_id(html, "_cns_per")),
        "estimated_eps": _parse_int(_parse_em_by_id(html, "_cns_eps")),
        "pbr": _parse_float(_parse_em_by_id(html, "_pbr")),
        "bps": _parse_bps(html),
        "dividend_yield": _parse_float(_parse_em_by_id(html, "_dvr")),
    }


def fetch_fundamentals() -> dict | None:
    """Naver Finance에서 삼성전자 기본적 분석 지표를 조회한다.

    Returns:
        parse_fundamentals_html() 결과 dict, 실패 시 None.
    """
    try:
        resp = requests.get(
            MAIN_URL, headers=HEADERS, params={"code": STOCK_CODE}, timeout=10
        )
        resp.raise_for_status()
        return parse_fundamentals_html(resp.text)
    except Exception:
        return None
