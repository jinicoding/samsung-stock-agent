"""추세 전환 감지 모듈 — 시그널 컨버전스(convergence) 엔진.

기술적 지표와 지지/저항선을 5개 카테고리로 분류하여
각 카테고리별 강세/약세 반전 신호를 감지하고 가중 점수(0~100)로 합산한다.

카테고리:
  1. 모멘텀(momentum): RSI, 스토캐스틱
  2. 추세(trend): MACD 히스토그램, MA 괴리율
  3. 변동성(volatility): 볼린저밴드 %b
  4. 거래량(volume): OBV 다이버전스, 거래량비율
  5. 구조(structure): 지지/저항선 근접도

핵심: 단일 지표가 아닌 "몇 개 카테고리에서 동시에 신호가 나오는가"로
컨버전스 등급(strong/moderate/weak/none)을 판정.
"""

# 카테고리별 가중치 (합계 100)
_CATEGORY_WEIGHTS = {
    "momentum": 25,
    "trend": 25,
    "volatility": 20,
    "volume": 15,
    "structure": 15,
}

# 지지/저항선 근접 판정 임계값 (%)
_STRUCTURE_THRESHOLD_PCT = 1.0


def _detect_momentum(tech: dict) -> dict:
    """모멘텀 카테고리: RSI + 스토캐스틱."""
    rsi = tech.get("rsi_14")
    stoch_k = tech.get("stoch_k")

    bullish_count = 0
    bearish_count = 0
    total_strength = 0.0
    n_indicators = 0

    if rsi is not None:
        n_indicators += 1
        if rsi <= 30:
            bullish_count += 1
            # RSI 30→50%, RSI 15→100%
            total_strength += min(100.0, 50 + (30 - rsi) / 15 * 50)
        elif rsi >= 70:
            bearish_count += 1
            total_strength += min(100.0, 50 + (rsi - 70) / 15 * 50)

    if stoch_k is not None:
        n_indicators += 1
        if stoch_k <= 20:
            bullish_count += 1
            total_strength += min(100.0, 50 + (20 - stoch_k) / 10 * 50)
        elif stoch_k >= 80:
            bearish_count += 1
            total_strength += min(100.0, 50 + (stoch_k - 80) / 10 * 50)

    if n_indicators == 0:
        return {"direction": "neutral", "strength": 0.0}

    if bullish_count > bearish_count:
        direction = "bullish"
    elif bearish_count > bullish_count:
        direction = "bearish"
    else:
        direction = "neutral"

    active = bullish_count + bearish_count
    strength = min(100.0, total_strength / active) if active > 0 else 0.0

    if direction == "neutral":
        strength = 0.0

    return {"direction": direction, "strength": strength}


def _detect_trend(tech: dict) -> dict:
    """추세 카테고리: MACD 히스토그램 + MA 괴리율."""
    macd_hist = tech.get("macd_histogram")
    ma20_pct = tech.get("price_vs_ma20_pct")

    bullish_count = 0
    bearish_count = 0
    total_strength = 0.0
    n_indicators = 0

    if macd_hist is not None:
        n_indicators += 1
        # MACD 히스토그램 절대값이 20 이상이어야 의미 있는 신호
        if macd_hist >= 20:
            bullish_count += 1
            total_strength += min(100.0, 50 + abs(macd_hist) / 100 * 50)
        elif macd_hist <= -20:
            bearish_count += 1
            total_strength += min(100.0, 50 + abs(macd_hist) / 100 * 50)

    if ma20_pct is not None:
        n_indicators += 1
        # MA20 아래(-3% 이하)에서 반등 → 강세, 위(+3% 이상)에서 과열 → 약세
        if ma20_pct <= -3.0:
            bullish_count += 1
            total_strength += min(100.0, 50 + abs(ma20_pct) / 10 * 50)
        elif ma20_pct >= 3.0:
            bearish_count += 1
            total_strength += min(100.0, 50 + abs(ma20_pct) / 10 * 50)

    if n_indicators == 0:
        return {"direction": "neutral", "strength": 0.0}

    if bullish_count > bearish_count:
        direction = "bullish"
    elif bearish_count > bullish_count:
        direction = "bearish"
    else:
        # 동수면 중립 (충돌)
        direction = "neutral"

    active = bullish_count + bearish_count
    strength = min(100.0, total_strength / active) if active > 0 else 0.0

    if direction == "neutral":
        strength = 0.0

    return {"direction": direction, "strength": strength}


