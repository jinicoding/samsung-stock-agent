"""규칙 기반 자연어 마켓 코멘터리 생성기.

분석 결과를 조합하여 2~3문장의 한국어 자연어 해석을 생성한다.
LLM 호출 없이 규칙 기반 템플릿으로 구현하여 안정성 확보.
"""

from src.analysis.report import (
    classify_ma_alignment,
    classify_rsi,
    classify_macd,
    classify_bb_position,
)


def generate_commentary(
    indicators: dict,
    supply_demand: dict | None = None,
    exchange_rate: dict | None = None,
    composite_signal: dict | None = None,
    support_resistance: dict | None = None,
    relative_strength: dict | None = None,
    trend_reversal: dict | None = None,
    signal_trend: dict | None = None,
    fundamentals: dict | None = None,
    news_sentiment: dict | None = None,
    consensus: dict | None = None,
    weekly_summary: dict | None = None,
    rel_perf: dict | None = None,
    sox_trend: dict | None = None,
    semiconductor_momentum: int | None = None,
    volatility: dict | None = None,
    candlestick: dict | None = None,
    convergence: dict | None = None,
    nasdaq_trend: dict | None = None,
    vix_risk: dict | None = None,
    timeframe_alignment: dict | None = None,
    weekly_indicators: dict | None = None,
    scenario: dict | None = None,
    pattern_match: dict | None = None,
    daily_delta: dict | None = None,
    risk_management: dict | None = None,
    market_regime: dict | None = None,
    fibonacci: dict | None = None,
    backtest: dict | None = None,
    volume_profile: dict | None = None,
) -> str:
    """분석 결과를 2~3문장 자연어 코멘터리로 변환한다.

    Args:
        indicators: compute_technical_indicators() 반환값.
        supply_demand: analyze_supply_demand() 반환값 (선택).
        exchange_rate: analyze_exchange_rate() 반환값 (선택).
        composite_signal: compute_composite_signal() 반환값 (선택).
        support_resistance: analyze_support_resistance() 반환값 (선택).
        trend_reversal: detect_reversal_signals() 반환값 (선택).

    Returns:
        2~3문장의 한국어 자연어 코멘터리.
    """
    sd = supply_demand or {}
    er = exchange_rate or {}
    sig = composite_signal or {}
    sr = support_resistance or {}

    sentences: list[str] = []

    # --- 1) 주요 흐름 문장: 수급 + 기술적 시그널 조합 ---
    sentences.append(_build_flow_sentence(indicators, sd, sig))

    # --- 1.1) 시장 체제 프레이밍 ---
    regime_sentence = _build_regime_framing(market_regime or {})
    if regime_sentence:
        sentences.append(regime_sentence)

    # --- 1.5) OBV 다이버전스 문장 ---
    obv_sentence = _build_obv_divergence_sentence(indicators)
    if obv_sentence:
        sentences.append(obv_sentence)

    # --- 1.6) ADX 추세 강도 문장 ---
    adx_sentence = _build_adx_sentence(indicators)
    if adx_sentence:
        sentences.append(adx_sentence)

    # --- 1.7) 추세 전환 감지 문장 ---
    reversal_sentence = _build_reversal_sentence(trend_reversal or {})
    if reversal_sentence:
        sentences.append(reversal_sentence)

    # --- 1.8) 멀티타임프레임 정합성 문장 ---
    tf_sentence = _build_timeframe_sentence(timeframe_alignment or {}, weekly_indicators or {})
    if tf_sentence:
        sentences.append(tf_sentence)

    # --- 1.9) 피보나치 되돌림 문장 ---
    fib_sentence = _build_fibonacci_sentence(fibonacci or {}, indicators.get("current_price", 0))
    if fib_sentence:
        sentences.append(fib_sentence)

    # --- 1.95) Volume Profile 문장 ---
    vp_sentence = _build_volume_profile_sentence(volume_profile or {})
    if vp_sentence:
        sentences.append(vp_sentence)

    # --- 2) 보조 경고/참고 문장: RSI, 볼린저, 지지/저항 ---
    caution = _build_caution_sentence(indicators, sr)
    if caution:
        sentences.append(caution)

    # --- 3) 상대강도 문장 ---
    rs_sentence = _build_rs_sentence(relative_strength or {})
    if rs_sentence:
        sentences.append(rs_sentence)

    # --- 4) 환율 영향 문장 ---
    fx_sentence = _build_fx_sentence(er)
    if fx_sentence:
        sentences.append(fx_sentence)

    # --- 4.5) 펀더멘털 문장 ---
    fund_sentence = _build_fundamentals_sentence(fundamentals or {})
    if fund_sentence:
        sentences.append(fund_sentence)

    # --- 4.7) 뉴스 심리 문장 ---
    news_sentence = _build_news_sentence(news_sentiment or {})
    if news_sentence:
        sentences.append(news_sentence)

    # --- 4.8) 컨센서스 문장 ---
    cons_sentence = _build_consensus_sentence(consensus or {})
    if cons_sentence:
        sentences.append(cons_sentence)

    # --- 4.93) 캔들스틱 패턴 문장 ---
    candle_sentence = _build_candlestick_sentence(candlestick or {})
    if candle_sentence:
        sentences.append(candle_sentence)

    # --- 4.95) 변동성 분석 문장 ---
    vol_sentence = _build_volatility_sentence(volatility or {})
    if vol_sentence:
        sentences.append(vol_sentence)

    # --- 4.9) 반도체 업황 문장 ---
    semi_sentence = _build_semiconductor_sentence(
        rel_perf or {}, sox_trend or {}, semiconductor_momentum,
    )
    if semi_sentence:
        sentences.append(semi_sentence)

    # --- 4.96) 수렴 분석 문장 ---
    conv_sentence = _build_convergence_sentence(convergence or {})
    if conv_sentence:
        sentences.append(conv_sentence)

    # --- 4.97) 글로벌 매크로 문장 ---
    macro_sentence = _build_global_macro_sentence(nasdaq_trend or {}, vix_risk or {})
    if macro_sentence:
        sentences.append(macro_sentence)

    # --- 4.98) 시나리오 분석 문장 ---
    scenario_sentence = _build_scenario_sentence(scenario or {})
    if scenario_sentence:
        sentences.append(scenario_sentence)

    # --- 4.99) 유사 패턴 분석 문장 ---
    pattern_sentence = _build_pattern_match_sentence(pattern_match or {})
    if pattern_sentence:
        sentences.append(pattern_sentence)

    # --- 4.995) 일일 델타 문장 ---
    delta_sentence = _build_delta_sentence(daily_delta or {})
    if delta_sentence:
        sentences.append(delta_sentence)

    # --- 4.997) 리스크 관리 문장 ---
    risk_sentence = _build_risk_management_sentence(risk_management or {})
    if risk_sentence:
        sentences.append(risk_sentence)

    # --- 4.998) 백테스팅 성과 문장 ---
    bt_sentence = _build_backtest_sentence(backtest or {}, sig)
    if bt_sentence:
        sentences.append(bt_sentence)

    # --- 5) 시그널 추이 문장 ---
    trend_sentence = _build_signal_trend_sentence(signal_trend or {})
    if trend_sentence:
        sentences.append(trend_sentence)

    # --- 6) 주간 추이 요약 문장 ---
    weekly_sentence = _build_weekly_sentence(weekly_summary or {})
    if weekly_sentence:
        sentences.append(weekly_sentence)

    return " ".join(sentences)


