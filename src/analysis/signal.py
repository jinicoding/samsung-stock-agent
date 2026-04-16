"""종합 투자 시그널 모듈.

기술적 분석(시장온도), 수급 판정, 환율 추세를 하나로 종합하여
-100~+100 점수와 5단계 판정을 반환한다.

가중치: 기술적 40%, 수급 40%, 환율 20% (기본 3축)
최대 10축 분석 체계: 기술적, 수급, 환율, 상대강도, 펀더멘털, 뉴스, 컨센서스, 반도체, 변동성/캔들스틱, 글로벌매크로
적응형 가중치: accuracy_summary 제공 시 축별 적중률 기반 ±30% 동적 조정.
"""

from __future__ import annotations

# 축 이름 → accuracy per_axis 키 매핑
_AXIS_TO_ACCURACY_KEY: dict[str, str] = {
    "technical": "technical_score",
    "supply": "supply_score",
    "exchange": "exchange_score",
    "relative_strength": "rs_score",
    "fundamentals": "fundamentals_score",
    "news": "news_score",
    "consensus": "consensus_score",
    "semiconductor": "semiconductor_score",
    "volatility": "volatility_score",
    "candlestick": "candlestick_score",
    "global_macro": "global_macro_score",
}


def adapt_weights(
    base_weights: dict[str, int],
    accuracy_summary: dict,
    max_adj: float = 0.30,
    min_evaluated: int = 5,
) -> dict[str, int]:
    """축별 적중률(hit_rate_5d) 기반으로 가중치를 동적 조정한다.

    Args:
        base_weights: 축 이름 → 정적 가중치(%) 맵.
        accuracy_summary: evaluate_signals() 반환값의 summary.
        max_adj: 최대 조정 비율 (기본 0.30 = ±30%).
        min_evaluated: 이 수 미만의 평가 데이터가 있는 축은 조정하지 않음.

    Returns:
        조정된 가중치(%) 맵. 합계는 항상 100.
    """
    per_axis = accuracy_summary.get("per_axis", {})
    if not per_axis:
        return dict(base_weights)

    # 1) 각 축의 적중률 수집 (데이터 부족 또는 None이면 제외)
    hit_rates: dict[str, float] = {}
    for axis in base_weights:
        acc_key = _AXIS_TO_ACCURACY_KEY.get(axis, axis + "_score")
        axis_data = per_axis.get(acc_key, {})
        hr = axis_data.get("hit_rate_5d")
        ev = axis_data.get("evaluated_5d", 0)
        if hr is not None and ev >= min_evaluated:
            hit_rates[axis] = hr

    # 조정 가능한 축이 없으면 원본 반환
    if not hit_rates:
        return dict(base_weights)

    # 평균 적중률 (조정 대상 축만)
    avg_hr = sum(hit_rates.values()) / len(hit_rates)

    # 2) 적중률 편차로 raw 조정 계수 산출 (±max_adj)
    raw_factors: dict[str, float] = {}
    for axis in base_weights:
        if axis in hit_rates:
            deviation = hit_rates[axis] - avg_hr  # -100~+100 범위
            # deviation을 ±50 기준으로 ±max_adj에 매핑
            factor = 1.0 + (deviation / 50.0) * max_adj
            factor = max(1.0 - max_adj, min(1.0 + max_adj, factor))
        else:
            factor = 1.0  # 데이터 부족: 조정 안 함
        raw_factors[axis] = factor

    # 3) raw 가중치 산출 후 정규화하여 합 100 유지
    raw_weights = {k: base_weights[k] * raw_factors[k] for k in base_weights}
    total_raw = sum(raw_weights.values())

    if total_raw == 0:
        return dict(base_weights)

    # 정규화 + 반올림
    adjusted = {k: round(v / total_raw * 100) for k, v in raw_weights.items()}

    # 반올림 오차 보정: 가장 큰 축에서 조정
    diff = 100 - sum(adjusted.values())
    if diff != 0:
        largest = max(adjusted, key=adjusted.get)  # type: ignore[arg-type]
        adjusted[largest] += diff

    return adjusted


