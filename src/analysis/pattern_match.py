"""유사 패턴 검색 모듈 — signal_history의 10축 점수로 과거 유사 날짜를 찾고 이후 주가 변동을 분석."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

SCORE_AXES = [
    "technical_score", "supply_score", "exchange_score",
    "fundamentals_score", "news_score", "consensus_score",
    "semiconductor_score", "volatility_score", "candlestick_score",
    "global_macro_score",
]

MIN_HISTORY = 20


def _normalize(value: float) -> float:
    return (value + 100.0) / 200.0


def _euclidean_distance(current: dict, historical: dict) -> tuple[float, int]:
    total = 0.0
    count = 0
    for ax in SCORE_AXES:
        cur_val = current.get(ax)
        hist_val = historical.get(ax)
        if cur_val is None or hist_val is None:
            continue
        diff = _normalize(cur_val) - _normalize(hist_val)
        total += diff * diff
        count += 1
    if count == 0:
        return float("inf"), 0
    return math.sqrt(total / count), count


def _get_forward_return(prices_by_date: dict, date_str: str, offset: int) -> float | None:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    base_price = prices_by_date.get(date_str)
    if base_price is None:
        return None
    for delta in range(offset, offset + 5):
        target = (dt + timedelta(days=delta)).strftime("%Y-%m-%d")
        if target in prices_by_date:
            return prices_by_date[target] / base_price - 1.0
    return None


def find_similar_patterns(
    current_scores: dict,
    db,
    *,
    top_n: int = 5,
    exclude_recent: int = 7,
) -> dict | None:
    signals = db.get_signal_history(365)
    if len(signals) < MIN_HISTORY:
        return None

    last_date = signals[-1]["date"]
    last_dt = datetime.strptime(last_date, "%Y-%m-%d")
    cutoff_dt = last_dt - timedelta(days=exclude_recent - 1)

    candidates = []
    for sig in signals:
        sig_dt = datetime.strptime(sig["date"], "%Y-%m-%d")
        if sig_dt >= cutoff_dt:
            continue
        dist, axis_count = _euclidean_distance(current_scores, sig)
        if axis_count == 0:
            continue
        candidates.append((dist, sig))

    candidates.sort(key=lambda x: x[0])
    top = candidates[:top_n]

    prices = db.get_prices(365)
    prices_by_date = {p["date"]: p["close"] for p in prices}

    matches = []
    for dist, sig in top:
        fr = {
            "1d": _get_forward_return(prices_by_date, sig["date"], 1),
            "3d": _get_forward_return(prices_by_date, sig["date"], 3),
            "5d": _get_forward_return(prices_by_date, sig["date"], 5),
        }
        similarity = 1.0 / (1.0 + dist * dist * 10)
        matches.append({
            "date": sig["date"],
            "distance": dist,
            "similarity": similarity,
            "scores": {ax: sig.get(ax) for ax in SCORE_AXES},
            "forward_returns": fr,
        })

    def _avg(vals):
        valid = [v for v in vals if v is not None]
        return sum(valid) / len(valid) if valid else None

    def _up_ratio(vals):
        valid = [v for v in vals if v is not None]
        if not valid:
            return None
        return sum(1 for v in valid if v > 0) / len(valid)

    r1 = [m["forward_returns"]["1d"] for m in matches]
    r3 = [m["forward_returns"]["3d"] for m in matches]
    r5 = [m["forward_returns"]["5d"] for m in matches]

    return {
        "matches": matches,
        "summary": {
            "avg_return_1d": _avg(r1),
            "avg_return_3d": _avg(r3),
            "avg_return_5d": _avg(r5),
            "up_ratio_1d": _up_ratio(r1),
            "up_ratio_3d": _up_ratio(r3),
            "up_ratio_5d": _up_ratio(r5),
            "match_count": len(matches),
        },
    }