def _detect_volatility(tech: dict) -> dict:
    """변동성 카테고리: 볼린저밴드 %b."""
    pctb = tech.get("bb_pctb")

    if pctb is None:
        return {"direction": "neutral", "strength": 0.0}

    if pctb <= 0.1:
        # 하단밴드 이탈/근접 → 강세 반전 (바운스 기대)
        strength = min(100.0, 50 + (0.1 - pctb) / 0.1 * 50)
        return {"direction": "bullish", "strength": strength}
    elif pctb >= 0.9:
        # 상단밴드 이탈/근접 → 약세 반전 (과열)
        strength = min(100.0, 50 + (pctb - 0.9) / 0.1 * 50)
        return {"direction": "bearish", "strength": strength}

    return {"direction": "neutral", "strength": 0.0}


def _detect_volume(tech: dict) -> dict:
    """거래량 카테고리: OBV 다이버전스 + 거래량비율."""
    obv_div = tech.get("obv_divergence")
    vol_ratio = tech.get("volume_ratio_5d")

    bullish_count = 0
    bearish_count = 0
    total_strength = 0.0
    n_indicators = 0

    if obv_div is not None:
        n_indicators += 1
        if obv_div == "bullish":
            bullish_count += 1
            total_strength += 80.0
        elif obv_div == "bearish":
            bearish_count += 1
            total_strength += 80.0

    if vol_ratio is not None:
        n_indicators += 1
        # 거래량 급증(2배 이상) → 반전 가능성 (방향은 다른 지표와 함께 판단)
        if vol_ratio >= 2.0:
            # OBV 방향이 있으면 그 방향으로 가중
            if obv_div == "bullish":
                bullish_count += 1
                total_strength += min(100.0, (vol_ratio - 1.0) * 50)
            elif obv_div == "bearish":
                bearish_count += 1
                total_strength += min(100.0, (vol_ratio - 1.0) * 50)
            # OBV 없으면 거래량 급증만으로는 방향 판단 못함

    if n_indicators == 0:
        return {"direction": "neutral", "strength": 0.0}

    if bullish_count > bearish_count:
        direction = "bullish"
    elif bearish_count > bullish_count:
        direction = "bearish"
    else:
        direction = "neutral"

    active = bullish_count + bearish_count
    strength = min(100.0, total_strength / active) if active > 0 else 0.0

    if direction == "neutral":
        strength = 0.0

    return {"direction": direction, "strength": strength}


def _detect_structure(tech: dict, sr: dict) -> dict:
    """구조 카테고리: 지지/저항선 근접도."""
    current = tech.get("current_price")
    support = sr.get("nearest_support")
    resistance = sr.get("nearest_resistance")

    if current is None:
        return {"direction": "neutral", "strength": 0.0}

    support_pct = None
    resistance_pct = None

    if support is not None and current > 0:
        support_pct = (current - support) / current * 100

    if resistance is not None and current > 0:
        resistance_pct = (resistance - current) / current * 100

    # 지지선에 근접 (임계값 이내) → 강세 반전 기대
    if support_pct is not None and support_pct <= _STRUCTURE_THRESHOLD_PCT:
        strength = min(100.0, 50 + (1.0 - support_pct / _STRUCTURE_THRESHOLD_PCT) * 50)
        return {"direction": "bullish", "strength": strength}

    # 저항선에 근접 (임계값 이내) → 약세 반전 기대
    if resistance_pct is not None and resistance_pct <= _STRUCTURE_THRESHOLD_PCT:
        strength = min(100.0, 50 + (1.0 - resistance_pct / _STRUCTURE_THRESHOLD_PCT) * 50)
        return {"direction": "bearish", "strength": strength}

    return {"direction": "neutral", "strength": 0.0}


