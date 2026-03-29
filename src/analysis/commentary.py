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

    # --- 1.5) OBV 다이버전스 문장 ---
    obv_sentence = _build_obv_divergence_sentence(indicators)
    if obv_sentence:
        sentences.append(obv_sentence)

    # --- 1.7) 추세 전환 감지 문장 ---
    reversal_sentence = _build_reversal_sentence(trend_reversal or {})
    if reversal_sentence:
        sentences.append(reversal_sentence)

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

    # --- 5) 시그널 추이 문장 ---
    trend_sentence = _build_signal_trend_sentence(signal_trend or {})
    if trend_sentence:
        sentences.append(trend_sentence)

    return " ".join(sentences)


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


def _join_parts(parts: list[str]) -> str:
    """여러 파트를 자연스럽게 연결."""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} {parts[1]}"
    return f"{parts[0]} {parts[1]} {parts[2]}"
