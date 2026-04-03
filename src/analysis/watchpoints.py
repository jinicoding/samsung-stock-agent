"""핵심 관찰 포인트(Key Watchpoints) 모듈.

투자자가 "오늘 무엇을 주목해야 하는가"를 즉시 파악할 수 있도록
지지/저항 시나리오, ATR 기반 변동 범위, 핵심 리스크/기회 요인을 제공한다.
"""

from __future__ import annotations


def compute_scenario_levels(
    sr: dict,
    current_price: float,
) -> dict:
    """지지/저항선 기반 상승·하락 시나리오를 계산한다.

    nearest_support 이탈 시 → next_support 목표
    nearest_resistance 돌파 시 → next_resistance 목표

    Returns:
        {nearest_support, nearest_resistance, next_support, next_resistance}
    """
    nearest_sup = sr.get("nearest_support")
    nearest_res = sr.get("nearest_resistance")

    # 모든 지지/저항 레벨 수집
    all_supports: list[float] = []
    all_resistances: list[float] = []

    # 피봇 포인트
    pivot = sr.get("pivot", {})
    for key in ("s1", "s2"):
        val = pivot.get(key)
        if val is not None:
            all_supports.append(val)
    for key in ("r1", "r2"):
        val = pivot.get(key)
        if val is not None:
            all_resistances.append(val)
    pp = pivot.get("pp")
    if pp is not None:
        if pp <= current_price:
            all_supports.append(pp)
        else:
            all_resistances.append(pp)

    # 스윙 레벨
    for level in sr.get("swing_levels", []):
        if level["type"] == "support":
            all_supports.append(level["price"])
        else:
            all_resistances.append(level["price"])

    # MA 레벨
    ma_levels = sr.get("ma_levels", {})
    for key in ("ma20", "ma60"):
        val = ma_levels.get(key)
        if val is not None:
            if val <= current_price:
                all_supports.append(val)
            else:
                all_resistances.append(val)

    # nearest_support보다 낮은 지지선 중 가장 높은 것 = next_support
    next_sup = None
    if nearest_sup is not None:
        lower_supports = [s for s in all_supports if s < nearest_sup]
        if lower_supports:
            next_sup = max(lower_supports)

    # nearest_resistance보다 높은 저항선 중 가장 낮은 것 = next_resistance
    next_res = None
    if nearest_res is not None:
        higher_resistances = [r for r in all_resistances if r > nearest_res]
        if higher_resistances:
            next_res = min(higher_resistances)

    return {
        "nearest_support": nearest_sup,
        "nearest_resistance": nearest_res,
        "next_support": next_sup,
        "next_resistance": next_res,
    }


def compute_daily_range(
    current_price: float,
    volatility: dict | None = None,
) -> dict:
    """ATR 기반 예상 일일 변동 범위를 계산한다.

    Returns:
        {expected_high, expected_low, atr, atr_pct}
    """
    if volatility is None:
        return {"expected_high": None, "expected_low": None, "atr": None, "atr_pct": None}

    atr = volatility.get("atr")
    atr_pct = volatility.get("atr_pct")

    if atr is None:
        return {"expected_high": None, "expected_low": None, "atr": None, "atr_pct": atr_pct}

    return {
        "expected_high": current_price + atr,
        "expected_low": current_price - atr,
        "atr": atr,
        "atr_pct": atr_pct,
    }


def extract_risk_opportunity_factors(
    volatility: dict | None = None,
    trend_reversal: dict | None = None,
    supply_demand: dict | None = None,
    news_sentiment: dict | None = None,
) -> list[dict]:
    """핵심 리스크/기회 요인을 자동 추출한다 (최대 3개).

    Returns:
        list of {type: "risk"|"opportunity", text: str}
    """
    factors: list[dict] = []

    # 변동성 체제
    if volatility is not None:
        regime = volatility.get("volatility_regime")
        squeeze = volatility.get("bandwidth_squeeze")
        if regime == "고변동성":
            factors.append({"type": "risk", "text": "고변동성 체제 — 급등락 가능성 확대"})
        if squeeze:
            factors.append({"type": "opportunity", "text": "볼린저밴드 수축 — 변동성 확대 임박 가능"})

    # 추세 전환
    if trend_reversal is not None:
        convergence = trend_reversal.get("convergence", "none")
        if convergence in ("strong", "moderate"):
            direction = trend_reversal.get("direction", "neutral")
            if direction == "bullish":
                factors.append({"type": "opportunity", "text": "강세 전환 신호 감지"})
            elif direction == "bearish":
                factors.append({"type": "risk", "text": "약세 전환 신호 감지"})

    # 수급 이상
    if supply_demand is not None:
        judgment = supply_demand.get("overall_judgment")
        if judgment == "buy_dominant":
            consec = supply_demand.get("foreign_consecutive_net_buy", 0)
            text = "외국인·기관 매수 우세"
            if consec >= 3:
                text += f" (외인 {consec}일 연속 순매수)"
            factors.append({"type": "opportunity", "text": text})
        elif judgment == "sell_dominant":
            consec = supply_demand.get("foreign_consecutive_net_sell", 0)
            text = "외국인·기관 매도 우세"
            if consec >= 3:
                text += f" (외인 {consec}일 연속 순매도)"
            factors.append({"type": "risk", "text": text})

    # 뉴스 감정
    if news_sentiment is not None:
        overall = news_sentiment.get("overall")
        if overall == "bearish":
            factors.append({"type": "risk", "text": "뉴스 감정 부정적"})
        elif overall == "bullish":
            factors.append({"type": "opportunity", "text": "뉴스 감정 긍정적"})

    # 최대 3개로 제한
    return factors[:3]


def build_watchpoints(
    current_price: float,
    support_resistance: dict | None = None,
    volatility: dict | None = None,
    trend_reversal: dict | None = None,
    supply_demand: dict | None = None,
    news_sentiment: dict | None = None,
) -> dict:
    """핵심 관찰 포인트를 종합한다.

    Returns:
        {scenarios: dict, daily_range: dict, factors: list[dict]}
    """
    # 시나리오
    if support_resistance is not None:
        scenarios = compute_scenario_levels(support_resistance, current_price)
    else:
        scenarios = {
            "nearest_support": None,
            "nearest_resistance": None,
            "next_support": None,
            "next_resistance": None,
        }

    # 일일 변동 범위
    daily_range = compute_daily_range(current_price, volatility)

    # 리스크/기회 요인
    factors = extract_risk_opportunity_factors(
        volatility=volatility,
        trend_reversal=trend_reversal,
        supply_demand=supply_demand,
        news_sentiment=news_sentiment,
    )

    return {
        "scenarios": scenarios,
        "daily_range": daily_range,
        "factors": factors,
    }
