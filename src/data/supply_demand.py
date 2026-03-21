"""삼성전자(005930) 외국인/기관 매매 동향을 조회한다.

매매 데이터: 한국투자증권 API (inquire-investor)
보유비율: Naver Finance HTML 파싱 (KIS API 미제공)
"""

import re
import time

import requests

from src.data.kis_api import kis_get

STOCK_CODE = "005930"
FRGN_URL = "https://finance.naver.com/item/frgn.naver"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def _safe_int(value: str) -> int:
    """빈 문자열이나 비숫자를 0으로 처리한다."""
    if not value or not value.lstrip("-").isdigit():
        return 0
    return int(value)


# ── KIS API: 매매 데이터 ──────────────────────────────────────


def fetch_foreign_trading(from_date: str, to_date: str) -> list[dict]:
    """외국인/기관 순매매 데이터를 KIS API로 조회한다.

    Args:
        from_date: 시작일 (YYYY-MM-DD)
        to_date: 종료일 (YYYY-MM-DD)

    Returns:
        [{"date", "institution", "foreign_total", "individual", "other_corp"}, ...]
        날짜 오름차순.
    """
    data = kis_get(
        "/uapi/domestic-stock/v1/quotations/inquire-investor",
        "FHKST01010900",
        {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": STOCK_CODE},
    )

    rows = []
    for r in data.get("output", []):
        d = r.get("stck_bsop_date", "")
        if not d:
            continue
        date_str = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        if date_str < from_date or date_str > to_date:
            continue

        frgn = _safe_int(r.get("frgn_ntby_qty", ""))
        orgn = _safe_int(r.get("orgn_ntby_qty", ""))
        prsn = _safe_int(r.get("prsn_ntby_qty", ""))

        # 당일 장중에는 빈 값이 올 수 있음 — 건너뜀
        if frgn == 0 and orgn == 0 and prsn == 0:
            continue

        rows.append({
            "date": date_str,
            "institution": orgn,
            "foreign_total": frgn,
            "individual": prsn,
            "other_corp": 0,
        })

    rows.sort(key=lambda x: x["date"])
    return rows


# ── Naver Finance: 보유비율 ───────────────────────────────────


def _parse_int(text: str) -> int:
    """쉼표/부호가 포함된 문자열을 int로 변환한다."""
    return int(text.replace(",", "").replace("+", ""))


def _parse_frgn_page(page: int) -> list[dict]:
    """Naver Finance 외국인/기관 매매 동향 페이지를 파싱한다."""
    resp = requests.get(FRGN_URL, headers=HEADERS, params={"code": STOCK_CODE, "page": page})
    resp.raise_for_status()

    text = resp.text
    first = text.find("type2")
    if first == -1:
        return []
    second = text.find("type2", first + 1)
    if second == -1:
        return []
    table_end = text.find("</table>", second)
    chunk = text[second - 100: table_end + 10]

    trs = re.findall(r"<tr[^>]*>(.*?)</tr>", chunk, re.S)
    rows = []
    for tr in trs:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        cells = [re.sub(r"<[^>]+>", "", td).strip() for td in tds]
        cells = [" ".join(c.split()) for c in cells]

        if len(cells) < 9:
            continue
        if not re.match(r"\d{4}\.\d{2}\.\d{2}", cells[0]):
            continue

        date_str = cells[0].replace(".", "-")
        rows.append({
            "date": date_str,
            "foreign_shares": _parse_int(cells[7]),
            "ownership_pct": float(cells[8].replace("%", "")),
        })

    return rows


def fetch_foreign_ownership(date: str) -> dict | None:
    """특정 날짜의 외국인 보유비율을 Naver Finance에서 조회한다."""
    page = 1
    max_pages = 60

    while page <= max_pages:
        rows = _parse_frgn_page(page)
        if not rows:
            return None

        for r in rows:
            if r["date"] == date:
                return {
                    "date": date,
                    "listed_shares": 0,
                    "foreign_shares": r["foreign_shares"],
                    "ownership_pct": r["ownership_pct"],
                    "limit_shares": 0,
                    "exhaustion_pct": 0.0,
                }
            if r["date"] < date:
                return None

        page += 1
        time.sleep(0.3)

    return None


def _fetch_naver_ownership_pages(from_date: str, to_date: str) -> list[dict]:
    """Naver Finance에서 보유비율 데이터를 페이지네이션하여 수집한다."""
    all_rows = []
    page = 1
    max_pages = 60

    while page <= max_pages:
        rows = _parse_frgn_page(page)
        if not rows:
            break

        for r in rows:
            if r["date"] < from_date:
                all_rows.sort(key=lambda x: x["date"])
                return [{
                    "date": r["date"],
                    "listed_shares": 0,
                    "foreign_shares": r["foreign_shares"],
                    "ownership_pct": r["ownership_pct"],
                    "limit_shares": 0,
                    "exhaustion_pct": 0.0,
                } for r in all_rows if from_date <= r["date"] <= to_date]

            if r["date"] <= to_date:
                all_rows.append(r)

        page += 1
        time.sleep(0.3)

    all_rows.sort(key=lambda x: x["date"])
    return [{
        "date": r["date"],
        "listed_shares": 0,
        "foreign_shares": r["foreign_shares"],
        "ownership_pct": r["ownership_pct"],
        "limit_shares": 0,
        "exhaustion_pct": 0.0,
    } for r in all_rows if from_date <= r["date"] <= to_date]


# ── 통합 인터페이스 ──────────────────────────────────────────


def fetch_foreign_trading_all_pages(from_date: str, to_date: str) -> tuple[list[dict], list[dict]]:
    """외국인 매매(KIS API) + 보유비율(Naver)을 동시 수집한다.

    Args:
        from_date: 시작일 (YYYY-MM-DD)
        to_date: 종료일 (YYYY-MM-DD)

    Returns:
        (trading_rows, ownership_rows) 튜플, 각각 날짜 오름차순.
    """
    trading_rows = fetch_foreign_trading(from_date, to_date)
    ownership_rows = _fetch_naver_ownership_pages(from_date, to_date)

    return trading_rows, ownership_rows
