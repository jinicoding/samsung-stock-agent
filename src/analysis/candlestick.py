"""캔들스틱 패턴 인식 모듈.

OHLCV 데이터에서 핵심 캔들스틱 패턴을 감지하고
종합 패턴 시그널(bullish/bearish/neutral)과 점수(-100~+100)를 반환한다.

단일 캔들 패턴: 도지, 해머, 행잉맨, 마루보즈
복합 캔들 패턴: 강세/약세 인걸핑, 모닝스타, 이브닝스타
"""


def _body(candle: dict) -> float:
    """몸통 크기 (절대값)."""
    return abs(candle["close"] - candle["open"])


def _range(candle: dict) -> float:
    """전체 범위 (고가 - 저가)."""
    return candle["high"] - candle["low"]


def _upper_shadow(candle: dict) -> float:
    """윗꼬리 길이."""
    return candle["high"] - max(candle["open"], candle["close"])


def _lower_shadow(candle: dict) -> float:
    """아래꼬리 길이."""
    return min(candle["open"], candle["close"]) - candle["low"]


def _is_bullish(candle: dict) -> bool:
    return candle["close"] > candle["open"]


def _is_bearish(candle: dict) -> bool:
    return candle["close"] < candle["open"]


def _is_uptrend(rows: list[dict], lookback: int = 3) -> bool:
    """최근 lookback개 캔들이 상승 추세인지 판단."""
    if len(rows) < lookback:
        return False
    closes = [r["close"] for r in rows[-lookback:]]
    return closes[-1] > closes[0]


def _is_downtrend(rows: list[dict], lookback: int = 3) -> bool:
    """최근 lookback개 캔들이 하락 추세인지 판단."""
    if len(rows) < lookback:
        return False
    closes = [r["close"] for r in rows[-lookback:]]
    return closes[-1] < closes[0]


def _detect_single_patterns(candle: dict, prior_rows: list[dict]) -> list[dict]:
    """단일 캔들 패턴 감지."""
    patterns = []
    body = _body(candle)
    rng = _range(candle)
    lower = _lower_shadow(candle)
    upper = _upper_shadow(candle)

    if rng == 0:
        return patterns

    body_ratio = body / rng

    # 도지 (Doji): 몸통이 전체 범위의 10% 이하
    if body_ratio <= 0.1:
        patterns.append({
            "name": "doji",
            "direction": "neutral",
            "weight": 20,
        })

    # 해머 (Hammer): 하락 추세 + 아래꼬리가 몸통의 2배 이상 + 윗꼬리 짧음
    if (body > 0
            and lower >= body * 2
            and upper <= body * 0.5
            and _is_downtrend(prior_rows)):
        patterns.append({
            "name": "hammer",
            "direction": "bullish",
            "weight": 50,
        })

    # 행잉맨 (Hanging Man): 상승 추세 + 해머와 동일한 형태
    if (body > 0
            and lower >= body * 2
            and upper <= body * 0.5
            and _is_uptrend(prior_rows)):
        patterns.append({
            "name": "hanging_man",
            "direction": "bearish",
            "weight": 50,
        })

    # 강세 마루보즈 (Bullish Marubozu): 양봉 + 꼬리가 전체 범위의 5% 이하
    if (_is_bullish(candle)
            and body_ratio >= 0.9
            and rng > 0):
        patterns.append({
            "name": "bullish_marubozu",
            "direction": "bullish",
            "weight": 60,
        })

    # 약세 마루보즈 (Bearish Marubozu): 음봉 + 꼬리가 전체 범위의 5% 이하
    if (_is_bearish(candle)
            and body_ratio >= 0.9
            and rng > 0):
        patterns.append({
            "name": "bearish_marubozu",
            "direction": "bearish",
            "weight": 60,
        })

    return patterns


