"""반도체 업황 데이터 수집: SK하이닉스 주가 + 필라델피아 반도체 지수(SOX).

SK하이닉스(000660)는 KIS API로, SOX는 Naver Finance 해외지수 페이지에서 수집한다.
"""

import re
from datetime import datetime, timedelta

import requests

from src.data.kis_api import kis_get

SKHYNIX_CODE = "000660"
SOX_NAVER_URL = "https://finance.naver.com/world/sise.naver"
SOX_SYMBOL = "SPI@SPX"  # Naver에서 SOX 심볼 (PHLX Semiconductor)


def fetch_skhynix_price() -> float:
    """SK하이닉스 현재가(또는 최근 종가)를 반환한다."""
    try:
        data = kis_get(
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            "FHKST01010100",
            {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": SKHYNIX_CODE},
        )
        price = int(data["output"]["stck_prpr"])
        return float(price)
    except Exception as e:
        raise RuntimeError(f"SK하이닉스 주가 조회 실패: {e}") from e


def fetch_skhynix_ohlcv(
    from_date: str | None = None, to_date: str | None = None,
) -> list[dict]:
    """SK하이닉스 OHLCV 데이터를 dict 리스트로 반환한다 (날짜 오름차순).

    Args:
        from_date: 시작일 (YYYY-MM-DD). None이면 1년 전.
        to_date: 종료일 (YYYY-MM-DD). None이면 오늘.
    """
    if to_date is None:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    try:
        all_rows: list[dict] = []
        current_to = to_date.replace("-", "")
        target_from = from_date.replace("-", "")

        while True:
            data = kis_get(
                "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                "FHKST03010100",
                {
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": SKHYNIX_CODE,
                    "FID_INPUT_DATE_1": target_from,
                    "FID_INPUT_DATE_2": current_to,
                    "FID_PERIOD_DIV_CODE": "D",
                    "FID_ORG_ADJ_PRC": "0",
                },
            )

            rows = data.get("output2", [])
            if not rows:
                break

            for r in rows:
                d = r.get("stck_bsop_date", "")
                if not d or d < target_from:
                    continue
                close = int(r.get("stck_clpr", 0))
                if close == 0:
                    continue
                all_rows.append({
                    "date": f"{d[:4]}-{d[4:6]}-{d[6:]}",
                    "open": float(int(r.get("stck_oprc", 0))),
                    "high": float(int(r.get("stck_hgpr", 0))),
                    "low": float(int(r.get("stck_lwpr", 0))),
                    "close": float(close),
                    "volume": int(r.get("acml_vol", 0)),
                })

            last_date = rows[-1].get("stck_bsop_date", "")
            if not last_date or last_date <= target_from:
                break

            prev = datetime.strptime(last_date, "%Y%m%d") - timedelta(days=1)
            current_to = prev.strftime("%Y%m%d")
            if current_to < target_from:
                break

        seen: set[str] = set()
        unique: list[dict] = []
        for r in all_rows:
            if r["date"] not in seen:
                seen.add(r["date"])
                unique.append(r)
        unique.sort(key=lambda x: x["date"])
        return unique
    except Exception as e:
        raise RuntimeError(f"SK하이닉스 OHLCV 조회 실패: {e}") from e


def fetch_sox_index(pages: int = 3) -> list[dict]:
    """Naver Finance에서 필라델피아 반도체 지수(SOX) 일별 데이터를 수집한다.

    Args:
        pages: 수집할 페이지 수 (1페이지 ≈ 10거래일).

    Returns:
        각 dict: {date, close} 날짜 오름차순. 네트워크 실패 시 빈 리스트.
    """
    all_rows: list[dict] = []
    try:
        for page in range(1, pages + 1):
            resp = requests.get(
                SOX_NAVER_URL,
                params={"symbol": "SPI@SOX", "fdtc": "2", "page": page},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            if resp.status_code != 200:
                break
            rows = _parse_sox_page(resp.text)
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


def _parse_sox_page(html: str) -> list[dict]:
    """Naver 해외지수 HTML에서 날짜+종가를 추출한다."""
    rows: list[dict] = []
    # Naver 해외지수 테이블: 날짜(YYYY.MM.DD), 종가, 전일비, 등락률, 시가, 고가, 저가
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
