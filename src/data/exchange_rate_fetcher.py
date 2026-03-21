"""한국투자증권 API를 사용하여 USD/KRW 환율을 조회한다."""

from datetime import datetime, timedelta

from src.data.kis_api import kis_get


def fetch_usdkrw_ohlc(from_date: str | None = None, to_date: str | None = None) -> list[dict]:
    """USD/KRW OHLC 데이터를 dict 리스트로 반환한다.

    Args:
        from_date: 시작일 (YYYY-MM-DD). None이면 1년 전.
        to_date: 종료일 (YYYY-MM-DD). None이면 오늘.

    Returns:
        [{"date", "open", "high", "low", "close"}, ...] 날짜 오름차순.
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
                "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice",
                "FHKST03030100",
                {
                    "FID_COND_MRKT_DIV_CODE": "X",
                    "FID_INPUT_ISCD": "FX@KRW",
                    "FID_INPUT_DATE_1": target_from,
                    "FID_INPUT_DATE_2": current_to,
                    "FID_PERIOD_DIV_CODE": "D",
                },
            )

            rows = data.get("output2", [])
            if not rows:
                break

            for r in rows:
                d = r.get("stck_bsop_date", "")
                if not d or d < target_from:
                    continue
                close_str = r.get("ovrs_nmix_prpr", "")
                if not close_str:
                    continue
                all_rows.append({
                    "date": f"{d[:4]}-{d[4:6]}-{d[6:]}",
                    "open": float(r.get("ovrs_nmix_oprc", 0)),
                    "high": float(r.get("ovrs_nmix_hgpr", 0)),
                    "low": float(r.get("ovrs_nmix_lwpr", 0)),
                    "close": float(close_str),
                })

            last_date = rows[-1].get("stck_bsop_date", "")
            if not last_date or last_date <= target_from:
                break

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
        raise RuntimeError(f"USD/KRW 환율 조회 실패: {e}") from e
