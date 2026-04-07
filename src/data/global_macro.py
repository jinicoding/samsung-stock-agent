"""글로벌 매크로 데이터 수집: NASDAQ Composite + VIX(CBOE 변동성 지수).

Naver Finance 해외지수 페이지에서 일별 종가 데이터를 크롤링한다.
semiconductor.py의 fetch_sox_index() 패턴을 따른다.
"""

import re

import requests

NAVER_WORLD_URL = "https://finance.naver.com/world/sise.naver"

# Naver Finance 해외지수 심볼
NASDAQ_SYMBOL = "CCMP"       # NASDAQ Composite
VIX_SYMBOL = "CBOEVIX"       # CBOE Volatility Index


def fetch_nasdaq_index(days: int = 60) -> list[dict]:
    """Naver Finance에서 NASDAQ Composite 일별 데이터를 수집한다.

    Args:
        days: 수집 목표 거래일 수 (페이지 수 자동 계산, 1페이지 ≈ 10거래일).

    Returns:
        각 dict: {date, close} 날짜 오름차순. 네트워크 실패 시 빈 리스트.
    """
    pages = max(1, days // 10)
    return _fetch_index(NASDAQ_SYMBOL, pages)


def fetch_vix_index(days: int = 60) -> list[dict]:
    """Naver Finance에서 VIX(CBOE 변동성 지수) 일별 데이터를 수집한다.

    Args:
        days: 수집 목표 거래일 수 (페이지 수 자동 계산, 1페이지 ≈ 10거래일).

    Returns:
        각 dict: {date, close} 날짜 오름차순. 네트워크 실패 시 빈 리스트.
    """
    pages = max(1, days // 10)
    return _fetch_index(VIX_SYMBOL, pages)


def _fetch_index(symbol: str, pages: int) -> list[dict]:
    """Naver Finance 해외지수 페이지에서 일별 종가를 수집하는 공통 함수."""
    all_rows: list[dict] = []
    try:
        for page in range(1, pages + 1):
            resp = requests.get(
                NAVER_WORLD_URL,
                params={"symbol": symbol, "fdtc": "2", "page": page},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            if resp.status_code != 200:
                break
            rows = _parse_index_page(resp.text)
            if not rows:
                break
            all_rows.extend(rows)
    except Exception:
        return []

    seen: set[str] = set()
    unique: list[dict] = []
    for r in all_rows:
        if r["date"] not in seen:
            seen.add(r["date"])
            unique.append(r)
    unique.sort(key=lambda x: x["date"])
    return unique


def _parse_index_page(html: str) -> list[dict]:
    """Naver 해외지수 HTML에서 날짜+종가를 추출한다."""
    rows: list[dict] = []
    pattern = re.compile(
        r'<td[^>]*class="date"[^>]*>\s*(\d{4}\.\d{2}\.\d{2})\s*</td>'
        r'.*?<td[^>]*class="num"[^>]*>\s*([\d,]+\.?\d*)\s*</td>',
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        date_str = match.group(1).replace(".", "-")
        close_str = match.group(2).replace(",", "")
        try:
            close = float(close_str)
            rows.append({"date": date_str, "close": close})
        except ValueError:
            continue
    return rows
