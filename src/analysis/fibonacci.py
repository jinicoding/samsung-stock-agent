"""피보나치 되돌림/확장 분석 모듈.

최근 N일 가격 데이터에서 swing high/low를 탐지하여
피보나치 되돌림 및 확장 수준을 계산한다.
"""

RETRACEMENT_RATIOS = {
    "0.0": 0.0,
    "0.236": 0.236,
    "0.382": 0.382,
    "0.5": 0.5,
    "0.618": 0.618,
    "0.786": 0.786,
    "1.0": 1.0,
}

EXTENSION_RATIOS = {
    "1.0": 1.0,
    "1.272": 1.272,
    "1.618": 1.618,
}


def find_swing_points(rows: list[dict]) -> tuple[dict | None, dict | None]:
    """최근 N일 데이터에서 swing high와 swing low를 찾는다.

    Returns:
        (swing_high, swing_low) — 데이터 부족 시 (None, None).
        각각 {"price": float, "date": str, "index": int}.
    """
    if len(rows) < 5:
        return None, None

    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]

    max_idx = max(range(len(highs)), key=lambda i: highs[i])
    min_idx = min(range(len(lows)), key=lambda i: lows[i])

    swing_high = {"price": highs[max_idx], "date": rows[max_idx]["date"], "index": max_idx}
    swing_low = {"price": lows[min_idx], "date": rows[min_idx]["date"], "index": min_idx}

    return swing_high, swing_low


def compute_retracement_levels(low: float, high: float, trend: str = "up") -> dict[str, float]:
    """피보나치 되돌림 수준을 계산한다.

    Args:
        low: swing low 가격.
        high: swing high 가격.
        trend: "up"이면 고점에서 되돌림, "down"이면 저점에서 되돌림.

    Returns:
        {"0.0": price, "0.236": price, ...} — high==low이면 빈 dict.
    """
    if high == low:
        return {}

    diff = high - low
    levels = {}

    if trend == "up":
        for label, ratio in RETRACEMENT_RATIOS.items():
            levels[label] = high - diff * ratio
    else:
        for label, ratio in RETRACEMENT_RATIOS.items():
            levels[label] = low + diff * ratio

    return levels


def compute_extension_levels(low: float, high: float, trend: str = "up") -> dict[str, float]:
    """피보나치 확장 수준을 계산한다.

    Returns:
        {"1.0": price, "1.272": price, "1.618": price} — high==low이면 빈 dict.
    """
    if high == low:
        return {}

    diff = high - low
    levels = {}

    if trend == "up":
        for label, ratio in EXTENSION_RATIOS.items():
            levels[label] = high + diff * ratio
    else:
        for label, ratio in EXTENSION_RATIOS.items():
            levels[label] = low - diff * ratio

    return levels


def find_current_position(current_price: float, levels: dict[str, float]) -> dict:
    """현재가가 피보나치 수준 중 어디에 위치하는지 판별한다.

    Returns:
        {"below": 바로 아래 수준 라벨, "above": 바로 위 수준 라벨,
         "nearest_support": 가장 가까운 지지, "nearest_resistance": 가장 가까운 저항}
    """
    result = {"below": None, "above": None, "nearest_support": None, "nearest_resistance": None}
    if not levels:
        return result

    sorted_levels = sorted(levels.items(), key=lambda x: x[1])

    supports = [(label, price) for label, price in sorted_levels if price <= current_price]
    resistances = [(label, price) for label, price in sorted_levels if price > current_price]

    if supports:
        result["below"] = supports[-1][0]
        result["nearest_support"] = supports[-1][1]

    if resistances:
        result["above"] = resistances[0][0]
        result["nearest_resistance"] = resistances[0][1]

    return result


def _determine_trend(rows: list[dict]) -> str:
    """최근 가격 흐름으로 추세 판단."""
    if len(rows) < 2:
        return "up"
    mid = len(rows) // 2
    first_half_avg = sum(r["close"] for r in rows[:mid]) / mid
    second_half_avg = sum(r["close"] for r in rows[mid:]) / (len(rows) - mid)
    return "up" if second_half_avg >= first_half_avg else "down"


def analyze_fibonacci(rows: list[dict], period: int = 60) -> dict:
    """피보나치 되돌림/확장 종합 분석.

    Args:
        rows: OHLCV dicts (날짜 오름차순).
        period: 분석 기간 (기본 60일).

    Returns:
        {"retracement": {...}, "extension": {...}, "position": {...},
         "swing_high": {...}, "swing_low": {...}, "trend": str}
    """
    empty = {
        "retracement": {},
        "extension": {},
        "position": {"below": None, "above": None, "nearest_support": None, "nearest_resistance": None},
        "swing_high": None,
        "swing_low": None,
        "trend": None,
    }

    recent = rows[-period:] if len(rows) > period else rows
    swing_high, swing_low = find_swing_points(recent)

    if swing_high is None or swing_low is None:
        return empty

    if swing_high["price"] == swing_low["price"]:
        return empty

    trend = _determine_trend(recent)
    retracement = compute_retracement_levels(swing_low["price"], swing_high["price"], trend)
    extension = compute_extension_levels(swing_low["price"], swing_high["price"], trend)

    current_price = recent[-1]["close"]
    position = find_current_position(current_price, retracement)

    return {
        "retracement": retracement,
        "extension": extension,
        "position": position,
        "swing_high": swing_high,
        "swing_low": swing_low,
        "trend": trend,
    }
