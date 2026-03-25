"""지지/저항선 분석 모듈.

세 가지 방법을 결합하여 핵심 지지선·저항선을 도출한다:
1. 클래식 피봇 포인트 (전일 HLC 기반)
2. 스윙 고점·저점 (local extrema)
3. 주요 이동평균선 (MA20, MA60) — 동적 지지/저항
"""


def compute_pivot_points(rows: list[dict]) -> dict:
    """전일 고가/저가/종가 기반 클래식 피봇 포인트를 계산한다.

    Returns:
        {pp, s1, s2, r1, r2} — 데이터 부족 시 모든 값 None.
    """
    none_result = {"pp": None, "s1": None, "s2": None, "r1": None, "r2": None}
    if len(rows) < 2:
        return none_result

    prev = rows[-2]
    h, l, c = prev["high"], prev["low"], prev["close"]
    pp = (h + l + c) / 3
    return {
        "pp": pp,
        "s1": 2 * pp - h,
        "s2": pp - (h - l),
        "r1": 2 * pp - l,
        "r2": pp + (h - l),
    }


def find_swing_levels(rows: list[dict], window: int = 3) -> list[dict]:
    """최근 데이터에서 스윙 고점·저점을 찾아 지지/저항 수준을 반환한다.

    Args:
        rows: OHLCV dicts (날짜 오름차순).
        window: 양쪽으로 비교할 봉 수. 기본 3.

    Returns:
        list of {type: "support"|"resistance", price: float, date: str}
    """
    n = len(rows)
    if n < window * 2 + 1:
        return []

    levels = []
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]

    for i in range(window, n - window):
        # 스윙 고점: i의 high가 양쪽 window개보다 모두 높음
        is_swing_high = all(
            highs[i] > highs[j] for j in range(i - window, i + window + 1) if j != i
        )
        if is_swing_high:
            levels.append({
                "type": "resistance",
                "price": highs[i],
                "date": rows[i]["date"],
            })

        # 스윙 저점: i의 low가 양쪽 window개보다 모두 낮음
        is_swing_low = all(
            lows[i] < lows[j] for j in range(i - window, i + window + 1) if j != i
        )
        if is_swing_low:
            levels.append({
                "type": "support",
                "price": lows[i],
                "date": rows[i]["date"],
            })

    return levels


def compute_ma_levels(rows: list[dict]) -> dict:
    """MA20, MA60을 동적 지지/저항 수준으로 반환한다.

    Returns:
        {ma20: float|None, ma60: float|None}
    """
    closes = [r["close"] for r in rows]
    n = len(closes)

    ma20 = sum(closes[-20:]) / 20 if n >= 20 else None
    ma60 = sum(closes[-60:]) / 60 if n >= 60 else None

    return {"ma20": ma20, "ma60": ma60}


def _find_nearest(current: float, levels: list[float]) -> tuple[float | None, float | None]:
    """현재가 기준 가장 가까운 지지선(<=현재가)과 저항선(>=현재가)을 찾는다."""
    supports = [l for l in levels if l <= current]
    resistances = [l for l in levels if l >= current]

    nearest_support = max(supports) if supports else None
    nearest_resistance = min(resistances) if resistances else None

    return nearest_support, nearest_resistance


def analyze_support_resistance(rows: list[dict]) -> dict:
    """종합 지지/저항선 분석.

    Args:
        rows: OHLCV dicts (날짜 오름차순).

    Returns:
        {pivot: {...}, swing_levels: [...], ma_levels: {...},
         nearest_support: float|None, nearest_resistance: float|None}

    Raises:
        ValueError: rows가 비어있을 때.
    """
    if not rows:
        raise ValueError("OHLCV 데이터가 비어있습니다.")

    current = rows[-1]["close"]

    pivot = compute_pivot_points(rows)
    swing_levels = find_swing_levels(rows)
    ma_levels = compute_ma_levels(rows)

    # 모든 레벨을 하나의 리스트로 수집
    all_levels: list[float] = []

    # 피봇 포인트 추가
    for key in ("pp", "s1", "s2", "r1", "r2"):
        if pivot[key] is not None:
            all_levels.append(pivot[key])

    # 스윙 레벨 추가
    for level in swing_levels:
        all_levels.append(level["price"])

    # MA 레벨 추가
    for key in ("ma20", "ma60"):
        if ma_levels[key] is not None:
            all_levels.append(ma_levels[key])

    nearest_support, nearest_resistance = _find_nearest(current, all_levels)

    return {
        "pivot": pivot,
        "swing_levels": swing_levels,
        "ma_levels": ma_levels,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
    }
