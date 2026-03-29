"""종합 투자 시그널 모듈.

기술적 분석(시장온도), 수급 판정, 환율 추세를 하나로 종합하여
-100~+100 점수와 5단계 판정을 반환한다.

가중치: 기술적 40%, 수급 40%, 환율 20%
"""


def _clamp(value: float, lo: float = -100.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _score_technical(tech: dict) -> float:
    """기술적 지표 → -100~+100 점수.

    RSI, MACD 히스토그램, 볼린저 %b, 이평선 괴리율을 종합.
    """
    scores: list[float] = []

    # RSI (14) — 30 이하 매수 과매도, 70 이상 매도 과매수
    rsi = tech.get("rsi_14")
    if rsi is not None:
        # RSI 50이 중립, 30→+100, 70→-100 (선형)
        rsi_score = _clamp((50 - rsi) * 5)  # 50→0, 30→+100, 70→-100
        scores.append(rsi_score)

    # MACD 히스토그램 — 양수면 매수, 음수면 매도
    macd_hist = tech.get("macd_histogram")
    if macd_hist is not None:
        # 히스토그램 크기에 비례 (±200 → ±100으로 정규화)
        macd_score = _clamp(macd_hist / 2)
        scores.append(macd_score)

    # 볼린저 %b — 0.2 이하 매수, 0.8 이상 매도
    pctb = tech.get("bb_pctb")
    if pctb is not None:
        # 0.5가 중립, 0→+100, 1→-100
        bb_score = _clamp((0.5 - pctb) * 200)
        scores.append(bb_score)

    # 이평선 괴리율 — MA5 위 매수, 아래 매도
    vs_ma5 = tech.get("price_vs_ma5_pct")
    if vs_ma5 is not None:
        ma_score = _clamp(vs_ma5 * 20)  # ±5% → ±100
        scores.append(ma_score)

    # 스토캐스틱 %K — 20 이하 매수, 80 이상 매도
    stoch_k = tech.get("stoch_k")
    if stoch_k is not None:
        # 50이 중립, 20→+100, 80→-100 (선형)
        stoch_score = _clamp((50 - stoch_k) * (100 / 30))
        scores.append(stoch_score)

    # OBV 다이버전스 — bearish(가격↑+OBV↓) 감점, bullish(가격↓+OBV↑) 가점
    obv_div = tech.get("obv_divergence")
    if obv_div == "bearish":
        scores.append(-60.0)
    elif obv_div == "bullish":
        scores.append(60.0)

    if not scores:
        return 0.0
    return _clamp(sum(scores) / len(scores))


def _score_supply(supply: dict) -> float:
    """수급 판정 → -100~+100 점수.

    overall_judgment + 연속 매수/매도 일수를 반영.
    """
    judgment = supply.get("overall_judgment", "neutral")
    base = {"buy_dominant": 60, "sell_dominant": -60, "neutral": 0}.get(judgment, 0)

    # 연속 매수/매도 일수로 가감 (최대 ±40)
    foreign_buy = supply.get("foreign_consecutive_net_buy", 0)
    foreign_sell = supply.get("foreign_consecutive_net_sell", 0)
    inst_buy = supply.get("institution_consecutive_net_buy", 0)
    inst_sell = supply.get("institution_consecutive_net_sell", 0)

    consec_bonus = (foreign_buy + inst_buy - foreign_sell - inst_sell) * 8
    consec_bonus = max(-40, min(40, consec_bonus))

    return _clamp(base + consec_bonus)


def _score_exchange(fx: dict) -> float:
    """환율 추세 → -100~+100 점수.

    삼성전자는 수출 기업이므로:
    - 원화약세(환율 상승) → 매수 신호 (수출 이익 ↑)
    - 원화강세(환율 하락) → 매도 신호 (수출 이익 ↓)
    """
    trend = fx.get("trend")
    base = {"원화약세": 60, "원화강세": -60, "보합": 0}.get(trend, 0) if trend else 0

    # 일일 변동률로 강도 조절
    change_1d = fx.get("change_1d_pct")
    if change_1d is not None:
        # 환율 상승 → 매수(양수), 환율 하락 → 매도(음수)
        daily_adj = _clamp(change_1d * 20, -40, 40)
        base += daily_adj

    return _clamp(base)


def _grade_from_score(score: float) -> str:
    """점수 → 5단계 판정."""
    if score >= 60:
        return "강력매수신호"
    elif score >= 20:
        return "매수우세"
    elif score > -20:
        return "중립"
    elif score > -60:
        return "매도우세"
    else:
        return "강력매도신호"


def _score_relative_strength(rs: dict) -> float:
    """상대강도 분석 → -100~+100 점수.

    삼성전자가 KOSPI를 상회하면 양수, 하회하면 음수.
    """
    trend = rs.get("rs_trend")
    base = {"outperform": 50, "underperform": -50, "neutral": 0}.get(trend, 0)

    # 1일 alpha로 강도 조절
    alpha_1d = rs.get("alpha_1d")
    if alpha_1d is not None:
        base += _clamp(alpha_1d * 10, -50, 50)

    return _clamp(base)


def _score_fundamentals(fund: dict) -> float:
    """펀더멘털 분석 → -100~+100 점수.

    PER/PBR 밸류에이션, 배당수익률, 실적 전망을 종합.
    """
    scores: list[float] = []

    # PER 밸류에이션
    per_val = fund.get("per_valuation")
    if per_val == "저평가":
        scores.append(60.0)
    elif per_val == "고평가":
        scores.append(-60.0)
    elif per_val == "적정":
        scores.append(0.0)

    # PBR 밸류에이션
    pbr_val = fund.get("pbr_valuation")
    if pbr_val == "저평가":
        scores.append(60.0)
    elif pbr_val == "고평가":
        scores.append(-60.0)
    elif pbr_val == "적정":
        scores.append(0.0)

    # 배당수익률 매력도
    div_attr = fund.get("dividend_attractiveness")
    if div_attr == "매력적":
        scores.append(40.0)
    elif div_attr == "낮음":
        scores.append(-20.0)
    elif div_attr == "보통":
        scores.append(10.0)

    # 실적 전망
    outlook = fund.get("earnings_outlook")
    if outlook == "개선":
        scores.append(50.0)
    elif outlook == "악화":
        scores.append(-50.0)
    elif outlook == "유지":
        scores.append(0.0)

    if not scores:
        return 0.0
    return _clamp(sum(scores) / len(scores))


def _reversal_bonus(trend_reversal: dict) -> float:
    """추세 전환 컨버전스에 따른 보너스/페널티 점수.

    strong → ±15, moderate → ±8, weak/none → 0.
    방향이 bullish면 양수(매수 보너스), bearish면 음수(매도 페널티).
    """
    convergence = trend_reversal.get("convergence", "none")
    direction = trend_reversal.get("direction", "neutral")

    if convergence == "strong":
        magnitude = 15.0
    elif convergence == "moderate":
        magnitude = 8.0
    else:
        return 0.0

    if direction == "bullish":
        return magnitude
    elif direction == "bearish":
        return -magnitude
    return 0.0


def compute_composite_signal(
    technical: dict,
    supply_demand: dict,
    exchange_rate: dict,
    relative_strength: dict | None = None,
    trend_reversal: dict | None = None,
    fundamentals: dict | None = None,
) -> dict:
    """종합 투자 시그널을 계산한다.

    Args:
        technical: compute_technical_indicators() 결과
        supply_demand: analyze_supply_demand() 결과
        exchange_rate: analyze_exchange_rate() 결과
        relative_strength: compute_relative_strength() 결과 (선택)
        trend_reversal: detect_reversal_signals() 결과 (선택)
        fundamentals: analyze_fundamentals() 결과 (선택)

    Returns:
        dict with:
            score: -100~+100 종합 점수
            grade: 5단계 판정 문자열
            technical_score: 기술적 축 점수 (-100~+100)
            supply_score: 수급 축 점수 (-100~+100)
            exchange_score: 환율 축 점수 (-100~+100)
            rs_score: 상대강도 축 점수 (-100~+100) (선택)
            fundamentals_score: 펀더멘털 축 점수 (-100~+100) (선택)
            weights: 각 축 가중치 (%)
    """
    tech_score = _score_technical(technical)
    sup_score = _score_supply(supply_demand)
    fx_score = _score_exchange(exchange_rate)

    has_rs = relative_strength is not None
    has_fund = fundamentals is not None

    rs_score = _score_relative_strength(relative_strength) if has_rs else None
    fund_score = _score_fundamentals(fundamentals) if has_fund else None

    if has_rs and has_fund:
        # 5축: 기술 30%, 수급 30%, 환율 15%, 상대강도 10%, 펀더멘털 15%
        composite = (tech_score * 0.30 + sup_score * 0.30 + fx_score * 0.15
                     + rs_score * 0.10 + fund_score * 0.15)
        weights = {"technical": 30, "supply": 30, "exchange": 15,
                   "relative_strength": 10, "fundamentals": 15}
    elif has_rs:
        # 4축 (RS만): 기술 35%, 수급 35%, 환율 15%, 상대강도 15%
        composite = tech_score * 0.35 + sup_score * 0.35 + fx_score * 0.15 + rs_score * 0.15
        weights = {"technical": 35, "supply": 35, "exchange": 15, "relative_strength": 15}
    elif has_fund:
        # 4축 (펀더멘털만): 기술 35%, 수급 30%, 환율 15%, 펀더멘털 20%
        composite = tech_score * 0.35 + sup_score * 0.30 + fx_score * 0.15 + fund_score * 0.20
        weights = {"technical": 35, "supply": 30, "exchange": 15, "fundamentals": 20}
    else:
        # 3축: 기술 40%, 수급 40%, 환율 20%
        composite = tech_score * 0.4 + sup_score * 0.4 + fx_score * 0.2
        weights = {"technical": 40, "supply": 40, "exchange": 20}

    # 추세 전환 컨버전스 보너스/페널티
    if trend_reversal is not None:
        composite += _reversal_bonus(trend_reversal)

    composite = _clamp(composite)

    result = {
        "score": composite,
        "grade": _grade_from_score(composite),
        "technical_score": tech_score,
        "supply_score": sup_score,
        "exchange_score": fx_score,
        "weights": weights,
    }
    if rs_score is not None:
        result["rs_score"] = rs_score
    if fund_score is not None:
        result["fundamentals_score"] = fund_score
    return result
