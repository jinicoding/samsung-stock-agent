"""시그널 일일 변화 추적 (Daily Delta Analysis).

signal_history에서 최근 2일치를 조회하여 전일 대비 변화량,
방향 전환, 유의미한 변동을 감지한다.
"""

from src.data.database import get_signal_history

_AXES = [
    "technical_score", "supply_score", "exchange_score",
    "fundamentals_score", "news_score", "consensus_score",
    "semiconductor_score", "volatility_score", "candlestick_score",
    "global_macro_score",
]

_SIGNIFICANT_THRESHOLD = 15


def _is_sign_flip(prev: float, curr: float) -> bool:
    return (prev < 0 and curr > 0) or (prev > 0 and curr < 0)


def compute_daily_delta() -> dict | None:
    """전일 대비 시그널 변화를 분석한다.

    Returns:
        {
            "axes_delta": {축: {"prev", "curr", "change"}},
            "alerts": [{"type", "axis", "detail"}],
            "overall": {"prev_score", "curr_score", "change",
                        "prev_grade", "curr_grade"},
        }
        데이터 부족 시 None.
    """
    history = get_signal_history(2)
    if len(history) < 2:
        return None

    prev, curr = history[-2], history[-1]
    axes_delta: dict[str, dict] = {}
    alerts: list[dict] = []

    for ax in _AXES:
        pv = prev.get(ax)
        cv = curr.get(ax)
        if pv is None or cv is None:
            continue
        change = cv - pv
        axes_delta[ax] = {"prev": pv, "curr": cv, "change": change}

        if _is_sign_flip(pv, cv):
            direction = "bearish→bullish" if cv > 0 else "bullish→bearish"
            alerts.append({
                "type": "signal_flip", "axis": ax,
                "detail": f"{ax} {direction} ({pv:+.1f} → {cv:+.1f})",
            })

        if abs(change) >= _SIGNIFICANT_THRESHOLD:
            alerts.append({
                "type": "significant_move", "axis": ax,
                "detail": f"{ax} {change:+.1f}점 변동",
            })

    prev_score = prev["score"]
    curr_score = curr["score"]
    overall_change = curr_score - prev_score

    if _is_sign_flip(prev_score, curr_score):
        direction = "bearish→bullish" if curr_score > 0 else "bullish→bearish"
        alerts.append({
            "type": "signal_flip", "axis": "overall",
            "detail": f"종합 {direction} ({prev_score:+.1f} → {curr_score:+.1f})",
        })

    if abs(overall_change) >= _SIGNIFICANT_THRESHOLD:
        alerts.append({
            "type": "significant_move", "axis": "overall",
            "detail": f"종합 점수 {overall_change:+.1f}점 변동",
        })

    prev_grade = prev["grade"]
    curr_grade = curr["grade"]
    if prev_grade != curr_grade:
        alerts.append({
            "type": "grade_change", "axis": "overall",
            "detail": f"{prev_grade} → {curr_grade}",
        })

    return {
        "axes_delta": axes_delta,
        "alerts": alerts,
        "overall": {
            "prev_score": prev_score,
            "curr_score": curr_score,
            "change": overall_change,
            "prev_grade": prev_grade,
            "curr_grade": curr_grade,
        },
    }