_REGIME_FRAMING = {
    "trending_up": "상승 추세장",
    "trending_down": "하락 추세장",
    "range_bound": "횡보 국면",
    "breakout": "상방 돌파 국면",
    "breakdown": "하방 붕괴 국면",
}


def _build_regime_framing(regime: dict) -> str:
    """시장 체제를 코멘터리 프레이밍 문장으로 변환한다."""
    r = regime.get("regime")
    if not r:
        return ""
    label = _REGIME_FRAMING.get(r, r)
    confidence = regime.get("confidence", 0)
    duration = regime.get("duration", 0)
    if duration > 1:
        base = f"{label}(확신도 {confidence}%)이 {duration}일째 지속되는 가운데,"
    else:
        base = f"{label}(확신도 {confidence}%) 진입 초기 국면에서,"

    # RSI 기준이 기본값(70/30)과 다르면 조정 이유 설명
    hints = regime.get("interpretation_hints", {})
    rsi_th = hints.get("rsi_thresholds", {})
    ob = rsi_th.get("overbought", 70)
    os_ = rsi_th.get("oversold", 30)
    if ob != 70 or os_ != 30:
        base += f" RSI 기준이 {ob}/{os_}로 조정되어 기술적 점수에 반영됨."

    return base


def _build_flow_sentence(indicators: dict, sd: dict, sig: dict) -> str:
    """주요 흐름을 설명하는 핵심 문장."""
    parts: list[str] = []

    # 수급 흐름
    supply_part = _describe_supply(sd)
    if supply_part:
        parts.append(supply_part)

    # 기술적 시그널
    tech_part = _describe_technical(indicators)
    if tech_part:
        parts.append(tech_part)

    # 이평선 배열
    ma_part = _describe_ma_alignment(indicators)
    if ma_part:
        parts.append(ma_part)

    # 조합
    if not parts:
        grade = sig.get("grade", "중립")
        return f"현재 시장은 {grade} 흐름을 보이고 있습니다."

    # 종합 판정 기반 결론
    grade = sig.get("grade", "중립")
    score = sig.get("score", 0)

    connector = _join_parts(parts)

    if grade in ("강력매수신호", "매수우세"):
        if score >= 60:
            return f"{connector} 강한 매수 우세 흐름입니다."
        return f"{connector} 매수 우세 흐름입니다."
    elif grade in ("강력매도신호", "매도우세"):
        if score <= -60:
            return f"{connector} 강한 매도 압력이 관찰됩니다."
        return f"{connector} 매도 우세 흐름입니다."
    else:
        return f"{connector} 관망세가 이어지고 있습니다."


