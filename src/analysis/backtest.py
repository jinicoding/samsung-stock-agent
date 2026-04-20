"""시그널 성과 백테스팅 모듈 — 종합 시그널의 예측 성과를 정량적으로 검증한다."""

from __future__ import annotations

from src.analysis.accuracy import AXES, FORWARD_DAYS, evaluate_signals

SCORE_BINS = [
    (-100, -60, "강력매도 (-100~-60)"),
    (-60, -20, "매도우세 (-60~-20)"),
    (-20, 20, "중립 (-20~+20)"),
    (20, 60, "매수우세 (+20~+60)"),
    (60, 101, "강력매수 (+60~+100)"),
]


def run_backtest(db, days: int = 365) -> dict:
    """시그널 이력 기반 종합 백테스트를 수행한다.

    Returns:
        {
            "grade_performance": {등급별 수익률/적중률},
            "score_range_performance": [점수 구간별 성과],
            "streak_analysis": {연속 성과, equity curve},
            "axis_contribution": {축별 상관·기여도},
        }
    """
    eval_result = evaluate_signals(db, days)
    details = eval_result["details"]

    return {
        "grade_performance": _grade_performance(details),
        "score_range_performance": _score_range_performance(details),
        "streak_analysis": _streak_analysis(details),
        "axis_contribution": _axis_contribution(details),
    }


def _grade_performance(details: list[dict]) -> dict:
    """등급별 평균 수익률과 적중률을 계산한다."""
    buckets: dict[str, list[dict]] = {}
    for d in details:
        grade = d["grade"]
        buckets.setdefault(grade, []).append(d)

    result = {}
    for grade, items in buckets.items():
        stats: dict = {"count": len(items)}
        for n in FORWARD_DAYS:
            returns = [i[f"forward_return_{n}d"] for i in items if i[f"forward_return_{n}d"] is not None]
            hits = [i[f"hit_{n}d"] for i in items if i[f"hit_{n}d"] is not None]
            stats[f"avg_return_{n}d"] = sum(returns) / len(returns) if returns else None
            stats[f"hit_rate_{n}d"] = sum(1 for h in hits if h) / len(hits) * 100 if hits else None
        result[grade] = stats
    return result


def _score_range_performance(details: list[dict]) -> list[dict]:
    """점수 구간별 성과 통계를 계산한다."""
    bins: dict[str, list[dict]] = {label: [] for _, _, label in SCORE_BINS}
    for d in details:
        for lo, hi, label in SCORE_BINS:
            if lo <= d["score"] < hi:
                bins[label].append(d)
                break

    result = []
    for _, _, label in SCORE_BINS:
        items = bins[label]
        entry: dict = {"range_label": label, "count": len(items)}
        for n in FORWARD_DAYS:
            returns = [i[f"forward_return_{n}d"] for i in items if i[f"forward_return_{n}d"] is not None]
            hits = [i[f"hit_{n}d"] for i in items if i[f"hit_{n}d"] is not None]
            entry[f"avg_return_{n}d"] = sum(returns) / len(returns) if returns else None
            entry[f"hit_rate_{n}d"] = sum(1 for h in hits if h) / len(hits) * 100 if hits else None
        result.append(entry)
    return result


def _streak_analysis(details: list[dict]) -> dict:
    """연속 성과(연승/연패)와 누적 수익 곡선을 계산한다."""
    hits_seq = []
    equity_curve = []
    cumulative = 0.0

    for d in details:
        ret_1d = d.get("forward_return_1d")
        hit_1d = d.get("hit_1d")
        if ret_1d is None:
            continue
        cumulative += ret_1d
        equity_curve.append({"date": d["date"], "cumulative_return": round(cumulative, 4)})
        if hit_1d is not None:
            hits_seq.append(hit_1d)

    max_win = _max_streak(hits_seq, True)
    max_lose = _max_streak(hits_seq, False)

    return {
        "max_win_streak": max_win,
        "max_lose_streak": max_lose,
        "equity_curve": equity_curve,
    }


def _max_streak(seq: list[bool], target: bool) -> int:
    """target 값의 최대 연속 횟수를 반환한다."""
    best = 0
    current = 0
    for v in seq:
        if v == target:
            current += 1
            if current > best:
                best = current
        else:
            current = 0
    return best


def _axis_contribution(details: list[dict]) -> dict:
    """축별 시그널 방향과 실제 수익률의 상관계수를 계산한다."""
    if not details:
        return {}

    result = {}
    correlations = []

    for axis in AXES:
        scores = []
        returns = []
        for d in details:
            sig_data = _find_signal_in_detail(d, axis)
            ret_1d = d.get("forward_return_1d")
            if sig_data is not None and ret_1d is not None:
                scores.append(sig_data)
                returns.append(ret_1d)

        corr = _pearson(scores, returns) if len(scores) >= 3 else None
        result[axis] = {"correlation_1d": corr, "contribution_rank": 0}
        if corr is not None:
            correlations.append((axis, abs(corr)))

    correlations.sort(key=lambda x: x[1], reverse=True)
    for rank, (axis, _) in enumerate(correlations, 1):
        result[axis]["contribution_rank"] = rank

    return result


def _find_signal_in_detail(detail: dict, axis: str) -> float | None:
    """detail dict에서 해당 축의 원본 점수를 추출한다."""
    per_axis = detail.get("per_axis", {}).get(axis, {})
    if per_axis.get("hit_1d") is None:
        return None
    # accuracy detail에는 축 원본 점수가 없으므로, hit 방향에서 역추정하지 않고
    # signal_history의 원본 score를 사용해야 한다.
    # evaluate_signals의 detail에는 per_axis에 return만 있고 원본 점수가 없다.
    # 대신 hit_1d가 있다는 것은 축 점수가 0이 아니었다는 뜻.
    # 상관계수 계산을 위해 return_1d의 부호를 축 방향으로 사용한다.
    # hit_1d == True면 축과 가격이 같은 방향 → 축 점수와 return_1d가 같은 부호.
    hit = per_axis.get("hit_1d")
    ret = per_axis.get("return_1d")
    if hit is None or ret is None:
        return None
    # 축이 양수였고 가격도 올랐으면 hit=True, 축이 음수였고 가격도 내렸으면 hit=True
    # 축 방향을 복원: hit==True면 return과 같은 부호, hit==False면 반대 부호
    if hit:
        return abs(ret)  # 축과 수익률이 같은 방향
    else:
        return -abs(ret)  # 축과 수익률이 반대 방향


def _pearson(x: list[float], y: list[float]) -> float | None:
    """피어슨 상관계수를 계산한다. 분산이 0이면 None."""
    n = len(x)
    if n < 2:
        return None
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)
    denom = (var_x * var_y) ** 0.5
    if denom == 0:
        return None
    return cov / denom
