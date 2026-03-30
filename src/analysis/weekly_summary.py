"""주간 추이 요약 분석 — 최근 5거래일 데이터 종합 요약.

기존 시그널이 '오늘의 스냅샷'이라면, 주간 요약은
'이번 주 전체 흐름'을 조감도로 제공한다.
"""

from __future__ import annotations


def _classify_judgment(
    closes: list[float],
    change_pct: float,
) -> str:
    """주간 요약 판정을 반환한다.

    판정 기준:
    - 횡보: 주간 등락률 절대값 < 1%
    - 상승/하락 전환: 전반부와 후반부의 방향이 다름
    - 상승/하락 지속: 전반부와 후반부 방향이 같음

    Returns:
        "상승 전환" | "하락 전환" | "상승 지속" | "하락 지속" | "횡보"
    """
    if abs(change_pct) < 1.0:
        return "횡보"

    n = len(closes)
    mid = n // 2
    first_half_change = closes[mid] - closes[0]
    second_half_change = closes[-1] - closes[mid]

    if second_half_change > 0 and first_half_change < 0:
        return "상승 전환"
    if second_half_change < 0 and first_half_change > 0:
        return "하락 전환"
    if change_pct > 0:
        return "상승 지속"
    return "하락 지속"


def summarize_weekly(
    prices: list[dict],
    trading: list[dict],
    signals: list[dict],
) -> dict | None:
    """최근 거래일의 데이터를 종합하여 주간 추이를 요약한다.

    Args:
        prices: 날짜 오름차순 OHLCV 리스트 (최대 5거래일).
        trading: 날짜 오름차순 외국인/기관 매매 리스트.
        signals: 날짜 오름차순 시그널 이력 리스트.

    Returns:
        주간 요약 dict. 데이터 부족 시 None.
    """
    if len(prices) < 2:
        return None

    week_open = prices[0]["open"]
    week_close = prices[-1]["close"]
    week_high = max(p["high"] for p in prices)
    week_low = min(p["low"] for p in prices)
    change_pct = (week_close - week_open) / week_open * 100

    total_volume = sum(p["volume"] for p in prices)
    avg_daily_volume = total_volume / len(prices)

    closes = [p["close"] for p in prices]

    institution_net = sum(t["institution"] for t in trading) if trading else 0
    foreign_net = sum(t["foreign_total"] for t in trading) if trading else 0

    sig_start_score = signals[0]["score"] if signals else None
    sig_end_score = signals[-1]["score"] if signals else None
    sig_score_change = (sig_end_score - sig_start_score) if signals else None
    sig_start_grade = signals[0]["grade"] if signals else None
    sig_end_grade = signals[-1]["grade"] if signals else None

    judgment = _classify_judgment(closes, change_pct)

    return {
        "days": len(prices),
        "start_date": prices[0]["date"],
        "end_date": prices[-1]["date"],
        "week_open": week_open,
        "week_close": week_close,
        "week_high": week_high,
        "week_low": week_low,
        "change_pct": change_pct,
        "total_volume": total_volume,
        "avg_daily_volume": avg_daily_volume,
        "institution_net_total": institution_net,
        "foreign_net_total": foreign_net,
        "signal_start_score": sig_start_score,
        "signal_end_score": sig_end_score,
        "signal_score_change": sig_score_change,
        "signal_start_grade": sig_start_grade,
        "signal_end_grade": sig_end_grade,
        "judgment": judgment,
    }
