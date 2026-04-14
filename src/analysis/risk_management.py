"""리스크 관리 수준 분석 모듈.

기존 데이터(지지/저항, ATR, 변동성 체제, 시그널 강도, 수렴도)를 종합하여
투자자가 즉시 활용할 수 있는 리스크 관리 수준을 산출한다.
"""


_REGIME_ATR_MULT = {"고변동성": 2.0, "보통": 1.5, "저변동성": 1.0}

_SIGNAL_THRESHOLD = 15


def compute_entry_zone(
    current_price: float,
    nearest_support: float | None,
    atr: float,
    signal_score: float,
) -> dict:
    """시그널 강도에 따른 매수/매도 진입 구간 산출."""
    abs_score = abs(signal_score)

    if abs_score < _SIGNAL_THRESHOLD:
        return {
            "lower": current_price - atr * 0.5,
            "upper": current_price + atr * 0.5,
            "direction": "관망",
            "basis": "시그널 부재 — ATR 중심 레인지",
        }

    direction = "매수" if signal_score > 0 else "매도"
    strength = min(abs_score / 100, 1.0)

    support = nearest_support if nearest_support is not None else current_price - atr * 2

    if direction == "매수":
        lower = support + (current_price - support) * strength
        upper = current_price + atr * (0.3 + 0.2 * strength)
    else:
        lower = current_price - atr * (0.3 + 0.2 * strength)
        upper = current_price + (current_price - support) * (1 - strength) * 0.5

    return {
        "lower": round(lower, 0),
        "upper": round(upper, 0),
        "direction": direction,
        "basis": f"시그널 강도 {abs_score:.0f} — {'현재가 근처' if strength > 0.5 else '지지선 근처'}",
    }


def compute_stop_level(
    current_price: float,
    nearest_support: float | None,
    atr: float,
    volatility_regime: str,
) -> dict:
    """변동성 체제에 따른 손절 수준 산출."""
    mult = _REGIME_ATR_MULT.get(volatility_regime, 1.5)

    if nearest_support is not None:
        stop_from_support = nearest_support - atr * (mult * 0.5)
        stop_from_atr = current_price - atr * mult
        stop = min(stop_from_support, stop_from_atr)
        method = "지지선_ATR"
    else:
        stop = current_price - atr * mult
        method = "ATR_배수"

    return {
        "price": round(stop, 0),
        "method": method,
        "atr_multiplier": mult,
        "regime": volatility_regime,
    }


def compute_target_levels(
    current_price: float,
    nearest_resistance: float | None,
    atr: float,
    signal_score: float,
) -> dict:
    """1차/2차 목표가 수준 산출."""
    if abs(signal_score) < _SIGNAL_THRESHOLD:
        return {
            "target_1": {"price": current_price + atr, "basis": "ATR 1배"},
            "target_2": {"price": current_price + atr * 2.5, "basis": "ATR 2.5배"},
            "direction": "중립",
        }

    if signal_score > 0:
        resistance = nearest_resistance if nearest_resistance is not None else current_price + atr * 1.5
        t1 = resistance
        t2 = max(current_price + atr * 2.5, t1 + atr)
        return {
            "target_1": {"price": round(t1, 0), "basis": "최근접 저항선"},
            "target_2": {"price": round(t2, 0), "basis": "ATR 2.5배"},
            "direction": "상승",
        }
    else:
        t1_short = current_price - atr
        t2_short = current_price - atr * 2.5
        return {
            "target_1": {"price": round(t1_short, 0), "basis": "ATR 1배 하방"},
            "target_2": {"price": round(t2_short, 0), "basis": "ATR 2.5배 하방"},
            "direction": "하락",
        }


def compute_risk_reward_ratio(
    entry_price: float,
    target_price: float,
    stop_price: float,
) -> dict:
    """리스크/리워드 비율 산출."""
    risk = abs(entry_price - stop_price)
    reward = abs(target_price - entry_price)

    if risk == 0:
        return {"ratio": None, "grade": "산출불가", "risk": 0, "reward": reward}

    ratio = reward / risk

    if ratio >= 1.5:
        grade = "유리"
    elif ratio >= 1.0:
        grade = "보통"
    else:
        grade = "불리"

    return {"ratio": round(ratio, 2), "grade": grade, "risk": round(risk, 0), "reward": round(reward, 0)}


def determine_position_size_guide(
    volatility_regime: str,
    conviction: float,
    rr_ratio: float | None,
    convergence_level: str,
) -> dict:
    """변동성 + 확신도 + R:R + 수렴도 기반 포지션 사이즈 가이드."""
    score = 0

    vol_scores = {"저변동성": 2, "보통": 1, "고변동성": 0}
    score += vol_scores.get(volatility_regime, 1)

    if conviction >= 70:
        score += 2
    elif conviction >= 50:
        score += 1

    if rr_ratio is not None:
        if rr_ratio >= 2.0:
            score += 2
        elif rr_ratio >= 1.5:
            score += 1
        elif rr_ratio < 1.0:
            score -= 1

    conv_scores = {"strong": 2, "moderate": 1, "weak": 0, "mixed": -1}
    score += conv_scores.get(convergence_level, 0)

    if score >= 6:
        level = "공격적"
        desc = "다수 조건 유리 — 확대 진입 가능 구간"
    elif score >= 4:
        level = "표준"
        desc = "보통 조건 — 기본 진입 구간"
    elif score >= 1:
        level = "보수적"
        desc = "일부 불리 조건 — 축소 진입 권장"
    else:
        level = "관망"
        desc = "불리 조건 다수 — 진입 대기"

    return {"level": level, "description": desc, "score": score}


def compute_risk_levels(
    current_price: float,
    nearest_support: float | None,
    nearest_resistance: float | None,
    atr: float,
    atr_pct: float,
    volatility_regime: str,
    signal_score: float,
    convergence_level: str,
    conviction: float,
) -> dict:
    """리스크 관리 수준 통합 산출."""
    entry = compute_entry_zone(current_price, nearest_support, atr, signal_score)
    stop = compute_stop_level(current_price, nearest_support, atr, volatility_regime)
    targets = compute_target_levels(current_price, nearest_resistance, atr, signal_score)

    entry_mid = (entry["lower"] + entry["upper"]) / 2
    rr = compute_risk_reward_ratio(entry_mid, targets["target_1"]["price"], stop["price"])

    guide = determine_position_size_guide(
        volatility_regime, conviction, rr["ratio"], convergence_level,
    )

    if rr["ratio"] is not None:
        summary = f"R:R {rr['ratio']:.1f} — {rr['grade']}. {guide['level']} 포지션. (ATR {atr_pct:.1f}%)"
    else:
        summary = f"R:R 산출불가. {guide['level']} 포지션. (ATR {atr_pct:.1f}%)"

    return {
        "entry_zone": entry,
        "stop_level": stop,
        "target_levels": targets,
        "risk_reward": rr,
        "position_guide": guide,
        "summary": summary,
    }