def _describe_supply(sd: dict) -> str:
    """수급 동향을 자연어로."""
    if not sd:
        return ""

    fb = sd.get("foreign_consecutive_net_buy", 0)
    fs = sd.get("foreign_consecutive_net_sell", 0)
    ib = sd.get("institution_consecutive_net_buy", 0)
    is_ = sd.get("institution_consecutive_net_sell", 0)

    parts = []
    if fb >= 3:
        parts.append(f"외국인 {fb}일 연속 순매수")
    elif fs >= 3:
        parts.append(f"외국인 {fs}일 연속 순매도")

    if ib >= 3:
        parts.append(f"기관 {ib}일 연속 순매수")
    elif is_ >= 3:
        parts.append(f"기관 {is_}일 연속 순매도")

    if not parts:
        judgment = sd.get("overall_judgment", "neutral")
        if judgment == "buy_dominant":
            return "수급이 매수 우위로"
        elif judgment == "sell_dominant":
            return "수급이 매도 우위로"
        return ""

    return "와(과) ".join(parts[:2]) + "가 이어지면서"


def _describe_technical(indicators: dict) -> str:
    """기술적 시그널을 자연어로."""
    macd_hist = indicators.get("macd_histogram")
    macd = indicators.get("macd")
    macd_sig = indicators.get("macd_signal")
    macd_cross = classify_macd(macd, macd_sig, macd_hist)

    parts = []
    if macd_cross == "골든크로스":
        parts.append("MACD 골든크로스")
    elif macd_cross == "데드크로스":
        parts.append("MACD 데드크로스")

    return "가 ".join(parts[:1]) if parts else ""


def _describe_ma_alignment(indicators: dict) -> str:
    """이평선 배열을 자연어로."""
    alignment = classify_ma_alignment(indicators)
    if alignment == "정배열":
        return "이동평균선 정배열 구간에서"
    elif alignment == "역배열":
        return "이동평균선 역배열 구간에서"
    return ""


def _build_caution_sentence(indicators: dict, sr: dict) -> str:
    """보조 경고/참고 문장."""
    warnings: list[str] = []

    # RSI 경고
    rsi = indicators.get("rsi_14")
    rsi_status = classify_rsi(rsi)
    if rsi_status == "과매수" and rsi is not None:
        warnings.append(f"RSI {rsi:.0f}으로 과매수 영역에 접근 중이므로 단기 조정 가능성에 유의하세요")
    elif rsi_status == "과매도" and rsi is not None:
        warnings.append(f"RSI {rsi:.0f}으로 과매도 영역이므로 반등 가능성을 주시하세요")

    # 스토캐스틱 과매수/과매도
    stoch_k = indicators.get("stoch_k")
    if stoch_k is not None:
        if stoch_k >= 80:
            warnings.append(f"스토캐스틱 %K {stoch_k:.0f}으로 과매수 영역이므로 단기 되돌림에 유의하세요")
        elif stoch_k <= 20:
            warnings.append(f"스토캐스틱 %K {stoch_k:.0f}으로 과매도 영역이므로 반등 가능성을 주시하세요")

    # 볼린저 밴드
    bb_pctb = indicators.get("bb_pctb")
    bb_pos = classify_bb_position(bb_pctb)
    if bb_pos == "상단 돌파":
        warnings.append("볼린저 밴드 상단 돌파로 과열 신호가 감지됩니다")
    elif bb_pos == "하단 이탈":
        warnings.append("볼린저 밴드 하단 이탈로 반등 구간 진입 가능성이 있습니다")

    # 지지/저항선 근접
    if sr:
        price = indicators.get("current_price", 0)
        sr_warning = _check_support_resistance(price, sr)
        if sr_warning:
            warnings.append(sr_warning)

    if not warnings:
        return ""

    # 최대 2개 경고만
    return "다만 " + ", ".join(warnings[:2]) + "."


def _check_support_resistance(price: float, sr: dict) -> str:
    """지지/저항선 근접 여부를 확인."""
    ns = sr.get("nearest_support")
    nr = sr.get("nearest_resistance")

    if price and ns and price > 0:
        dist_pct = (price - ns) / price * 100
        if dist_pct < 2.0:
            return f"지지선({int(ns):,}원)에 근접해 있어 이탈 시 추가 하락에 유의하세요"

    if price and nr and price > 0:
        dist_pct = (nr - price) / price * 100
        if dist_pct < 2.0:
            return f"저항선({int(nr):,}원)에 근접해 있어 돌파 여부가 관건입니다"

    return ""


def _build_obv_divergence_sentence(indicators: dict) -> str:
    """OBV 다이버전스 관련 자연어 문장."""
    obv_div = indicators.get("obv_divergence")
    if obv_div == "bearish":
        return "가격 상승에도 거래량이 뒷받침되지 않는 OBV 괴리가 감지되어 추세 지속에 주의가 필요합니다."
    if obv_div == "bullish":
        return "가격은 하락세이나 거래량 흐름이 선행 반등 신호를 보이고 있어 OBV 다이버전스에 주목할 필요가 있습니다."
    return ""


