"""USD/KRW 환율 분석 모듈.

환율 현재가·등락률, 이동평균·추세 판정, 주가-환율 상관관계를 계산한다.
삼성전자는 매출의 ~80%가 해외에서 발생하므로 환율은 실적에 직결된다.
"""

import math


def _ma(values: list[float], window: int) -> float | None:
    """최근 window개 단순이동평균. 데이터 부족 시 None."""
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def _pct_change(old: float, new: float) -> float:
    """변동률(%)."""
    return (new - old) / old * 100


def _pearson(x: list[float], y: list[float]) -> float | None:
    """피어슨 상관계수. 길이가 다르거나 2 미만이면 None."""
    n = len(x)
    if n != len(y) or n < 2:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        return None
    return cov / (sx * sy)


def analyze_exchange_rate(
    rate_rows: list[dict],
    price_rows: list[dict] | None = None,
) -> dict:
    """USD/KRW 환율 분석 결과를 반환한다.

    Args:
        rate_rows: 환율 OHLC dicts (날짜 오름차순). {date, open, high, low, close}
        price_rows: 주가 OHLCV dicts (날짜 오름차순, 선택). 상관관계 분석에 사용.

    Returns:
        dict with: current_rate, change_1d/5d/20d_pct, ma5, ma20, trend, correlation_20d

    Raises:
        ValueError: rate_rows가 비어있을 때.
    """
    if not rate_rows:
        raise ValueError("환율 데이터가 비어있습니다.")

    closes = [r["close"] for r in rate_rows]
    n = len(closes)
    current = closes[-1]

    # 등락률
    def change_nd(days: int) -> float | None:
        if n <= days:
            return None
        return _pct_change(closes[-(days + 1)], current)

    # 이동평균
    ma5 = _ma(closes, 5)
    ma20 = _ma(closes, 20)

    # 추세 판정
    trend: str | None = None
    if ma5 is not None and ma20 is not None:
        if current > ma5 > ma20:
            trend = "원화약세"
        elif current < ma5 < ma20:
            trend = "원화강세"
        else:
            trend = "보합"

    # 주가-환율 상관관계 (최근 20일 종가 기준)
    correlation: float | None = None
    if price_rows and n >= 20:
        rate_by_date = {r["date"]: r["close"] for r in rate_rows}
        price_by_date = {r["date"]: r["close"] for r in price_rows}
        common_dates = sorted(set(rate_by_date) & set(price_by_date))
        if len(common_dates) >= 20:
            recent = common_dates[-20:]
            rx = [rate_by_date[d] for d in recent]
            px = [price_by_date[d] for d in recent]
            correlation = _pearson(rx, px)

    return {
        "current_date": rate_rows[-1]["date"],
        "current_rate": current,
        "change_1d_pct": change_nd(1),
        "change_5d_pct": change_nd(5),
        "change_20d_pct": change_nd(20),
        "ma5": ma5,
        "ma20": ma20,
        "trend": trend,
        "correlation_20d": correlation,
    }