def _determine_convergence(
    category_signals: dict[str, dict],
) -> tuple[str, int, str]:
    """카테고리 신호들의 컨버전스를 판정한다.

    Returns:
        (convergence_grade, active_categories, dominant_direction)
    """
    bullish_cats = 0
    bearish_cats = 0

    for sig in category_signals.values():
        if sig["direction"] == "bullish":
            bullish_cats += 1
        elif sig["direction"] == "bearish":
            bearish_cats += 1

    # 같은 방향의 카테고리 수로 컨버전스 판정
    dominant_count = max(bullish_cats, bearish_cats)

    if bullish_cats > bearish_cats:
        direction = "bullish"
    elif bearish_cats > bullish_cats:
        direction = "bearish"
    else:
        direction = "neutral"

    # 컨버전스 등급: 같은 방향의 활성 카테고리 기준
    if dominant_count >= 4:
        grade = "strong"
    elif dominant_count == 3:
        grade = "moderate"
    elif dominant_count >= 1:
        grade = "weak"
    else:
        grade = "none"

    # 혼합 신호 (양방향 모두 활성) → 등급 하향
    if bullish_cats > 0 and bearish_cats > 0:
        # 충돌하는 신호가 있으면 한 단계 하향
        if grade == "strong":
            grade = "moderate"
        elif grade == "moderate":
            grade = "weak"

    return grade, dominant_count, direction


def _compute_weighted_score(category_signals: dict[str, dict], direction: str) -> float:
    """카테고리별 가중 점수를 합산한다 (0~100).

    주도 방향과 같은 방향의 활성 카테고리만 가중치에 포함.
    중립 카테고리는 점수 희석을 방지하기 위해 제외.
    """
    if direction == "neutral":
        return 0.0

    total_score = 0.0
    active_weight = 0

    for cat, sig in category_signals.items():
        if sig["direction"] == direction:
            weight = _CATEGORY_WEIGHTS[cat]
            active_weight += weight
            total_score += sig["strength"] * weight / 100

    if active_weight == 0:
        return 0.0

    return min(100.0, total_score / active_weight * 100)


def _build_summary(
    direction: str,
    convergence: str,
    active_categories: int,
    score: float,
    category_signals: dict[str, dict],
) -> str:
    """사람이 읽을 수 있는 요약 문장을 생성한다."""
    if convergence == "none":
        return "현재 뚜렷한 추세 전환 신호가 감지되지 않습니다."

    dir_kr = "강세" if direction == "bullish" else "약세"
    grade_kr = {
        "strong": "강한",
        "moderate": "중간",
        "weak": "약한",
    }.get(convergence, "")

    active_names = []
    cat_kr = {
        "momentum": "모멘텀",
        "trend": "추세",
        "volatility": "변동성",
        "volume": "거래량",
        "structure": "구조",
    }
    for cat, sig in category_signals.items():
        if sig["direction"] == direction:
            active_names.append(cat_kr[cat])

    cats_str = ", ".join(active_names)
    return (
        f"{grade_kr} {dir_kr} 반전 신호 감지 "
        f"(컨버전스 점수: {score:.0f}/100, "
        f"활성 카테고리 {active_categories}개: {cats_str})"
    )


def detect_reversal_signals(tech_indicators: dict, support_resistance: dict) -> dict:
    """추세 전환 신호를 감지한다.

    Args:
        tech_indicators: compute_technical_indicators() 결과
        support_resistance: analyze_support_resistance() 결과

    Returns:
        dict:
            direction: "bullish" | "bearish" | "neutral"
            convergence: "strong" | "moderate" | "weak" | "none"
            score: 0~100 가중 점수
            active_categories: 활성 카테고리 수 (주도 방향 기준)
            category_signals: {category: {direction, strength}} 5개 카테고리 상세
            summary: 요약 문자열
    """
    category_signals = {
        "momentum": _detect_momentum(tech_indicators),
        "trend": _detect_trend(tech_indicators),
        "volatility": _detect_volatility(tech_indicators),
        "volume": _detect_volume(tech_indicators),
        "structure": _detect_structure(tech_indicators, support_resistance),
    }

    convergence, active_categories, direction = _determine_convergence(category_signals)
    score = _compute_weighted_score(category_signals, direction)

    summary = _build_summary(
        direction, convergence, active_categories, score, category_signals,
    )

    return {
        "direction": direction,
        "convergence": convergence,
        "score": score,
        "active_categories": active_categories,
        "category_signals": category_signals,
        "summary": summary,
    }