def _clamp(value: float, lo: float = -100.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _score_technical(tech: dict, market_regime: dict | None = None) -> float:
    """기술적 지표 → -100~+100 점수.

    RSI, MACD 히스토그램, 볼린저 %b, 이평선 괴리율을 종합.
    market_regime 제공 시 체제별 RSI 임계값을 조정한다.
    """
    scores: list[float] = []

    # 체제별 RSI 임계값 결정
    rsi_overbought = 70.0
    rsi_oversold = 30.0
    if market_regime is not None and market_regime.get("confidence", 0) >= 50:
        hints = market_regime.get("interpretation_hints", {})
        thresholds = hints.get("rsi_thresholds", {})
        rsi_overbought = thresholds.get("overbought", 70.0)
        rsi_oversold = thresholds.get("oversold", 30.0)

    # RSI 중립점과 스케일링: 중립 = (overbought + oversold) / 2
    rsi_midpoint = (rsi_overbought + rsi_oversold) / 2.0
    rsi_half_range = (rsi_overbought - rsi_oversold) / 2.0

    rsi = tech.get("rsi_14")
    if rsi is not None:
        # RSI midpoint이 중립, oversold→+100, overbought→-100 (선형)
        if rsi_half_range > 0:
            rsi_score = _clamp((rsi_midpoint - rsi) / rsi_half_range * 100)
        else:
            rsi_score = _clamp((50 - rsi) * 5)
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
    raw = sum(scores) / len(scores)

    # ADX 기반 확신도 조절
    adx = tech.get("adx")
    if adx is not None:
        plus_di = tech.get("plus_di", 0)
        minus_di = tech.get("minus_di", 0)
        if adx > 25:
            # 강한 추세: +DI/-DI 방향으로 시그널 강화
            di_bias = 20.0 if plus_di > minus_di else -20.0
            raw += di_bias * (adx - 25) / 25  # ADX 50에서 최대 ±20
        elif adx < 20:
            # 추세 부재: 모멘텀 시그널 약화 (0~30% 감쇠)
            dampen = 1.0 - (20 - adx) / 20 * 0.3
            raw *= dampen

    return _clamp(raw)


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


def _score_consensus(consensus: dict) -> float:
    """증권사 컨센서스 → -100~+100 점수.

    괴리율 기반 밸류에이션 + 투자의견 + 리포트 톤을 종합.
    """
    scores: list[float] = []

    # 밸류에이션 (괴리율 기반)
    valuation = consensus.get("valuation")
    if valuation == "저평가":
        scores.append(60.0)
    elif valuation == "적정하단":
        scores.append(30.0)
    elif valuation == "적정":
        scores.append(0.0)
    elif valuation == "고평가":
        scores.append(-60.0)

    # 투자의견
    rec_label = consensus.get("recommendation_label")
    if rec_label == "매수":
        scores.append(60.0)
    elif rec_label == "매수유지":
        scores.append(30.0)
    elif rec_label == "중립":
        scores.append(0.0)
    elif rec_label == "매도":
        scores.append(-60.0)

    # 리포트 톤
    tone = consensus.get("research_tone")
    if tone == "긍정":
        scores.append(30.0)
    elif tone == "부정":
        scores.append(-30.0)

    if not scores:
        return 0.0
    return _clamp(sum(scores) / len(scores))


def _score_volatility(vol: dict) -> float:
    """변동성 분석 → -100~+100 점수.

    고변동성=-30, 저변동성=+20, 보통=0.
    밴드폭 수축 시 +15 가산.
    """
    regime = vol.get("volatility_regime")
    squeeze = vol.get("bandwidth_squeeze", False)

    base = {"고변동성": -30, "저변동성": 20, "보통": 0}.get(regime, 0)

    if squeeze:
        base += 15

    return _clamp(float(base))


def _score_candlestick(candle: dict) -> float:
    """캔들스틱 패턴 분석 → -100~+100 점수.

    detect_candlestick_patterns() 결과의 score를 그대로 사용.
    """
    return _clamp(float(candle.get("score", 0)))


def _score_semiconductor(momentum: int) -> float:
    """반도체 모멘텀 스코어 → -100~+100 점수.

    compute_semiconductor_momentum() 결과(-100~+100)를 그대로 시그널 점수로 사용.
    """
    return _clamp(float(momentum))


def _score_news_sentiment(news: dict) -> float:
    """뉴스 감정 요약 → -100~+100 점수.

    bullish/bearish/neutral 라벨 + score 강도로 산출.
    score = positive - negative 건수.
    """
    label = news.get("label", "neutral")
    raw_score = news.get("score", 0)
    count = news.get("count", 0)

    if count == 0:
        return 0.0

    # 라벨 기반 base
    base = {"bullish": 40, "bearish": -40, "neutral": 0}.get(label, 0)

    # score 강도 반영: (positive - negative) / count * 60
    ratio = raw_score / count if count > 0 else 0
    intensity = _clamp(ratio * 60, -60, 60)

    return _clamp(base + intensity)


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


def _apply_timeframe_filter(score: float, alignment: dict) -> float:
    """멀티타임프레임 정합성에 따라 종합 점수를 필터/증폭한다.

    별도 축이 아닌 기존 시그널의 필터/증폭기로 작동:
    - aligned_bullish/divergent_bullish → +15% 증폭
    - aligned_bearish/divergent_bearish → -15% 감쇠
    - neutral → 변동 없음
    """
    label = alignment.get("alignment", "neutral")
    if label in ("aligned_bullish", "divergent_bullish"):
        return score * 1.15
    if label in ("aligned_bearish", "divergent_bearish"):
        return score * 0.85
    return score


def compute_composite_signal(
    technical: dict,
    supply_demand: dict,
    exchange_rate: dict,
    relative_strength: dict | None = None,
    trend_reversal: dict | None = None,
    fundamentals: dict | None = None,
    news_sentiment: dict | None = None,
    consensus: dict | None = None,
    semiconductor_momentum: int | None = None,
    volatility: dict | None = None,
    candlestick: dict | None = None,
    global_macro_score: int | None = None,
    accuracy_summary: dict | None = None,
    timeframe_alignment: dict | None = None,
    market_regime: dict | None = None,
) -> dict:
    """종합 투자 시그널을 계산한다.

    Args:
        technical: compute_technical_indicators() 결과
        supply_demand: analyze_supply_demand() 결과
        exchange_rate: analyze_exchange_rate() 결과
        relative_strength: compute_relative_strength() 결과 (선택)
        trend_reversal: detect_reversal_signals() 결과 (선택)
        fundamentals: analyze_fundamentals() 결과 (선택)
        news_sentiment: summarize_sentiment() 결과 (선택)
        consensus: analyze_consensus() 결과 (선택)
        semiconductor_momentum: compute_semiconductor_momentum() 결과 (선택)
        volatility: compute_volatility() 결과 (선택)
        candlestick: detect_candlestick_patterns() 결과 (선택)

    Returns:
        dict with:
            score: -100~+100 종합 점수
            grade: 5단계 판정 문자열
            technical_score: 기술적 축 점수 (-100~+100)
            supply_score: 수급 축 점수 (-100~+100)
            exchange_score: 환율 축 점수 (-100~+100)
            rs_score: 상대강도 축 점수 (-100~+100) (선택)
            fundamentals_score: 펀더멘털 축 점수 (-100~+100) (선택)
            news_score: 뉴스 감정 축 점수 (-100~+100) (선택)
            consensus_score: 컨센서스 축 점수 (-100~+100) (선택)
            semiconductor_score: 반도체 업황 축 점수 (-100~+100) (선택)
            weights: 각 축 가중치 (%)
    """
    tech_score = _score_technical(technical, market_regime=market_regime)
    sup_score = _score_supply(supply_demand)
    fx_score = _score_exchange(exchange_rate)

    has_rs = relative_strength is not None
    has_fund = fundamentals is not None
    has_news = news_sentiment is not None
    has_cons = consensus is not None
    has_semi = semiconductor_momentum is not None
    has_vol = volatility is not None
    has_candle = candlestick is not None
    has_macro = global_macro_score is not None

    rs_score = _score_relative_strength(relative_strength) if has_rs else None
    fund_score = _score_fundamentals(fundamentals) if has_fund else None
    news_score = _score_news_sentiment(news_sentiment) if has_news else None
    cons_score = _score_consensus(consensus) if has_cons else None
    semi_score = _score_semiconductor(semiconductor_momentum) if has_semi else None
    vol_score = _score_volatility(volatility) if has_vol else None
    candle_score = _score_candlestick(candlestick) if has_candle else None

    # --- 동적 가중치 산출 ---
    # 기본 optional 축(RS, Fund, News) 조합에 따라 base_weights를 정한 뒤,
    # consensus가 있으면 10%를 할당하고 기존 축을 비례 축소.

    if has_rs and has_fund and has_news:
        base_weights = {"technical": 25, "supply": 25, "exchange": 15,
                        "relative_strength": 10, "fundamentals": 15, "news": 10}
    elif has_rs and has_fund:
        base_weights = {"technical": 30, "supply": 30, "exchange": 15,
                        "relative_strength": 10, "fundamentals": 15}
    elif has_rs and has_news:
        base_weights = {"technical": 30, "supply": 30, "exchange": 15,
                        "relative_strength": 15, "news": 10}
    elif has_fund and has_news:
        base_weights = {"technical": 30, "supply": 25, "exchange": 15,
                        "fundamentals": 20, "news": 10}
    elif has_rs:
        base_weights = {"technical": 35, "supply": 35, "exchange": 15,
                        "relative_strength": 15}
    elif has_fund:
        base_weights = {"technical": 35, "supply": 30, "exchange": 15,
                        "fundamentals": 20}
    elif has_news:
        base_weights = {"technical": 35, "supply": 35, "exchange": 15,
                        "news": 15}
    else:
        base_weights = {"technical": 40, "supply": 40, "exchange": 20}

    # consensus, semiconductor 각 10%, volatility 5%를 기존 축에서 비례 축소하여 확보
    extra_axes: dict[str, int] = {}
    if has_cons:
        extra_axes["consensus"] = 10
    if has_semi:
        extra_axes["semiconductor"] = 10
    if has_vol:
        extra_axes["volatility"] = 5
    if has_candle:
        extra_axes["candlestick"] = 5
    if has_macro:
        extra_axes["global_macro"] = 10

    if extra_axes:
        extra_total = sum(extra_axes.values())
        remaining = 100 - extra_total
        weights = {k: round(v * remaining / 100) for k, v in base_weights.items()}
        weights.update(extra_axes)
        # 반올림 오차 보정: 가장 큰 축에 보정
        diff = 100 - sum(weights.values())
        if diff != 0:
            largest_key = max(base_weights, key=base_weights.get)
            weights[largest_key] += diff
    else:
        weights = dict(base_weights)

    # --- 적응형 가중치 조정 ---
    adapted = False
    if accuracy_summary is not None:
        adapted_weights = adapt_weights(weights, accuracy_summary)
        if adapted_weights != weights:
            adapted = True
            weights = adapted_weights

    # --- 가중 합산 ---
    score_map: dict[str, float] = {
        "technical": tech_score,
        "supply": sup_score,
        "exchange": fx_score,
    }
    if has_rs:
        score_map["relative_strength"] = rs_score
    if has_fund:
        score_map["fundamentals"] = fund_score
    if has_news:
        score_map["news"] = news_score
    if has_cons:
        score_map["consensus"] = cons_score
    if has_semi:
        score_map["semiconductor"] = semi_score
    if has_vol:
        score_map["volatility"] = vol_score
    if has_candle:
        score_map["candlestick"] = candle_score
    if has_macro:
        score_map["global_macro"] = _clamp(float(global_macro_score))

    composite = sum(score_map[k] * weights[k] / 100 for k in score_map)

    # 추세 전환 컨버전스 보너스/페널티
    if trend_reversal is not None:
        composite += _reversal_bonus(trend_reversal)

    # 멀티타임프레임 정합성: 기존 시그널의 필터/증폭기
    if timeframe_alignment is not None:
        composite = _apply_timeframe_filter(composite, timeframe_alignment)

    composite = _clamp(composite)

    result = {
        "score": composite,
        "grade": _grade_from_score(composite),
        "technical_score": tech_score,
        "supply_score": sup_score,
        "exchange_score": fx_score,
        "weights": weights,
    }
    if adapted:
        result["adapted_weights"] = True
    if rs_score is not None:
        result["rs_score"] = rs_score
    if fund_score is not None:
        result["fundamentals_score"] = fund_score
    if news_score is not None:
        result["news_score"] = news_score
    if cons_score is not None:
        result["consensus_score"] = cons_score
    if semi_score is not None:
        result["semiconductor_score"] = semi_score
    if vol_score is not None:
        result["volatility_score"] = vol_score
    if candle_score is not None:
        result["candlestick_score"] = candle_score
    if has_macro:
        result["global_macro_score"] = _clamp(float(global_macro_score))
    if market_regime is not None:
        result["market_regime"] = market_regime
    return result


def adjust_for_convergence(sig: dict, convergence: dict) -> dict:
    """수렴 분석 결과에 따라 종합 시그널 점수를 조절한다.

    Args:
        sig: compute_composite_signal() 반환값.
        convergence: analyze_convergence() 반환값.

    Returns:
        sig 복사본에 수렴 조정이 반영된 dict.
            - strong: 점수 ±10% 강화 (방향 유지)
            - mixed: 점수 −10% 감쇠 (0 방향으로)
            - moderate/weak: 조정 없음
    """
    level = convergence.get("convergence_level", "mixed")
    score = sig["score"]

    if level == "strong":
        score *= 1.10
    elif level == "mixed":
        score *= 0.90

    score = _clamp(score)

    result = dict(sig)
    result["score"] = score
    result["grade"] = _grade_from_score(score)
    result["convergence"] = convergence
    return result
