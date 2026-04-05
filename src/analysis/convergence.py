"""Multi-Axis Convergence Analysis (다축 수렴 분석).

각 분석 축의 개별 점수를 입력받아 몇 개의 축이 같은 방향을 가리키는지 감지한다.
수렴도가 높을수록 시그널의 신뢰도가 높다.
"""

# 9개 축 이름 (전체 집합)
ALL_AXES = [
    "technical_score",
    "supply_score",
    "exchange_score",
    "fundamental_score",
    "news_score",
    "consensus_score",
    "semiconductor_score",
    "volatility_score",
    "candlestick_score",
]

# 방향 분류 임계값
DIRECTION_THRESHOLD = 15


def classify_direction(score: float) -> str:
    """점수를 방향으로 분류한다. 임계값: ±15."""
    if score > DIRECTION_THRESHOLD:
        return "bullish"
    elif score < -DIRECTION_THRESHOLD:
        return "bearish"
    return "neutral"


def analyze_convergence(scores: dict) -> dict:
    """다축 수렴 분석을 수행한다.

    Args:
        scores: 축 이름 → 점수 (-100~+100) 딕셔너리.
                누락된 축은 분석에서 제외된다.

    Returns:
        dict with:
            convergence_level: strong/moderate/weak/mixed
            dominant_direction: bullish/bearish/neutral
            aligned_axes: 지배적 방향과 일치하는 축 이름 리스트
            conflicting_axes: 지배적 방향과 반대인 축 이름 리스트
            neutral_axes: 중립 축 이름 리스트
            conviction: 확신도 (0-100)
            axis_directions: 각 축별 방향 딕셔너리
    """
    # 제공된 축만 분석
    axis_directions: dict[str, str] = {}
    for axis in ALL_AXES:
        if axis in scores:
            axis_directions[axis] = classify_direction(scores[axis])

    # 방향별 축 분류
    bullish_axes = [a for a, d in axis_directions.items() if d == "bullish"]
    bearish_axes = [a for a, d in axis_directions.items() if d == "bearish"]
    neutral_axes = [a for a, d in axis_directions.items() if d == "neutral"]

    # 지배적 방향 결정
    if len(bullish_axes) > len(bearish_axes):
        dominant = "bullish"
        aligned = bullish_axes
        conflicting = bearish_axes
    elif len(bearish_axes) > len(bullish_axes):
        dominant = "bearish"
        aligned = bearish_axes
        conflicting = bullish_axes
    else:
        # 동수이면 neutral
        dominant = "neutral"
        aligned = []
        conflicting = []

    aligned_count = len(aligned)

    # 수렴도 판정
    if aligned_count >= 7:
        level = "strong"
    elif aligned_count >= 5:
        level = "moderate"
    elif aligned_count >= 3:
        level = "weak"
    else:
        level = "mixed"

    # 확신도 계산: (일치 축 수 / 전체 축 수) × 100, 충돌 축이 있으면 감점
    total = len(axis_directions)
    if total == 0:
        conviction = 0
    else:
        base = (aligned_count / total) * 100
        conflict_penalty = (len(conflicting) / total) * 30
        conviction = max(0, min(100, round(base - conflict_penalty)))

    return {
        "convergence_level": level,
        "dominant_direction": dominant,
        "aligned_axes": aligned,
        "conflicting_axes": conflicting,
        "neutral_axes": neutral_axes,
        "conviction": conviction,
        "axis_directions": axis_directions,
    }