def _detect_two_candle_patterns(prev: dict, curr: dict) -> list[dict]:
    """2봉 복합 캔들 패턴 감지."""
    patterns = []

    prev_body = _body(prev)
    curr_body = _body(curr)

    # 강세 인걸핑 (Bullish Engulfing): 음봉 후 더 큰 양봉이 감쌈
    if (_is_bearish(prev) and _is_bullish(curr)
            and curr["open"] <= prev["close"]
            and curr["close"] >= prev["open"]
            and curr_body > prev_body):
        patterns.append({
            "name": "bullish_engulfing",
            "direction": "bullish",
            "weight": 70,
        })

    # 약세 인걸핑 (Bearish Engulfing): 양봉 후 더 큰 음봉이 감쌈
    if (_is_bullish(prev) and _is_bearish(curr)
            and curr["open"] >= prev["close"]
            and curr["close"] <= prev["open"]
            and curr_body > prev_body):
        patterns.append({
            "name": "bearish_engulfing",
            "direction": "bearish",
            "weight": 70,
        })

    return patterns


def _detect_three_candle_patterns(
    first: dict, second: dict, third: dict,
) -> list[dict]:
    """3봉 복합 캔들 패턴 감지."""
    patterns = []

    first_body = _body(first)
    second_body = _body(second)
    third_body = _body(third)
    first_range = _range(first)

    # 큰 봉의 기준: 첫째 봉 몸통의 30% 이상
    small_body_threshold = first_body * 0.3 if first_body > 0 else first_range * 0.1

    # 모닝스타 (Morning Star): 큰 음봉 + 작은 몸통 + 큰 양봉
    if (_is_bearish(first)
            and first_body > 0
            and second_body <= small_body_threshold
            and _is_bullish(third)
            and third_body > first_body * 0.5
            and third["close"] > (first["open"] + first["close"]) / 2):
        patterns.append({
            "name": "morning_star",
            "direction": "bullish",
            "weight": 80,
        })

    # 이브닝스타 (Evening Star): 큰 양봉 + 작은 몸통 + 큰 음봉
    if (_is_bullish(first)
            and first_body > 0
            and second_body <= small_body_threshold
            and _is_bearish(third)
            and third_body > first_body * 0.5
            and third["close"] < (first["open"] + first["close"]) / 2):
        patterns.append({
            "name": "evening_star",
            "direction": "bearish",
            "weight": 80,
        })

    return patterns


def _clamp(value: float, lo: float = -100.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def detect_candlestick_patterns(rows: list[dict]) -> dict:
    """OHLCV rows에서 캔들스틱 패턴을 감지한다.

    Args:
        rows: DB에서 가져온 OHLCV dicts (날짜 오름차순).
              각 dict: {date, open, high, low, close, volume}

    Returns:
        dict with:
            patterns: list[dict] — 감지된 패턴 리스트
                각 패턴: {name, direction, weight}
            signal: "bullish" | "bearish" | "neutral"
            score: -100~+100 종합 패턴 점수

    Raises:
        ValueError: rows가 비어있을 때.
    """
    if not rows:
        raise ValueError("OHLCV 데이터가 비어있습니다.")

    patterns: list[dict] = []

    # 단일 캔들 패턴 (마지막 봉 기준)
    last = rows[-1]
    prior = rows[:-1] if len(rows) > 1 else []
    patterns.extend(_detect_single_patterns(last, prior))

    # 2봉 패턴
    if len(rows) >= 2:
        patterns.extend(_detect_two_candle_patterns(rows[-2], rows[-1]))

    # 3봉 패턴
    if len(rows) >= 3:
        patterns.extend(
            _detect_three_candle_patterns(rows[-3], rows[-2], rows[-1]),
        )

    # 종합 점수 계산: 각 패턴의 direction * weight 합산
    if not patterns:
        return {"patterns": [], "signal": "neutral", "score": 0}

    total_weight = 0
    weighted_score = 0.0
    for p in patterns:
        w = p["weight"]
        if p["direction"] == "bullish":
            weighted_score += w
        elif p["direction"] == "bearish":
            weighted_score -= w
        # neutral은 점수에 기여하지 않지만 weight는 분모에 포함
        total_weight += w

    score = _clamp(weighted_score / total_weight * 100) if total_weight > 0 else 0

    if score > 10:
        signal = "bullish"
    elif score < -10:
        signal = "bearish"
    else:
        signal = "neutral"

    return {
        "patterns": patterns,
        "signal": signal,
        "score": score,
    }