def _build_rs_sentence(rs: dict) -> str:
    """상대강도 관련 자연어 문장."""
    if not rs:
        return ""

    trend = rs.get("rs_trend")
    alpha_5d = rs.get("alpha_5d")

    if trend == "outperform":
        if alpha_5d is not None and alpha_5d > 2:
            return f"KOSPI 대비 5일 초과수익률 {alpha_5d:+.1f}%로 시장을 크게 상회하고 있어 개별 종목 모멘텀이 강합니다."
        return "삼성전자가 KOSPI 대비 상대적으로 강한 흐름을 보이고 있습니다."
    elif trend == "underperform":
        if alpha_5d is not None and alpha_5d < -2:
            return f"KOSPI 대비 5일 초과수익률 {alpha_5d:+.1f}%로 시장 대비 부진한 흐름이 이어지고 있습니다."
        return "삼성전자가 시장 대비 소폭 약세를 보이고 있습니다."

    return ""


def _build_reversal_sentence(tr: dict) -> str:
    """추세 전환 컨버전스 감지 시 자연어 경고 문장."""
    if not tr:
        return ""

    convergence = tr.get("convergence", "none")
    direction = tr.get("direction", "neutral")

    if convergence not in ("strong", "moderate"):
        return ""

    dir_kr = "강세" if direction == "bullish" else "약세"
    active = tr.get("active_categories", 0)

    if convergence == "strong":
        return f"다수의 기술적 지표({active}개 카테고리)가 동시에 {dir_kr} 반전 신호를 보이고 있어 추세 전환 가능성에 주목할 필요가 있습니다."
    else:  # moderate
        return f"{active}개 카테고리에서 {dir_kr} 반전 신호가 감지되어 추세 전환 여부를 주시할 필요가 있습니다."


def _build_fx_sentence(er: dict) -> str:
    """환율 영향 문장."""
    if not er:
        return ""

    trend = er.get("trend")
    if trend == "원화약세":
        return "원화약세 흐름이 수출 비중이 높은 삼성전자에 우호적 환경을 조성하고 있습니다."
    elif trend == "원화강세":
        return "원화강세 흐름이 수출 실적에 부담 요인으로 작용할 수 있습니다."
    return ""


def _build_fundamentals_sentence(fund: dict) -> str:
    """펀더멘털 분석 기반 자연어 문장."""
    if not fund:
        return ""

    per_val = fund.get("per_valuation")
    pbr_val = fund.get("pbr_valuation")
    div_attr = fund.get("dividend_attractiveness")
    outlook = fund.get("earnings_outlook")

    parts: list[str] = []

    # PER/PBR 저평가 또는 고평가 언급
    undervalued = (per_val == "저평가") or (pbr_val == "저평가")
    overvalued = (per_val == "고평가") or (pbr_val == "고평가")

    if undervalued and not overvalued:
        metrics = []
        if per_val == "저평가":
            per = fund.get("per")
            metrics.append(f"PER {per:.1f}배" if per is not None else "PER")
        if pbr_val == "저평가":
            pbr = fund.get("pbr")
            metrics.append(f"PBR {pbr:.2f}배" if pbr is not None else "PBR")
        parts.append(f"{'·'.join(metrics)} 기준 저평가 영역에 위치해 있습니다")
    elif overvalued and not undervalued:
        metrics = []
        if per_val == "고평가":
            per = fund.get("per")
            metrics.append(f"PER {per:.1f}배" if per is not None else "PER")
        if pbr_val == "고평가":
            pbr = fund.get("pbr")
            metrics.append(f"PBR {pbr:.2f}배" if pbr is not None else "PBR")
        parts.append(f"{'·'.join(metrics)} 기준 고평가 영역으로 밸류에이션 부담이 있습니다")

    # 배당 매력
    if div_attr == "매력적":
        div_yield = fund.get("dividend_yield")
        if div_yield is not None:
            parts.append(f"배당수익률 {div_yield:.1f}%로 배당 매력이 높습니다")

    # 실적 전망
    if outlook == "개선":
        parts.append("컨센서스 기준 실적 개선이 기대됩니다")
    elif outlook == "악화":
        parts.append("컨센서스 기준 실적 둔화가 우려됩니다")

    if not parts:
        return ""

    return parts[0] + "."


def _build_news_sentence(news: dict) -> str:
    """뉴스 감정 분석 기반 자연어 문장."""
    if not news:
        return ""

    label = news.get("label", "neutral")
    pos = news.get("positive", 0)
    neg = news.get("negative", 0)

    if label == "bullish":
        return f"뉴스 심리가 긍정적(긍정 {pos}건 vs 부정 {neg}건)으로 시장 분위기가 우호적입니다."
    elif label == "bearish":
        return f"뉴스 심리가 부정적(부정 {neg}건 vs 긍정 {pos}건)으로 투자 심리 위축에 유의할 필요가 있습니다."

    return ""


