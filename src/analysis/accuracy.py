"""시그널 정확도 추적 모듈 — 과거 시그널 vs 실제 주가 변동 대조."""

from __future__ import annotations

FORWARD_DAYS = (1, 3, 5)

AXES = (
    "technical_score", "supply_score", "exchange_score",
    "fundamentals_score", "news_score", "consensus_score",
    "semiconductor_score", "volatility_score", "candlestick_score",
    "global_macro_score",
)


def evaluate_signals(db, days: int = 365) -> dict:
    """시그널 이력과 주가 데이터를 대조하여 정확도 통계를 반환한다.

    Args:
        db: database 모듈 (get_signal_history, get_prices 함수 보유)
        days: 조회할 과거 일수

    Returns:
        {"details": [...], "summary": {...}}
    """
    signals = db.get_signal_history(days)
    prices = db.get_prices(days)

    if not signals:
        return _empty_result()

    # 날짜 → 인덱스 매핑
    date_to_idx = {p["date"]: i for i, p in enumerate(prices)}

    details = []
    for sig in signals:
        detail = _evaluate_one(sig, prices, date_to_idx)
        details.append(detail)

    summary = _build_summary(details)
    return {"details": details, "summary": summary}


def _evaluate_one(
    sig: dict,
    prices: list[dict],
    date_to_idx: dict[str, int],
) -> dict:
    """단일 시그널의 forward return과 hit 여부를 계산한다."""
    base_price = sig["price"]
    sig_date = sig["date"]
    sig_idx = date_to_idx.get(sig_date)

    detail: dict = {
        "date": sig_date,
        "score": sig["score"],
        "grade": sig["grade"],
    }

    for n in FORWARD_DAYS:
        ret_key = f"forward_return_{n}d"
        hit_key = f"hit_{n}d"

        future_price = _get_future_price(sig_idx, n, prices)
        if future_price is None or base_price == 0:
            detail[ret_key] = None
            detail[hit_key] = None
            continue

        fwd_return = (future_price - base_price) / base_price * 100
        detail[ret_key] = fwd_return

        # 중립(score == 0)은 방향 판정 불가
        if sig["score"] == 0:
            detail[hit_key] = None
        else:
            signal_bullish = sig["score"] > 0
            price_up = future_price > base_price
            detail[hit_key] = signal_bullish == price_up

    # 축별 forward return & hit 정보
    axis_detail: dict = {}
    for axis in AXES:
        axis_score = sig.get(axis)
        axis_info: dict = {}
        # 축 점수가 None 또는 0이면 방향 판정 불가 → 해당 축 전체 제외
        if axis_score is None or axis_score == 0:
            for n in FORWARD_DAYS:
                axis_info[f"return_{n}d"] = None
                axis_info[f"hit_{n}d"] = None
        else:
            for n in FORWARD_DAYS:
                future_price = _get_future_price(sig_idx, n, prices)
                if future_price is None or base_price == 0:
                    axis_info[f"return_{n}d"] = None
                    axis_info[f"hit_{n}d"] = None
                else:
                    fwd_return = (future_price - base_price) / base_price * 100
                    axis_info[f"return_{n}d"] = fwd_return
                    axis_info[f"hit_{n}d"] = (axis_score > 0) == (future_price > base_price)
        axis_detail[axis] = axis_info
    detail["per_axis"] = axis_detail

    return detail


def _get_future_price(
    sig_idx: int | None, n: int, prices: list[dict]
) -> float | None:
    """시그널 발생일로부터 n거래일 후 종가를 반환한다."""
    if sig_idx is None:
        return None
    future_idx = sig_idx + n
    if future_idx >= len(prices):
        return None
    return prices[future_idx]["close"]


def _build_summary(details: list[dict]) -> dict:
    """전체 적중률·평균 수익률 통계를 계산한다."""
    summary: dict = {"total_signals": len(details)}

    for n in FORWARD_DAYS:
        ret_key = f"forward_return_{n}d"
        hit_key = f"hit_{n}d"

        returns = [d[ret_key] for d in details if d[ret_key] is not None]
        hits = [d[hit_key] for d in details if d[hit_key] is not None]

        summary[f"avg_return_{n}d"] = (
            sum(returns) / len(returns) if returns else None
        )
        summary[f"hit_rate_{n}d"] = (
            sum(1 for h in hits if h) / len(hits) * 100 if hits else None
        )
        summary[f"evaluated_signals_{n}d"] = len(hits)

    summary["per_axis"] = _build_per_axis_summary(details)
    return summary


def _build_per_axis_summary(details: list[dict]) -> dict:
    """축별 적중률·평균 수익률 통계를 계산한다."""
    per_axis: dict = {}
    for axis in AXES:
        axis_stats: dict = {}
        for n in FORWARD_DAYS:
            returns = []
            hits = []
            for d in details:
                ad = d.get("per_axis", {}).get(axis, {})
                ret = ad.get(f"return_{n}d")
                hit = ad.get(f"hit_{n}d")
                if ret is not None:
                    returns.append(ret)
                if hit is not None:
                    hits.append(hit)
            axis_stats[f"avg_return_{n}d"] = (
                sum(returns) / len(returns) if returns else None
            )
            axis_stats[f"hit_rate_{n}d"] = (
                sum(1 for h in hits if h) / len(hits) * 100 if hits else None
            )
            axis_stats[f"evaluated_{n}d"] = len(hits)
        per_axis[axis] = axis_stats
    return per_axis


def _empty_result() -> dict:
    """시그널이 없을 때의 빈 결과."""
    summary: dict = {"total_signals": 0}
    for n in FORWARD_DAYS:
        summary[f"avg_return_{n}d"] = None
        summary[f"hit_rate_{n}d"] = None
        summary[f"evaluated_signals_{n}d"] = 0
    summary["per_axis"] = _build_per_axis_summary([])
    return {"details": [], "summary": summary}
