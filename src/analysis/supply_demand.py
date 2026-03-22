"""수급 분석 모듈 — 외국인/기관 매매 동향 해석.

DB의 foreign_trading, foreign_ownership 데이터를 분석하여
수급 흐름과 종합 판정을 제공한다.
"""


def _consecutive_count(values: list[int], positive: bool) -> int:
    """마지막 날짜부터 역순으로 연속 양수(positive=True) 또는 음수(False) 카운트."""
    count = 0
    for v in reversed(values):
        if positive and v > 0:
            count += 1
        elif not positive and v < 0:
            count += 1
        else:
            break
    return count


def _cumulative(values: list[int], n: int) -> int | None:
    """최근 N일 누적 합계. 데이터 부족 시 None."""
    if len(values) < n:
        return None
    return sum(values[-n:])


def _ownership_trend(ownership_rows: list[dict]) -> str | None:
    """외국인 보유비율 변화 추이 판정.

    최근 데이터의 첫날 대비 마지막날 변화를 기준으로:
    - +0.1%p 이상 증가: increasing
    - -0.1%p 이상 감소: decreasing
    - 그 외: sideways
    """
    if len(ownership_rows) < 2:
        return None
    first = ownership_rows[0]["ownership_pct"]
    last = ownership_rows[-1]["ownership_pct"]
    diff = last - first
    if diff >= 0.1:
        return "increasing"
    elif diff <= -0.1:
        return "decreasing"
    return "sideways"


def analyze_supply_demand(
    trading_rows: list[dict],
    ownership_rows: list[dict],
) -> dict:
    """수급 분석 결과를 반환한다.

    Args:
        trading_rows: foreign_trading DB rows (날짜 오름차순).
            각 dict: {date, institution, foreign_total, individual, other_corp}
        ownership_rows: foreign_ownership DB rows (날짜 오름차순).
            각 dict: {date, ownership_pct, foreign_shares, ...}

    Returns:
        분석 결과 dict.
    """
    foreign_vals = [r["foreign_total"] for r in trading_rows]
    institution_vals = [r["institution"] for r in trading_rows]

    # 연속 순매수/순매도
    foreign_consec_buy = _consecutive_count(foreign_vals, positive=True)
    foreign_consec_sell = _consecutive_count(foreign_vals, positive=False)
    inst_consec_buy = _consecutive_count(institution_vals, positive=True)
    inst_consec_sell = _consecutive_count(institution_vals, positive=False)

    # 누적 순매매
    foreign_cum_5d = _cumulative(foreign_vals, 5)
    foreign_cum_20d = _cumulative(foreign_vals, 20)
    inst_cum_5d = _cumulative(institution_vals, 5)
    inst_cum_20d = _cumulative(institution_vals, 20)

    # 보유비율 추이
    trend = _ownership_trend(ownership_rows)
    ownership_change: float | None = None
    if len(ownership_rows) >= 2:
        ownership_change = ownership_rows[-1]["ownership_pct"] - ownership_rows[0]["ownership_pct"]

    # 종합 판정
    judgment = _judge(
        foreign_cum_5d, inst_cum_5d,
        foreign_consec_buy, foreign_consec_sell,
        inst_consec_buy, inst_consec_sell,
        trend,
    )

    return {
        # 연속 매수/매도
        "foreign_consecutive_net_buy": foreign_consec_buy,
        "foreign_consecutive_net_sell": foreign_consec_sell,
        "institution_consecutive_net_buy": inst_consec_buy,
        "institution_consecutive_net_sell": inst_consec_sell,
        # 누적 순매매
        "foreign_cumulative_5d": foreign_cum_5d,
        "foreign_cumulative_20d": foreign_cum_20d,
        "institution_cumulative_5d": inst_cum_5d,
        "institution_cumulative_20d": inst_cum_20d,
        # 보유비율
        "ownership_trend": trend,
        "ownership_change_pct": ownership_change,
        # 종합 판정
        "overall_judgment": judgment,
    }


def _judge(
    foreign_cum_5d: int | None,
    inst_cum_5d: int | None,
    foreign_consec_buy: int,
    foreign_consec_sell: int,
    inst_consec_buy: int,
    inst_consec_sell: int,
    ownership_trend: str | None,
) -> str:
    """수급 종합 판정: buy_dominant / sell_dominant / neutral.

    판정 기준 (점수제):
    - 외국인 5일 누적 양수 +1, 음수 -1
    - 기관 5일 누적 양수 +1, 음수 -1
    - 외국인 연속 3일 이상 매수 +1, 매도 -1
    - 기관 연속 3일 이상 매수 +1, 매도 -1
    - 보유비율 increasing +1, decreasing -1

    점수 합산: ≥2 매수 우위, ≤-2 매도 우위, 그 외 중립.
    """
    score = 0

    if foreign_cum_5d is not None:
        if foreign_cum_5d > 0:
            score += 1
        elif foreign_cum_5d < 0:
            score -= 1

    if inst_cum_5d is not None:
        if inst_cum_5d > 0:
            score += 1
        elif inst_cum_5d < 0:
            score -= 1

    if foreign_consec_buy >= 3:
        score += 1
    elif foreign_consec_sell >= 3:
        score -= 1

    if inst_consec_buy >= 3:
        score += 1
    elif inst_consec_sell >= 3:
        score -= 1

    if ownership_trend == "increasing":
        score += 1
    elif ownership_trend == "decreasing":
        score -= 1

    if score >= 2:
        return "buy_dominant"
    elif score <= -2:
        return "sell_dominant"
    return "neutral"