def _build_signal_trend_sentence(st: dict) -> str:
    """시그널 추이 기반 자연어 문장."""
    if not st:
        return ""

    direction = st.get("direction", "횡보")
    consec = st.get("consecutive_same_grade", 0)
    latest_grade = st.get("latest_grade", "")
    score_change = st.get("score_change", 0)

    parts = []

    # 연속 동일 등급 3일 이상
    if consec >= 3:
        parts.append(f"시그널이 {consec}일 연속 {latest_grade}을 유지하고 있습니다")

    # 추세 방향
    if direction == "개선" and score_change > 15:
        parts.append(f"최근 시그널이 {score_change:+.0f}p 개선되며 긍정적 흐름이 강화되고 있습니다")
    elif direction == "개선":
        parts.append("시그널이 점진적으로 개선되는 추세입니다")
    elif direction == "악화" and score_change < -15:
        parts.append(f"최근 시그널이 {score_change:+.0f}p 하락하며 약세 신호가 확대되고 있습니다")
    elif direction == "악화":
        parts.append("시그널이 소폭 약화되는 추세입니다")

    if not parts:
        return ""

    return parts[0] + "."


def _build_consensus_sentence(cons: dict) -> str:
    """증권사 컨센서스 기반 자연어 문장."""
    if not cons:
        return ""

    valuation = cons.get("valuation")
    divergence = cons.get("divergence_pct")
    rec_label = cons.get("recommendation_label")

    if valuation == "저평가" and divergence is not None:
        return f"증권사 컨센서스 목표가 대비 {divergence:.0f}% 괴리로 저평가 구간에 위치하며, 투자의견은 {rec_label}입니다."
    elif valuation == "고평가" and divergence is not None:
        return f"증권사 컨센서스 목표가 대비 {divergence:.0f}% 괴리로 고평가 영역이며, 투자의견은 {rec_label}입니다."
    elif valuation == "적정하단" and divergence is not None:
        return f"증권사 목표가 대비 {divergence:.0f}% 괴리로 적정가 하단에 위치하며, 투자의견은 {rec_label}입니다."

    return ""


def _build_weekly_sentence(ws: dict) -> str:
    """주간 추이 요약을 자연어 문장으로."""
    if not ws:
        return ""

    judgment = ws.get("judgment", "")
    change_pct = ws.get("change_pct", 0)
    days = ws.get("days", 0)

    if not judgment or days < 2:
        return ""

    sign = "+" if change_pct > 0 else ""

    if judgment == "횡보":
        return f"이번 주 {days}거래일간 {sign}{change_pct:.1f}% 변동으로 횡보 흐름을 보였습니다."
    elif "전환" in judgment:
        return f"이번 주 {days}거래일간 {sign}{change_pct:.1f}% 변동과 함께 {judgment} 흐름이 나타나 추세 변화에 주목할 필요가 있습니다."
    elif "상승" in judgment:
        return f"이번 주 {days}거래일간 {sign}{change_pct:.1f}% 상승하며 주간 상승 흐름이 이어지고 있습니다."
    elif "하락" in judgment:
        return f"이번 주 {days}거래일간 {sign}{change_pct:.1f}% 하락하며 주간 약세 흐름이 지속되고 있습니다."

    return ""


def _build_semiconductor_sentence(
    rel_perf: dict, sox_trend: dict, momentum: int | None,
) -> str:
    """반도체 업황에 따른 자연어 코멘트."""
    if momentum is None:
        return ""
    if not rel_perf or not sox_trend:
        return ""

    trend = rel_perf.get("relative_trend", "neutral")
    sox_label = sox_trend.get("trend", "횡보")
    alpha_5d = rel_perf.get("alpha_5d")

    # 강한 호조
    if momentum >= 30:
        parts = ["반도체 업황이 호조세로"]
        details = []
        if sox_label == "상승":
            details.append("SOX 지수 상승")
        if trend == "outperform" and alpha_5d is not None:
            details.append(f"SK하이닉스 대비 초과수익({alpha_5d:+.1f}%)")
        elif trend == "outperform":
            details.append("SK하이닉스 대비 초과수익")
        if details:
            parts.append(", ".join(details) + "이 긍정적입니다.")
        else:
            parts.append("긍정적인 흐름입니다.")
        return " ".join(parts)

    # 강한 부진
    if momentum <= -30:
        parts = ["반도체 업황이 부진한 가운데"]
        details = []
        if sox_label == "하락":
            details.append("SOX 지수 하락")
        if trend == "underperform" and alpha_5d is not None:
            details.append(f"SK하이닉스 대비 부진({alpha_5d:+.1f}%)")
        elif trend == "underperform":
            details.append("SK하이닉스 대비 부진")
        if details:
            parts.append(", ".join(details) + "이 부담 요인입니다.")
        else:
            parts.append("업황 개선 여부를 주시할 필요가 있습니다.")
        return " ".join(parts)

    # 중립 범위는 문장 생략
    return ""


