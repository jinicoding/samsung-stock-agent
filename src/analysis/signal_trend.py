"""시그널 추이 분석 — 최근 N일 종합 시그널 변화 추적.

signal_history 테이블의 데이터를 활용하여 시그널 점수·등급의
변화 추이를 분석한다. 텍스트 스파크라인으로 시각화하고
추세 방향(개선/악화/횡보)을 판단한다.
"""

from __future__ import annotations

from typing import Any

# 스파크라인 문자 (낮은→높은)
_SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _sparkline(values: list[float]) -> str:
    """숫자 리스트를 텍스트 스파크라인으로 변환."""
    if not values:
        return ""
    mn = min(values)
    mx = max(values)
    rng = mx - mn
    if rng == 0:
        mid = len(_SPARK_CHARS) // 2
        return _SPARK_CHARS[mid] * len(values)
    return "".join(
        _SPARK_CHARS[min(int((v - mn) / rng * (len(_SPARK_CHARS) - 1)), len(_SPARK_CHARS) - 1)]
        for v in values
    )


def _classify_direction(scores: list[float]) -> str:
    """점수 리스트의 전반적 추세를 판단한다.

    Returns:
        "개선" | "악화" | "횡보"
    """
    if len(scores) <= 1:
        return "횡보"
    first_half = scores[: len(scores) // 2] or scores[:1]
    second_half = scores[len(scores) // 2 :]
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    diff = avg_second - avg_first
    if diff > 5:
        return "개선"
    if diff < -5:
        return "악화"
    return "횡보"


def analyze_signal_trend(
    db_module: Any,
    days: int = 5,
) -> dict | None:
    """최근 N일 시그널 추이를 분석한다.

    Args:
        db_module: get_signal_history(days) 메서드를 가진 DB 모듈.
        days: 조회할 일수 (기본 5).

    Returns:
        분석 결과 dict 또는 데이터 없으면 None.
        {
            "days_available": int,
            "scores": list[float],
            "grades": list[str],
            "dates": list[str],
            "direction": "개선" | "악화" | "횡보",
            "consecutive_same_grade": int,
            "score_range": float,
            "score_change": float,  # 최근 - 최초
            "sparkline": str,
            "latest_score": float,
            "latest_grade": str,
        }
    """
    rows = db_module.get_signal_history(days)
    if not rows:
        return None

    scores = [r["score"] for r in rows]
    grades = [r["grade"] for r in rows]
    dates = [r["date"] for r in rows]

    # 연속 동일 등급 일수 (최근부터 역순)
    consecutive = 1
    for i in range(len(grades) - 2, -1, -1):
        if grades[i] == grades[-1]:
            consecutive += 1
        else:
            break

    return {
        "days_available": len(rows),
        "scores": scores,
        "grades": grades,
        "dates": dates,
        "direction": _classify_direction(scores),
        "consecutive_same_grade": consecutive,
        "score_range": max(scores) - min(scores),
        "score_change": scores[-1] - scores[0],
        "sparkline": _sparkline(scores),
        "latest_score": float(scores[-1]),
        "latest_grade": grades[-1],
    }
