"""Price scenario analysis — builds bull/base/bear scenarios from signals."""


def _fallback_atr(current_price: float) -> float:
    return current_price * 0.015


def _upside_target(
    current_price: float,
    nearest_resistance: float | None,
    atr: float | None,
) -> float:
    if nearest_resistance is not None and nearest_resistance > current_price:
        return nearest_resistance
    effective_atr = atr if atr is not None else _fallback_atr(current_price)
    return current_price + effective_atr * 2.5


def _downside_target(
    current_price: float,
    nearest_support: float | None,
    atr: float | None,
) -> float:
    if nearest_support is not None and nearest_support < current_price:
        return nearest_support
    effective_atr = atr if atr is not None else _fallback_atr(current_price)
    return current_price - effective_atr * 2.5


def _base_range(current_price: float, atr: float | None) -> list[float]:
    effective_atr = atr if atr is not None else _fallback_atr(current_price)
    return [current_price - effective_atr, current_price + effective_atr]


def _conviction_score(
    signal_score: float,
    timeframe_alignment: dict,
    convergence: dict,
) -> float:
    """0-100 raw conviction from signal strength + alignment + convergence."""
    signal_component = min(abs(signal_score), 100) * 0.4
    alignment = timeframe_alignment.get("alignment", "neutral")
    alignment_map = {
        "aligned_bullish": 40,
        "aligned_bearish": 40,
        "divergent_bullish": 20,
        "divergent_bearish": 20,
        "neutral": 10,
    }
    alignment_component = alignment_map.get(alignment, 10) * 0.3
    convergence_component = convergence.get("conviction", 50) * 0.3
    return signal_component + alignment_component + convergence_component


def _conviction_label(raw: float) -> str:
    if raw >= 45:
        return "높음"
    if raw >= 25:
        return "보통"
    return "낮음"


def _dominant_scenario(signal_score: float) -> str:
    if signal_score >= 20:
        return "상승"
    if signal_score <= -20:
        return "하락"
    return "기본"


def _format_price(price: float) -> str:
    return f"{price:,.0f}"


def build_price_scenarios(
    current_price: float,
    support_resistance: dict,
    volatility: dict,
    composite_signal: dict,
    timeframe_alignment: dict,
    convergence: dict,
) -> dict:
    signal_score = composite_signal["score"]
    atr = volatility.get("atr")
    nearest_resistance = support_resistance.get("nearest_resistance")
    nearest_support = support_resistance.get("nearest_support")

    up_target = _upside_target(current_price, nearest_resistance, atr)
    down_target = _downside_target(current_price, nearest_support, atr)
    base = _base_range(current_price, atr)

    raw_conv = _conviction_score(signal_score, timeframe_alignment, convergence)

    bullish_conv = _conviction_label(raw_conv if signal_score > 0 else raw_conv * 0.5)
    bearish_conv = _conviction_label(raw_conv if signal_score < 0 else raw_conv * 0.5)
    base_conv = _conviction_label(raw_conv if -20 <= signal_score <= 20 else raw_conv * 0.5)

    up_trigger = (
        f"저항선 {_format_price(nearest_resistance)} 돌파 시"
        if nearest_resistance and nearest_resistance > current_price
        else "매수세 지속 확대 시"
    )
    down_trigger = (
        f"지지선 {_format_price(nearest_support)} 이탈 시"
        if nearest_support and nearest_support < current_price
        else "매도세 지속 확대 시"
    )

    upside_pct = (up_target - current_price) / current_price * 100
    downside_pct = (current_price - down_target) / current_price * 100

    dominant = _dominant_scenario(signal_score)

    key_level = current_price
    if dominant == "상승" and nearest_resistance and nearest_resistance > current_price:
        key_level = nearest_resistance
    elif dominant == "하락" and nearest_support and nearest_support < current_price:
        key_level = nearest_support
    elif nearest_support and nearest_support < current_price:
        key_level = nearest_support

    scenarios = [
        {
            "label": "상승",
            "target": up_target,
            "trigger": up_trigger,
            "conviction": bullish_conv,
        },
        {
            "label": "기본",
            "range": base,
            "trigger": "현 수급 흐름 유지",
            "conviction": base_conv,
        },
        {
            "label": "하락",
            "target": down_target,
            "trigger": down_trigger,
            "conviction": bearish_conv,
        },
    ]

    return {
        "scenarios": scenarios,
        "dominant_scenario": dominant,
        "key_level": key_level,
        "risk_reward_comment": (
            f"상승 여력 +{upside_pct:.1f}% vs 하방 리스크 -{downside_pct:.1f}%"
        ),
    }