def _build_candlestick_sentence(candle: dict) -> str:
    """캔들스틱 패턴 기반 자연어 문장."""
    if not candle:
        return ""

    patterns = candle.get("patterns", [])
    if not patterns:
        return ""

    signal = candle.get("signal", "neutral")
    score = candle.get("score", 0)

    pattern_names = {
        "doji": "도지", "hammer": "해머", "hanging_man": "행잉맨",
        "bullish_marubozu": "강세 마루보즈", "bearish_marubozu": "약세 마루보즈",
        "bullish_engulfing": "강세 인걸핑", "bearish_engulfing": "약세 인걸핑",
        "morning_star": "모닝스타", "evening_star": "이브닝스타",
    }

    names = [pattern_names.get(p["name"], p["name"]) for p in patterns]
    joined = "·".join(names)

    if signal == "bullish" and score >= 50:
        return f"캔들스틱에서 {joined} 패턴이 감지되어 강한 강세 반전 신호를 보이고 있습니다."
    elif signal == "bullish":
        return f"캔들스틱에서 {joined} 패턴이 나타나 강세 전환 가능성에 주목할 필요가 있습니다."
    elif signal == "bearish" and score <= -50:
        return f"캔들스틱에서 {joined} 패턴이 감지되어 강한 약세 전환 신호에 유의할 필요가 있습니다."
    elif signal == "bearish":
        return f"캔들스틱에서 {joined} 패턴이 나타나 약세 전환 가능성을 주시할 필요가 있습니다."

    # neutral — 도지 등 방향성 불확실 패턴
    return f"캔들스틱에서 {joined} 패턴이 나타나 방향성 모색 구간으로 판단됩니다."


def _build_volatility_sentence(vol: dict) -> str:
    """변동성 분석 기반 자연어 문장."""
    if not vol:
        return ""

    regime = vol.get("volatility_regime")
    squeeze = vol.get("bandwidth_squeeze", False)

    if regime == "고변동성":
        atr_pct = vol.get("atr_pct")
        if atr_pct is not None:
            return f"현재 변동성이 높은 구간(ATR {atr_pct:.1f}%)으로 리스크 관리에 유의할 필요가 있습니다."
        return "현재 변동성이 높은 구간으로 리스크 관리에 유의할 필요가 있습니다."

    if regime == "저변동성" and squeeze:
        return "변동성이 낮고 볼린저 밴드폭이 수축되어 있어 조만간 방향성 돌파가 나올 수 있는 구간입니다."

    if squeeze:
        return "볼린저 밴드폭 수축이 감지되어 변동성 확대에 대비할 필요가 있습니다."

    return ""


def _build_convergence_sentence(conv: dict) -> str:
    """다축 수렴 분석 기반 자연어 문장."""
    if not conv:
        return ""

    level = conv.get("convergence_level")
    direction = conv.get("dominant_direction", "neutral")
    aligned = conv.get("aligned_axes", [])
    total_axes = len(aligned) + len(conv.get("conflicting_axes", [])) + len(conv.get("neutral_axes", []))
    conviction = conv.get("conviction", 0)

    if total_axes == 0:
        return ""

    dir_kr = {"bullish": "강세", "bearish": "약세", "neutral": "중립"}.get(direction, "중립")

    if level == "strong":
        return f"{total_axes}축 중 {len(aligned)}축이 {dir_kr}를 가리키며 강한 수렴 — 시그널 신뢰도 높음(확신도 {conviction}%)."
    elif level == "moderate":
        return f"{total_axes}축 중 {len(aligned)}축이 {dir_kr} 방향으로 보통 수렴을 보이고 있습니다(확신도 {conviction}%)."
    elif level == "mixed":
        return f"분석 축 간 방향이 분산되어 혼조 양상으로 시그널 신뢰도가 낮습니다(확신도 {conviction}%)."

    return ""


def _build_global_macro_sentence(nasdaq: dict, vix: dict) -> str:
    """글로벌 매크로(NASDAQ 추세 + VIX 리스크) 기반 자연어 문장."""
    if not nasdaq or not vix:
        return ""

    trend = nasdaq.get("trend")
    risk = vix.get("risk_level")

    if not trend or not risk:
        return ""

    # NASDAQ 상승 + VIX 안정 → 우호적
    if trend == "상승" and risk == "안정":
        return "글로벌 기술주 환경이 우호적으로 외국인 수급에 긍정적입니다."

    # NASDAQ 상승 + VIX 경계 → 우호적이나 경계
    if trend == "상승" and risk == "경계":
        return "글로벌 기술주가 상승세이나 VIX 경계 수준으로 변동성 확대에 유의할 필요가 있습니다."

    # NASDAQ 하락 + VIX 공포 → 리스크 확대
    if trend == "하락" and risk == "공포":
        return "글로벌 리스크 확대로 외국인 수급에 부담이 될 수 있습니다."

    # NASDAQ 하락 + VIX 경계 → 부정적
    if trend == "하락" and risk == "경계":
        return "글로벌 기술주 약세와 VIX 경계 수준이 외국인 투자심리에 부담 요인입니다."

    # NASDAQ 하락 + VIX 안정 → 경계
    if trend == "하락" and risk == "안정":
        return "글로벌 기술주 약세에도 VIX가 안정적이어서 영향은 제한적일 수 있습니다."

    # NASDAQ 상승 + VIX 공포 → 혼조
    if trend == "상승" and risk == "공포":
        return "글로벌 기술주가 반등 시도 중이나 VIX 공포 수준으로 변동성 리스크가 높습니다."

    # 보합/중립 → 생략
    return ""


