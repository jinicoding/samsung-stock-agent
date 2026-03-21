"""한국투자증권 API를 사용하여 삼성전자(005930) 주가를 조회한다."""

from datetime import datetime, timedelta

from src.data.kis_api import kis_get

STOCK_CODE = "005930"


def fetch_samsung_price() -> float:
    """삼성전자 현재가(또는 최근 종가)를 반환한다.

    조회 실패 시 RuntimeError를 발생시킨다.
    """
    try:
        data = kis_get(
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            "FHKST01010100",
            {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": STOCK_CODE},
        )
        price = int(data["output"]["stck_prpr"])
        return float(price)
    except Exception as e:
        raise RuntimeError(f"삼성전자 주가 조회 실패: {e}") from e


def fetch_samsung_ohlcv(from_date: str | None = None, to_date: str | None = None) -> list[dict]:
    """OHLCV 데이터를 dict 리스트로 반환한다.

    Args:
        from_date: 시작일 (YYYY-MM-DD). None이면 1년 전.
        to_date: 종료일 (YYYY-MM-DD). None이면 오늘.

    Returns:
        각 dict: {date, open, high, low, close, volume} 날짜 오름차순.
    """
    if to_date is None:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    try:
        all_rows = []
        current_to = to_date.replace("-", "")
        target_from = from_date.replace("-", "")

        while True:
            data = kis_get(
                "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                "FHKST03010100",
                {
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": STOCK_CODE,
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

            # 마지막 행의 날짜가 시작일 이하이면 종료
            last_date = rows[-1].get("stck_bsop_date", "")
            if not last_date or last_date <= target_from:
                break

            # 다음 페이지: 마지막 날짜 - 1일
            prev = datetime.strptime(last_date, "%Y%m%d") - timedelta(days=1)
            current_to = prev.strftime("%Y%m%d")
            if current_to < target_from:
                break

        # 중복 제거 후 날짜 오름차순 정렬
        seen = set()
        unique = []
        for r in all_rows:
            if r["date"] not in seen:
                seen.add(r["date"])
                unique.append(r)
        unique.sort(key=lambda x: x["date"])
        return unique
    except Exception as e:
        raise RuntimeError(f"삼성전자 OHLCV 조회 실패: {e}") from e