def _build_adx_sentence(indicators: dict) -> str:
    """ADX 추세 강도 기반 자연어 문장."""
    adx = indicators.get("adx")
    if adx is None:
        return ""

    plus_di = indicators.get("plus_di", 0) or 0
    minus_di = indicators.get("minus_di", 0) or 0

    if adx > 25:
        direction = "상승" if plus_di > minus_di else "하락"
        if adx > 40:
            return f"ADX {adx:.0f}으로 매우 강한 {direction} 추세가 진행 중이며 추세 추종 전략이 유효한 구간입니다."
        return f"ADX {adx:.0f}으로 {direction} 추세가 뚜렷하게 형성되어 있습니다."
    elif adx < 20:
        return f"ADX {adx:.0f}으로 뚜렷한 추세가 부재하여 횡보 구간으로 판단되며 방향성 확인이 필요합니다."

    return ""


def _build_timeframe_sentence(alignment: dict, weekly_ind: dict) -> str:
    """멀티타임프레임 정합성 기반 자연어 문장."""
    if not alignment or not weekly_ind:
        return ""

    label = alignment.get("alignment", "neutral")
    trend = weekly_ind.get("weekly_trend")
    ma5w = weekly_ind.get("ma5w")
    ma13w = weekly_ind.get("ma13w")

    if trend is None or ma5w is None or ma13w is None:
        return ""

    trend_kr = {"up": "상승", "down": "하락", "sideways": "횡보"}.get(trend, "횡보")
    ma_order = "정배열" if ma5w > ma13w else "역배열" if ma5w < ma13w else "수렴"

    if label == "aligned_bullish":
        return f"주봉 {trend_kr} 추세(MA5w/MA13w {ma_order})에서 일봉 과매도로 추세 방향 매수 기회가 포착됩니다."
    if label == "aligned_bearish":
        return f"주봉 {trend_kr} 추세(MA5w/MA13w {ma_order})에서 일봉 과매수로 추가 하락에 경계가 필요합니다."
    if label == "divergent_bullish":
        return f"주봉 {trend_kr} 추세(MA5w/MA13w {ma_order})가 유지되어 단기 조정 시 지지가 기대됩니다."
    if label == "divergent_bearish":
        return f"주봉 {trend_kr} 추세(MA5w/MA13w {ma_order})가 지속되어 반등 시에도 저항이 예상됩니다."

    return ""


def _build_scenario_sentence(scenario: dict) -> str:
    """시나리오 분석 기반 자연어 문장."""
    if not scenario:
        return ""
    dominant = scenario.get("dominant_scenario")
    comment = scenario.get("risk_reward_comment", "")
    if not dominant:
        return ""
    label_map = {"상승": "상승 시나리오가 우세하며", "하락": "하락 시나리오가 우세하며", "기본": "박스권 횡보가 예상되며"}
    prefix = label_map.get(dominant, "")
    if not prefix:
        return ""
    if comment:
        return f"시나리오 분석에서 {prefix} {comment}입니다."
    return f"시나리오 분석에서 {prefix} 방향성 확인이 필요합니다."


def _build_pattern_match_sentence(pm: dict) -> str:
    """유사 패턴 분석 기반 자연어 문장."""
    if not pm:
        return ""
    summary = pm.get("summary", {})
    count = summary.get("match_count", 0)
    if count == 0:
        return ""
    avg5 = summary.get("avg_return_5d")
    up5 = summary.get("up_ratio_5d")
    if avg5 is None or up5 is None:
        return ""
    direction = "상승" if avg5 > 0 else "하락"
    return f"과거 유사 패턴 {count}건에서 5일 후 평균 {avg5:+.1%}({direction}), 상승 확률 {up5:.0%}입니다."


def _join_parts(parts: list[str]) -> str:
    """여러 파트를 자연스럽게 연결."""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} {parts[1]}"
    return f"{parts[0]} {parts[1]} {parts[2]}"


_DELTA_KR = {
    "technical_score": "기술적",
    "supply_score": "수급",
    "exchange_score": "환율",
    "fundamentals_score": "펀더멘털",
    "news_score": "뉴스",
    "consensus_score": "컨센서스",
    "semiconductor_score": "반도체",
    "volatility_score": "변동성",
    "candlestick_score": "캔들스틱",
    "global_macro_score": "매크로",
}


def _build_delta_sentence(delta: dict) -> str:
    if not delta:
        return ""

    alerts = delta.get("alerts", [])
    if not alerts:
        return ""

    flips = [a for a in alerts if a["type"] == "signal_flip" and a["axis"] != "overall"]
    moves = [a for a in alerts if a["type"] == "significant_move" and a["axis"] != "overall"]

    if flips:
        alert = flips[0]
        axis = alert["axis"]
        kr = _DELTA_KR.get(axis, axis)
        ad = delta.get("axes_delta", {}).get(axis, {})
        change = ad.get("change", 0)
        direction = "매수 전환" if change > 0 else "매도 전환"
        return f"전일 대비 {kr} 점수가 {change:+.1f}점 변동하여 {direction} 시그널로 전환되었습니다."

    if moves:
        alert = moves[0]
        axis = alert["axis"]
        kr = _DELTA_KR.get(axis, axis)
        ad = delta.get("axes_delta", {}).get(axis, {})
        change = ad.get("change", 0)
        direction = "급등" if change > 0 else "급락"
        return f"전일 대비 {kr} 점수가 {change:+.1f}점 {direction}하여 주목할 필요가 있습니다."

    return ""


def _build_risk_management_sentence(rm: dict) -> str:
    if not rm:
        return ""

    rr = rm.get("risk_reward", {})
    guide = rm.get("position_guide", {})
    entry = rm.get("entry_zone", {})

    rr_ratio = rr.get("ratio")
    rr_grade = rr.get("grade", "")
    guide_level = guide.get("level", "")
    direction = entry.get("direction", "")

    parts: list[str] = []

    if rr_ratio is not None and rr_grade in ("유리", "불리"):
        if rr_grade == "유리":
            parts.append(f"리스크 대비 보상 비율이 {rr_ratio:.1f}로 유리한 구간입니다")
        else:
            parts.append(f"리스크 대비 보상 비율이 {rr_ratio:.1f}로 불리하여 주의가 필요합니다")

    if guide_level in ("공격적", "관망"):
        if guide_level == "공격적":
            parts.append("다수 조건이 유리하여 확대 진입을 고려할 수 있는 구간입니다")
        else:
            parts.append("불리 조건이 다수로 진입 대기가 적절합니다")

    if not parts:
        return ""

    return ". ".join(parts) + "."


_FIB_LEVEL_INTERPRETATION = {
    "0.236": ("매우 얕은 되돌림으로 강한 추세가 유지되고 있습니다", "얕은"),
    "0.382": ("얕은 되돌림 구간으로 추세의 힘이 강하게 유지되고 있습니다", "얕은"),
    "0.5": ("중간 되돌림 구간으로 추세의 방향성 확인이 필요합니다", "중간"),
    "0.618": ("깊은 되돌림 구간으로 추세 약화 가능성에 유의할 필요가 있습니다", "깊은"),
    "0.786": ("매우 깊은 되돌림으로 추세 전환 가능성이 높아지고 있습니다", "매우 깊은"),
}


def _build_fibonacci_sentence(fib: dict, current_price: float) -> str:
    """피보나치 되돌림 수준 관련 자연어 문장."""
    if not fib:
        return ""

    position = fib.get("position", {})
    below = position.get("below")
    above = position.get("above")
    retracement = fib.get("retracement", {})

    if not below or not retracement:
        return ""

    interp = _FIB_LEVEL_INTERPRETATION.get(below)
    if interp:
        desc, depth = interp
        ns = position.get("nearest_support")
        if ns is not None and current_price > 0:
            dist_pct = (current_price - ns) / current_price * 100
            if dist_pct < 2.0:
                return f"피보나치 {below} 되돌림 지지선({int(ns):,}원)에 근접해 있으며, {desc}."
        return f"현재가가 피보나치 {below}~{above} 구간에 위치하며, {desc}."

    return ""


def _build_volume_profile_sentence(vp: dict) -> str:
    """Volume Profile 기반 자연어 문장."""
    if not vp:
        return ""

    poc = vp.get("poc")
    if poc is None:
        return ""

    position = vp.get("position", {})
    vs_poc = position.get("vs_poc")
    in_va = position.get("in_value_area")
    current_price = vp.get("current_price")
    value_area = vp.get("value_area", {})
    vah = value_area.get("vah")
    val = value_area.get("val")

    if vs_poc == "above" and not in_va and vah is not None:
        return f"현재가가 거래 밀집대(POC {int(poc):,}원) 위, Value Area 상단({int(vah):,}원)을 돌파하여 추가 상승 모멘텀이 기대됩니다."
    elif vs_poc == "below" and not in_va and val is not None:
        return f"현재가가 거래 밀집대(POC {int(poc):,}원) 아래, Value Area 하단({int(val):,}원)을 이탈하여 매물 부담에 유의할 필요가 있습니다."
    elif in_va:
        return f"현재가가 거래 밀집 가치 영역(Value Area {int(val):,}~{int(vah):,}원) 내부에서 거래 중이며 POC({int(poc):,}원)가 지지/저항으로 작용할 수 있습니다."
    elif vs_poc == "above":
        return f"현재가가 POC({int(poc):,}원) 상회 중으로 거래 밀집대 위에서 거래되고 있습니다."
    elif vs_poc == "below":
        return f"현재가가 POC({int(poc):,}원) 하회 중으로 거래 밀집대 아래에서 매물 압력이 예상됩니다."

    return ""


def _build_backtest_sentence(bt: dict, sig: dict) -> str:
    """백테스팅 결과를 자연어 코멘터리로 변환한다."""
    if not bt:
        return ""

    grade = sig.get("grade", "")
    grade_perf = bt.get("grade_performance", {})
    current_stats = grade_perf.get(grade, {})

    hit_5d = current_stats.get("hit_rate_5d")
    if hit_5d is None:
        return ""

    count = current_stats.get("count", 0)
    if count < 3:
        return ""

    if hit_5d >= 65:
        return f"과거 {grade} 시그널의 5일 적중률이 {hit_5d:.0f}%로, 현재 시그널 신뢰도가 높다."
    elif hit_5d <= 45:
        return f"과거 {grade} 시그널의 5일 적중률이 {hit_5d:.0f}%에 불과해, 시그널 신뢰에 주의가 필요하다."
    else:
        return ""
