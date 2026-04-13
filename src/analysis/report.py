"""일일 분석 리포트 생성기.

compute_technical_indicators 결과를 투자자가 읽기 좋은
HTML 텔레그램 메시지로 변환한다.
"""

from __future__ import annotations


def classify_ma_alignment(indicators: dict) -> str:
    """이동평균선 배열 상태를 판단한다.

    Returns:
        "정배열" | "역배열" | "혼조" | "데이터 부족"
    """
    ma5 = indicators.get("ma5")
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")

    if ma5 is None or ma20 is None:
        return "데이터 부족"

    if ma60 is None:
        # MA5, MA20만으로 판단
        if ma5 > ma20:
            return "정배열"
        elif ma5 < ma20:
            return "역배열"
        return "혼조"

    if ma5 > ma20 > ma60:
        return "정배열"
    elif ma5 < ma20 < ma60:
        return "역배열"
    return "혼조"


def assess_volume(volume_ratio: float | None) -> str | None:
    """거래량 비율(5일 평균 대비)로 거래량 상태를 판단한다.

    Returns:
        "급증" | "증가" | "보통" | "감소" | None
    """
    if volume_ratio is None:
        return None
    if volume_ratio >= 2.0:
        return "급증"
    if volume_ratio >= 1.5:
        return "증가"
    if volume_ratio >= 0.7:
        return "보통"
    return "감소"


def classify_rsi(rsi: float | None) -> str:
    """RSI 상태를 판단한다.

    Returns:
        "과매수" | "과매도" | "중립" | "N/A"
    """
    if rsi is None:
        return "N/A"
    if rsi >= 70:
        return "과매수"
    if rsi <= 30:
        return "과매도"
    return "중립"


def classify_macd(
    macd: float | None,
    signal: float | None,
    histogram: float | None,
) -> str:
    """MACD 크로스 상태를 판단한다.

    Returns:
        "골든크로스" | "데드크로스" | "N/A"
    """
    if macd is None or signal is None or histogram is None:
        return "N/A"
    if histogram > 0:
        return "골든크로스"
    if histogram < 0:
        return "데드크로스"
    return "N/A"


def _histogram_direction(histogram: float | None) -> str:
    """히스토그램 방향을 판단한다."""
    if histogram is None:
        return ""
    if histogram > 0:
        return "확장"
    return "수축"


def classify_stochastic(
    stoch_k: float | None, stoch_d: float | None,
) -> str:
    """스토캐스틱 오실레이터 상태를 판단한다.

    Returns:
        "과매수" | "과매도" | "골든크로스" | "데드크로스" | "N/A"
    """
    if stoch_k is None:
        return "N/A"
    if stoch_k >= 80:
        return "과매수"
    if stoch_k <= 20:
        return "과매도"
    if stoch_d is not None:
        if stoch_k > stoch_d:
            return "골든크로스"
        if stoch_k < stoch_d:
            return "데드크로스"
    return "N/A"


def classify_bb_position(bb_pctb: float | None) -> str:
    """볼린저 밴드 %B 위치를 판단한다.

    Returns:
        "상단 돌파" | "하단 이탈" | "밴드 내" | "N/A"
    """
    if bb_pctb is None:
        return "N/A"
    if bb_pctb > 1.0:
        return "상단 돌파"
    if bb_pctb < 0:
        return "하단 이탈"
    return "밴드 내"


def assess_market_temperature(
    change_1d_pct: float | None,
    ma_alignment: str,
    volume_status: str | None,
    rsi_14: float | None = None,
    macd_cross: str | None = None,
    bb_pctb: float | None = None,
) -> str:
    """종합 시장 온도를 판정한다.

    4개 지표를 스코어링: 3점↑ 강세, 2점 중립, 1점↓ 약세.

    Returns:
        "강세" | "중립" | "약세"
    """
    score = 0
    count = 0

    # 1) 전일 대비 등락
    if change_1d_pct is not None:
        count += 1
        if change_1d_pct > 1.0:
            score += 2
        elif change_1d_pct > 0:
            score += 1
        elif change_1d_pct < -1.0:
            score -= 2
        elif change_1d_pct < 0:
            score -= 1

    # 2) 이동평균 배열
    if ma_alignment not in ("데이터 부족",):
        count += 1
        if ma_alignment == "정배열":
            score += 2
        elif ma_alignment == "역배열":
            score -= 2

    # 3) 거래량 상태 (상승 중 거래량 증가는 긍정, 하락 중 거래량 증가는 부정)
    if volume_status is not None:
        count += 1
        is_rising = change_1d_pct is not None and change_1d_pct > 0
        if volume_status in ("급증", "증가"):
            score += 1 if is_rising else -1
        elif volume_status == "감소":
            score -= 1 if is_rising else 0

    # 4) RSI: 과매수 시 약세 가산, 과매도 시 강세 가산
    if rsi_14 is not None:
        rsi_status = classify_rsi(rsi_14)
        if rsi_status != "중립":
            count += 1
            if rsi_status == "과매수":
                score -= 2
            elif rsi_status == "과매도":
                score += 2

    # 5) MACD 크로스 상태
    if macd_cross is not None and macd_cross != "N/A":
        count += 1
        if macd_cross == "골든크로스":
            score += 2
        elif macd_cross == "데드크로스":
            score -= 2

    # 6) 볼린저 밴드 %B: 밴드 이탈 시만 반영
    if bb_pctb is not None:
        bb_pos = classify_bb_position(bb_pctb)
        if bb_pos != "밴드 내":
            count += 1
            if bb_pos == "상단 돌파":
                score -= 2  # 과열 → 약세 가산
            elif bb_pos == "하단 이탈":
                score += 2  # 침체 → 강세 가산 (반등 기대)

    if count == 0:
        return "중립"

    avg = score / count
    if avg >= 1.0:
        return "강세"
    elif avg <= -1.0:
        return "약세"
    return "중립"


def _format_price(price: float) -> str:
    """가격을 천단위 콤마 포맷."""
    return f"{int(price):,}"


def _format_change(pct: float | None) -> str:
    """변동률을 부호 포함 문자열로."""
    if pct is None:
        return "N/A"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.2f}%"


def _volume_emoji(status: str | None) -> str:
    if status == "급증":
        return "🔥"
    if status == "증가":
        return "📈"
    if status == "감소":
        return "📉"
    return ""


def _temp_emoji(temp: str) -> str:
    if temp == "강세":
        return "🟢"
    if temp == "약세":
        return "🔴"
    return "🟡"


def _format_shares(shares: int | None) -> str:
    """주 단위 순매매를 읽기 쉬운 형식으로."""
    if shares is None:
        return "N/A"
    sign = "+" if shares > 0 else ""
    if abs(shares) >= 1_000_000:
        return f"{sign}{shares / 1_000_000:.1f}백만주"
    if abs(shares) >= 10_000:
        return f"{sign}{shares / 10_000:.1f}만주"
    return f"{sign}{shares:,}주"


def _ownership_arrow(trend: str | None) -> str:
    if trend == "increasing":
        return "↑"
    if trend == "decreasing":
        return "↓"
    return "→"


def _judgment_label(judgment: str) -> tuple[str, str]:
    """종합 판정을 (라벨, 이모지) 튜플로."""
    if judgment == "buy_dominant":
        return "매수우위", "🟢"
    if judgment == "sell_dominant":
        return "매도우위", "🔴"
    return "중립", "🟡"


def _trend_emoji(trend: str | None) -> str:
    if trend == "원화약세":
        return "📈"
    if trend == "원화강세":
        return "📉"
    return "➡️"


def _build_exchange_rate_section(er: dict) -> list[str]:
    """환율 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>💱 USD/KRW 환율</b>")

    rate = er["current_rate"]
    change_1d = er.get("change_1d_pct")
    lines.append(f"  현재: {rate:,.1f}원 ({_format_change(change_1d)})")

    change_5d = er.get("change_5d_pct")
    change_20d = er.get("change_20d_pct")
    lines.append(f"  5일: {_format_change(change_5d)} | 20일: {_format_change(change_20d)}")

    trend = er.get("trend")
    if trend:
        lines.append(f"  추세: {_trend_emoji(trend)} {trend}")

    corr = er.get("correlation_20d")
    if corr is not None:
        if corr > 0.5:
            corr_label = "양의 상관"
        elif corr < -0.5:
            corr_label = "음의 상관"
        else:
            corr_label = "약한 상관"
        lines.append(f"  주가 상관(20일): {corr:.2f} ({corr_label})")

    return lines


def _build_supply_demand_section(sd: dict) -> list[str]:
    """수급 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>📊 수급 동향</b>")

    # 외국인 연속 매수/매도
    fb = sd["foreign_consecutive_net_buy"]
    fs = sd["foreign_consecutive_net_sell"]
    if fb > 0:
        lines.append(f"  외국인: 연속 {fb}일 순매수")
    elif fs > 0:
        lines.append(f"  외국인: 연속 {fs}일 순매도")
    else:
        lines.append("  외국인: 매매 전환")

    # 기관 연속 매수/매도
    ib = sd["institution_consecutive_net_buy"]
    is_ = sd["institution_consecutive_net_sell"]
    if ib > 0:
        lines.append(f"  기관: 연속 {ib}일 순매수")
    elif is_ > 0:
        lines.append(f"  기관: 연속 {is_}일 순매도")
    else:
        lines.append("  기관: 매매 전환")

    # 5일 누적 순매매
    lines.append(f"  5일 누적: 외국인 {_format_shares(sd['foreign_cumulative_5d'])} | 기관 {_format_shares(sd['institution_cumulative_5d'])}")

    # 보유비율 추이
    trend = sd.get("ownership_trend")
    change = sd.get("ownership_change_pct")
    arrow = _ownership_arrow(trend)
    if change is not None:
        sign = "+" if change > 0 else ""
        lines.append(f"  보유비율: {arrow} ({sign}{change:.2f}%p)")
    elif trend is not None:
        lines.append(f"  보유비율: {arrow}")

    # 종합 판정
    label, emoji = _judgment_label(sd["overall_judgment"])
    lines.append(f"  <b>수급 판정:</b> {emoji} {label}")

    return lines


def _grade_emoji(grade: str) -> str:
    """종합 시그널 등급 이모지."""
    if grade == "강력매수신호":
        return "🟢🟢"
    if grade == "매수우세":
        return "🟢"
    if grade == "중립":
        return "🟡"
    if grade == "매도우세":
        return "🔴"
    return "🔴🔴"


def _score_bar(score: float) -> str:
    """점수를 시각적 게이지 바로 변환. -100~+100."""
    # 10단계 (5칸 기준, -100~+100을 0~10으로 매핑)
    filled = int((score + 100) / 20)
    filled = max(0, min(10, filled))
    return "█" * filled + "░" * (10 - filled)


def _build_composite_signal_section(sig: dict) -> list[str]:
    """종합 투자 시그널을 HTML 라인 리스트로."""
    lines = []
    grade = sig["grade"]
    score = sig["score"]
    lines.append(f"<b>🎯 오늘의 종합 판정: {_grade_emoji(grade)} {grade}</b>")
    lines.append(f"  [{_score_bar(score)}] {score:+.1f}점")
    lines.append("")
    lines.append(f"  기술적: {sig['technical_score']:+.0f} (가중치 {sig['weights']['technical']}%)")
    lines.append(f"  수급: {sig['supply_score']:+.0f} (가중치 {sig['weights']['supply']}%)")
    lines.append(f"  환율: {sig['exchange_score']:+.0f} (가중치 {sig['weights']['exchange']}%)")
    if "rs_score" in sig:
        rs_w = sig["weights"].get("relative_strength", 15)
        lines.append(f"  상대강도: {sig['rs_score']:+.0f} (가중치 {rs_w}%)")
    if "fundamentals_score" in sig:
        fund_w = sig["weights"].get("fundamentals", 15)
        lines.append(f"  펀더멘털: {sig['fundamentals_score']:+.0f} (가중치 {fund_w}%)")
    if "news_score" in sig:
        news_w = sig["weights"].get("news", 10)
        lines.append(f"  뉴스: {sig['news_score']:+.0f} (가중치 {news_w}%)")
    if "consensus_score" in sig:
        cons_w = sig["weights"].get("consensus", 10)
        lines.append(f"  컨센서스: {sig['consensus_score']:+.0f} (가중치 {cons_w}%)")
    if "semiconductor_score" in sig:
        semi_w = sig["weights"].get("semiconductor", 10)
        lines.append(f"  반도체: {sig['semiconductor_score']:+.0f} (가중치 {semi_w}%)")
    if "volatility_score" in sig:
        vol_w = sig["weights"].get("volatility", 5)
        lines.append(f"  변동성: {sig['volatility_score']:+.0f} (가중치 {vol_w}%)")
    if "candlestick_score" in sig:
        candle_w = sig["weights"].get("candlestick", 5)
        lines.append(f"  캔들스틱: {sig['candlestick_score']:+.0f} (가중치 {candle_w}%)")
    lines.append("")
    return lines


def _build_support_resistance_section(sr: dict, current_price: float) -> list[str]:
    """지지/저항선 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>📐 지지/저항선</b>")

    pivot = sr["pivot"]
    if pivot["pp"] is not None:
        lines.append(
            f"  PP: {_format_price(pivot['pp'])} | "
            f"S1: {_format_price(pivot['s1'])} | S2: {_format_price(pivot['s2'])}"
        )
        lines.append(
            f"  R1: {_format_price(pivot['r1'])} | R2: {_format_price(pivot['r2'])}"
        )

    ns = sr["nearest_support"]
    nr = sr["nearest_resistance"]

    if ns is not None:
        dist_pct = (current_price - ns) / current_price * 100
        lines.append(f"  가장 가까운 지지선: {_format_price(ns)}원 ({dist_pct:+.1f}%)")
    if nr is not None:
        dist_pct = (nr - current_price) / current_price * 100
        lines.append(f"  가장 가까운 저항선: {_format_price(nr)}원 (+{dist_pct:.1f}%)")

    if ns is None and nr is None and pivot["pp"] is None:
        lines.append("  데이터 부족")

    return lines


_AXIS_KR_NAME: dict[str, str] = {
    "technical_score": "기술적",
    "supply_score": "수급",
    "exchange_score": "환율",
    "fundamentals_score": "펀더멘털",
    "news_score": "뉴스",
    "consensus_score": "컨센서스",
    "semiconductor_score": "반도체",
    "volatility_score": "변동성",
    "candlestick_score": "캔들스틱",
    "global_macro_score": "글로벌매크로",
}


def _hit_rate_label(rate: float) -> str:
    """적중률 수준 라벨."""
    if rate >= 70:
        return "🟢높음"
    if rate >= 50:
        return "🟡보통"
    return "🔴낮음"


def _build_accuracy_section(
    acc: dict, composite_signal: dict | None = None,
) -> list[str]:
    """시그널 정확도 통계를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>🎯 시그널 정확도</b>")

    # 적응형 가중치 활성 표시
    if composite_signal and composite_signal.get("adapted_weights"):
        lines.append("  ⚡ 적응형 가중치 활성")

    # 데이터 부족 판단: 1일 기준 evaluated_signals가 5 미만이면 축적 중
    eval_1d = acc.get("evaluated_signals_1d", 0)
    if eval_1d < 5:
        lines.append(f"  📊 데이터 축적 중 (평가 시그널: {acc.get('total_signals', 0)}개)")
        return lines

    lines.append(f"  총 평가 시그널: {acc['total_signals']}개")
    lines.append("")

    for n in (1, 3, 5):
        hit = acc.get(f"hit_rate_{n}d")
        ret = acc.get(f"avg_return_{n}d")
        count = acc.get(f"evaluated_signals_{n}d", 0)

        hit_str = f"{hit:.1f}%" if hit is not None else "N/A"
        ret_str = f"{ret:+.2f}%" if ret is not None else "N/A"
        lines.append(f"  {n}일 적중률: {hit_str} | 평균 수익률: {ret_str} ({count}건)")

    # 축별 5일 적중률 테이블
    per_axis = acc.get("per_axis", {})
    axis_rows = []
    for axis_key, kr_name in _AXIS_KR_NAME.items():
        axis_data = per_axis.get(axis_key, {})
        evaluated = axis_data.get("evaluated_5d", 0)
        if evaluated < 5:
            continue
        hit = axis_data.get("hit_rate_5d")
        if hit is None:
            continue
        axis_rows.append((kr_name, hit, evaluated))

    if axis_rows:
        lines.append("")
        lines.append("  <b>축별 5일 적중률</b>")
        for kr_name, hit, evaluated in axis_rows:
            label = _hit_rate_label(hit)
            lines.append(f"  {kr_name}: {hit:.0f}% {label} ({evaluated}건)")

    return lines


def _rs_trend_label(trend: str) -> tuple[str, str]:
    """RS 추세를 (라벨, 이모지) 튜플로."""
    if trend == "outperform":
        return "시장 대비 강세", "💪"
    if trend == "underperform":
        return "시장 대비 약세", "📉"
    return "시장 동행", "➡️"


def _convergence_emoji(convergence: str) -> str:
    if convergence == "strong":
        return "🔴"
    if convergence == "moderate":
        return "🟡"
    return ""


def _build_trend_reversal_section(tr: dict) -> list[str]:
    """추세 전환 감지 결과를 HTML 라인 리스트로.

    convergence가 weak/none이면 빈 리스트 반환(섹션 생략).
    """
    convergence = tr.get("convergence", "none")
    if convergence in ("weak", "none"):
        return []

    lines = []
    lines.append("")
    lines.append("<b>🔄 추세 전환 감지</b>")

    direction = tr.get("direction", "neutral")
    dir_kr = "강세" if direction == "bullish" else "약세"
    grade_kr = "강한" if convergence == "strong" else "중간"

    lines.append(f"  {_convergence_emoji(convergence)} {grade_kr} {dir_kr} 반전 컨버전스")
    lines.append(f"  점수: {tr.get('score', 0):.0f}/100 | 활성 카테고리: {tr.get('active_categories', 0)}개")

    # 활성 카테고리 상세
    cat_kr = {
        "momentum": "모멘텀", "trend": "추세", "volatility": "변동성",
        "volume": "거래량", "structure": "구조",
    }
    cat_signals = tr.get("category_signals", {})
    active = [
        cat_kr.get(cat, cat)
        for cat, sig in cat_signals.items()
        if sig.get("direction") == direction
    ]
    if active:
        lines.append(f"  활성: {', '.join(active)}")

    return lines


def _build_relative_strength_section(rs: dict) -> list[str]:
    """상대강도 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>📊 시장 상대강도 (vs KOSPI)</b>")

    trend_label, trend_emoji = _rs_trend_label(rs.get("rs_trend", "neutral"))
    lines.append(f"  추세: {trend_emoji} {trend_label}")

    # N일 수익률 비교
    for n in (1, 5, 20):
        s_ret = rs.get(f"samsung_return_{n}d")
        k_ret = rs.get(f"kospi_return_{n}d")
        alpha = rs.get(f"alpha_{n}d")
        if s_ret is not None and k_ret is not None and alpha is not None:
            sign = "+" if alpha > 0 else ""
            lines.append(f"  {n}일: 삼성 {s_ret:+.2f}% vs KOSPI {k_ret:+.2f}% (α {sign}{alpha:.2f}%)")

    # RS 수치
    rs_cur = rs.get("rs_current")
    rs_ma = rs.get("rs_ma20")
    if rs_cur is not None:
        ma_str = f" / MA20: {rs_ma:.2f}" if rs_ma is not None else ""
        lines.append(f"  RS: {rs_cur:.2f}{ma_str}")

    return lines


def _valuation_emoji(val: str) -> str:
    if val == "저평가":
        return "🟢"
    if val == "고평가":
        return "🔴"
    if val == "적정":
        return "🟡"
    return ""


def _sentiment_emoji(label: str) -> str:
    if label == "bullish":
        return "🟢"
    if label == "bearish":
        return "🔴"
    return "🟡"


def _build_news_sentiment_section(
    news: dict, headlines: list[dict] | None = None,
) -> list[str]:
    """뉴스 감정 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>📰 뉴스 심리</b>")

    label = news.get("label", "neutral")
    label_kr = {"bullish": "긍정적", "bearish": "부정적", "neutral": "중립"}.get(label, "중립")
    lines.append(f"  판정: {_sentiment_emoji(label)} {label_kr}")

    pos = news.get("positive", 0)
    neg = news.get("negative", 0)
    neu = news.get("neutral", 0)
    lines.append(f"  긍정 {pos} | 부정 {neg} | 중립 {neu}")

    # 주요 헤드라인 최대 3개
    if headlines:
        shown = headlines[:3]
        for h in shown:
            title = h.get("title", "")
            source = h.get("source", "")
            if title:
                lines.append(f"  · {title} ({source})")

    return lines


def _consensus_valuation_emoji(val: str) -> str:
    if val == "저평가":
        return "🟢"
    if val == "고평가":
        return "🔴"
    if val == "적정하단":
        return "🟡"
    if val == "적정":
        return "🟡"
    return ""


def _build_volatility_section(vol: dict) -> list[str]:
    """변동성 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>📉 변동성 분석</b>")

    atr = vol.get("atr")
    atr_pct = vol.get("atr_pct")
    if atr is not None and atr_pct is not None:
        lines.append(f"  ATR(14): {atr:,.0f}원 ({atr_pct:.1f}%)")

    hv20 = vol.get("hv20")
    if hv20 is not None:
        lines.append(f"  HV20(연율화): {hv20 * 100:.1f}%")

    regime = vol.get("volatility_regime")
    percentile = vol.get("volatility_percentile")
    if regime is not None:
        pct_str = f" (백분위 {percentile:.0f}%)" if percentile is not None else ""
        regime_emoji = "🔴" if regime == "고변동성" else "🟢" if regime == "저변동성" else ""
        lines.append(f"  변동성 체제: {regime}{pct_str} {regime_emoji}".rstrip())

    squeeze = vol.get("bandwidth_squeeze")
    if squeeze:
        lines.append("  ⚡ 볼린저 밴드폭 수축 감지 — 돌파 대비 구간")

    return lines


def _build_candlestick_section(candle: dict) -> list[str]:
    """캔들스틱 패턴 분석 결과를 HTML 라인 리스트로."""
    lines = []
    patterns = candle.get("patterns", [])
    if not patterns:
        return lines

    lines.append("")
    lines.append("<b>🕯 캔들스틱 패턴</b>")

    signal = candle.get("signal", "neutral")
    score = candle.get("score", 0)

    signal_kr = {"bullish": "강세", "bearish": "약세", "neutral": "중립"}.get(signal, "중립")
    signal_emoji = "🟢" if signal == "bullish" else "🔴" if signal == "bearish" else ""

    pattern_names = {
        "doji": "도지", "hammer": "해머", "hanging_man": "행잉맨",
        "bullish_marubozu": "강세 마루보즈", "bearish_marubozu": "약세 마루보즈",
        "bullish_engulfing": "강세 인걸핑", "bearish_engulfing": "약세 인걸핑",
        "morning_star": "모닝스타", "evening_star": "이브닝스타",
    }

    for p in patterns:
        name = pattern_names.get(p["name"], p["name"])
        dir_kr = {"bullish": "강세", "bearish": "약세", "neutral": "중립"}.get(p["direction"], "")
        lines.append(f"  {name} ({dir_kr}, 신뢰도 {p['weight']})")

    lines.append(f"  종합: {signal_kr} ({score:+.0f}점) {signal_emoji}".rstrip())

    return lines


def _build_convergence_section(conv: dict) -> list[str]:
    """다축 수렴 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>🔀 다축 수렴 분석</b>")

    level = conv.get("convergence_level", "mixed")
    direction = conv.get("dominant_direction", "neutral")
    conviction = conv.get("conviction", 0)
    aligned = conv.get("aligned_axes", [])
    conflicting = conv.get("conflicting_axes", [])
    neutral = conv.get("neutral_axes", [])

    level_kr = {"strong": "강한 수렴", "moderate": "보통 수렴",
                "weak": "약한 수렴", "mixed": "혼조"}.get(level, level)
    dir_kr = {"bullish": "강세", "bearish": "약세", "neutral": "중립"}.get(direction, direction)

    level_emoji = {"strong": "🟢", "moderate": "🟡", "weak": "🟠", "mixed": "🔴"}.get(level, "⚪")

    lines.append(f"  수렴 수준: {level_emoji} {level_kr}")
    lines.append(f"  지배 방향: {dir_kr}")
    lines.append(f"  확신도: {conviction}%")

    axis_label = {
        "technical_score": "기술적", "supply_score": "수급",
        "exchange_score": "환율", "fundamental_score": "펀더멘털",
        "news_score": "뉴스", "consensus_score": "컨센서스",
        "semiconductor_score": "반도체", "volatility_score": "변동성",
        "candlestick_score": "캔들스틱",
    }

    if aligned:
        names = [axis_label.get(a, a) for a in aligned]
        lines.append(f"  일치 축({len(aligned)}): {', '.join(names)}")
    if conflicting:
        names = [axis_label.get(a, a) for a in conflicting]
        lines.append(f"  충돌 축({len(conflicting)}): {', '.join(names)}")
    if neutral:
        names = [axis_label.get(a, a) for a in neutral]
        lines.append(f"  중립 축({len(neutral)}): {', '.join(names)}")

    return lines


def _build_consensus_section(cons: dict) -> list[str]:
    """증권사 컨센서스 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>🏦 증권사 컨센서스</b>")

    target = cons.get("target_price")
    current = cons.get("current_price")
    divergence = cons.get("divergence_pct")
    valuation = cons.get("valuation", "판정불가")

    if target is not None:
        lines.append(f"  목표가: {int(target):,}원 (현재가: {int(current):,}원)" if current else f"  목표가: {int(target):,}원")

    if divergence is not None:
        lines.append(f"  괴리율: {divergence:+.1f}% ({_consensus_valuation_emoji(valuation)} {valuation})")

    rec = cons.get("recommendation")
    rec_label = cons.get("recommendation_label", "판정불가")
    if rec is not None:
        lines.append(f"  투자의견: {rec:.2f} ({rec_label})")

    tone = cons.get("research_tone", "중립")
    tone_emoji = "🟢" if tone == "긍정" else "🔴" if tone == "부정" else "🟡"
    lines.append(f"  증권가 톤: {tone_emoji} {tone}")

    # 최근 리포트 Top 3
    researches = cons.get("researches", [])
    if researches:
        for r in researches[:3]:
            title = r.get("title", "")
            broker = r.get("broker", "")
            if title:
                lines.append(f"  · {title} ({broker})")

    return lines


def _build_fundamentals_section(fund: dict) -> list[str]:
    """펀더멘털 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>📋 펀더멘털 분석</b>")

    per = fund.get("per")
    per_val = fund.get("per_valuation", "판정불가")
    per_str = f"{per:.1f}" if per is not None else "N/A"
    lines.append(f"  PER: {per_str} ({_valuation_emoji(per_val)} {per_val})")

    pbr = fund.get("pbr")
    pbr_val = fund.get("pbr_valuation", "판정불가")
    pbr_str = f"{pbr:.2f}" if pbr is not None else "N/A"
    lines.append(f"  PBR: {pbr_str} ({_valuation_emoji(pbr_val)} {pbr_val})")

    div_yield = fund.get("dividend_yield")
    div_attr = fund.get("dividend_attractiveness", "판정불가")
    div_str = f"{div_yield:.2f}%" if div_yield is not None else "N/A"
    lines.append(f"  배당수익률: {div_str} ({div_attr})")

    eps = fund.get("eps")
    est_eps = fund.get("estimated_eps")
    eps_str = f"{eps:,}" if eps is not None else "N/A"
    est_eps_str = f"{est_eps:,}" if est_eps is not None else "N/A"
    lines.append(f"  EPS: {eps_str}원 | 추정EPS: {est_eps_str}원")

    outlook = fund.get("earnings_outlook", "판정불가")
    outlook_emoji = "📈" if outlook == "개선" else "📉" if outlook == "악화" else "➡️"
    lines.append(f"  실적 전망: {outlook_emoji} {outlook}")

    return lines


def _build_signal_trend_section(trend: dict) -> list[str]:
    """시그널 추이 섹션을 생성한다."""
    lines = [""]
    direction = trend.get("direction", "횡보")
    dir_emoji = "📈" if direction == "개선" else "📉" if direction == "악화" else "➡️"
    sparkline = trend.get("sparkline", "")
    days = trend.get("days_available", 0)
    consec = trend.get("consecutive_same_grade", 0)
    latest_grade = trend.get("latest_grade", "")
    score_change = trend.get("score_change", 0)
    scores = trend.get("scores", [])

    lines.append(f"<b>{dir_emoji} 시그널 추이 ({days}일)</b>")

    # 스파크라인 + 점수 범위
    if scores:
        score_strs = [f"{s:+.0f}" for s in scores]
        lines.append(f"  {sparkline}  ({' → '.join(score_strs)})")

    # 추세 방향 + 변동폭
    change_str = f"{score_change:+.1f}p" if score_change != 0 else "변동없음"
    lines.append(f"  추세: {direction} ({change_str})")

    # 연속 동일 등급
    if consec >= 2:
        lines.append(f"  {latest_grade} {consec}일 연속 유지")

    lines.append("")
    return lines


def _judgment_emoji(judgment: str) -> str:
    """주간 판정 이모지."""
    if "상승" in judgment:
        return "📈"
    if "하락" in judgment:
        return "📉"
    return "➡️"


def _build_weekly_summary_section(ws: dict) -> list[str]:
    """주간 추이 요약을 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append(f"<b>📅 주간 추이 ({ws['start_date']} ~ {ws['end_date']})</b>")

    change_pct = ws["change_pct"]
    sign = "+" if change_pct > 0 else ""
    lines.append(
        f"  {_judgment_emoji(ws['judgment'])} {ws['judgment']} "
        f"({sign}{change_pct:.1f}%)"
    )
    lines.append(
        f"  시가: {_format_price(ws['week_open'])} → 종가: {_format_price(ws['week_close'])}"
    )
    lines.append(
        f"  고가: {_format_price(ws['week_high'])} | 저가: {_format_price(ws['week_low'])}"
    )

    avg_vol = ws["avg_daily_volume"]
    if avg_vol >= 1_000_000:
        vol_str = f"{avg_vol / 1_000_000:.1f}백만주"
    else:
        vol_str = f"{avg_vol:,.0f}주"
    lines.append(f"  일평균 거래량: {vol_str}")

    foreign = ws.get("foreign_net_total", 0)
    institution = ws.get("institution_net_total", 0)
    lines.append(
        f"  주간 수급: 외국인 {_format_shares(foreign)} | 기관 {_format_shares(institution)}"
    )

    sig_change = ws.get("signal_score_change")
    sig_start = ws.get("signal_start_grade", "")
    sig_end = ws.get("signal_end_grade", "")
    if sig_change is not None and sig_start and sig_end:
        lines.append(
            f"  시그널: {sig_start} → {sig_end} ({sig_change:+.0f}p)"
        )

    return lines


def _build_semiconductor_section(
    rel_perf: dict, sox_trend: dict, momentum: int,
) -> list[str]:
    """반도체 업황 분석 결과를 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>🔬 반도체 업황</b>")

    # 삼성전자 vs SK하이닉스 상대성과
    alpha_5d = rel_perf.get("alpha_5d")
    alpha_20d = rel_perf.get("alpha_20d")
    trend = rel_perf.get("relative_trend", "neutral")
    trend_kr = {"outperform": "우위", "underperform": "열위", "neutral": "동행"}.get(trend, "동행")

    alpha_5d_str = f"{alpha_5d:+.1f}%" if alpha_5d is not None else "N/A"
    alpha_20d_str = f"{alpha_20d:+.1f}%" if alpha_20d is not None else "N/A"
    lines.append(f"  vs SK하이닉스: {trend_kr} (5일 α {alpha_5d_str} | 20일 α {alpha_20d_str})")

    # SOX 지수 추세
    sox_label = sox_trend.get("trend", "횡보")
    sox_change = sox_trend.get("change_pct", 0)
    sox_current = sox_trend.get("current")
    sox_emoji = "📈" if sox_label == "상승" else "📉" if sox_label == "하락" else "➡️"
    current_str = f" ({sox_current:,.0f})" if sox_current is not None else ""
    lines.append(f"  SOX: {sox_emoji} {sox_label} ({sox_change:+.1f}%){current_str}")

    # 모멘텀 스코어
    if momentum >= 30:
        m_emoji = "🟢"
    elif momentum <= -30:
        m_emoji = "🔴"
    else:
        m_emoji = "🟡"
    lines.append(f"  모멘텀: {m_emoji} {momentum:+d}점")

    return lines


def _build_global_macro_section(
    nasdaq_trend: dict, vix_risk: dict, macro_score: int,
) -> list[str]:
    """글로벌 매크로 현황을 HTML 라인 리스트로."""
    lines = []
    lines.append("")
    lines.append("<b>🌍 글로벌 매크로</b>")

    # NASDAQ 추세
    trend = nasdaq_trend.get("trend", "보합")
    ma_pos = nasdaq_trend.get("ma_position", "근접")
    change_pct = nasdaq_trend.get("change_pct", 0)
    trend_emoji = "📈" if trend == "상승" else "📉" if trend == "하락" else "➡️"
    lines.append(f"  NASDAQ: {trend_emoji} {trend} ({change_pct:+.1f}%) | MA 대비 {ma_pos}")

    # VIX 리스크
    level = vix_risk.get("level", "안정")
    vix_val = vix_risk.get("value")
    vix_emoji = {"안정": "🟢", "경계": "🟡", "공포": "🔴", "극단": "🔴"}.get(level, "⚪")
    val_str = f" ({vix_val:.1f})" if vix_val is not None else ""
    lines.append(f"  VIX: {vix_emoji} {level}{val_str}")

    # 매크로 스코어
    if macro_score >= 30:
        s_emoji = "🟢"
    elif macro_score <= -30:
        s_emoji = "🔴"
    else:
        s_emoji = "🟡"
    lines.append(f"  매크로 스코어: {s_emoji} {macro_score:+d}점")

    return lines


_DELTA_AXIS_NAMES = {
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


def _build_daily_delta_section(delta: dict) -> list[str]:
    lines: list[str] = []
    lines.append("")
    lines.append("<b>📊 오늘의 변화</b>")

    overall = delta.get("overall", {})
    change = overall.get("change", 0)
    prev_score = overall.get("prev_score", 0)
    curr_score = overall.get("curr_score", 0)
    bar_len = min(abs(int(change)), 10)
    bar_char = "▓" if change >= 0 else "░"
    spark = bar_char * bar_len if bar_len > 0 else "–"
    arrow = "⬆️" if change > 0 else "⬇️" if change < 0 else ""
    lines.append(f"  종합: {prev_score:+.1f} → {curr_score:+.1f} ({change:+.1f}) {spark} {arrow}")

    prev_grade = overall.get("prev_grade", "")
    curr_grade = overall.get("curr_grade", "")
    if prev_grade and curr_grade and prev_grade != curr_grade:
        lines.append(f"  등급: {prev_grade} → {curr_grade}")

    alerts = delta.get("alerts", [])
    if not alerts:
        lines.append("  주요 변화 없음")
        return lines

    for alert in alerts:
        atype = alert.get("type", "")
        axis = alert.get("axis", "")
        detail = alert.get("detail", "")
        kr_name = _DELTA_AXIS_NAMES.get(axis, axis)

        if atype == "signal_flip":
            lines.append(f"  🔄 {kr_name}: {detail}")
        elif atype == "significant_move":
            ax_delta = delta.get("axes_delta", {}).get(axis, {})
            ch = ax_delta.get("change", 0)
            emoji = "⬆️" if ch > 0 else "⬇️"
            lines.append(f"  {emoji} {kr_name}: {detail}")
        elif atype == "grade_change":
            lines.append(f"  🔄 등급 전환: {detail}")

    return lines


def _build_executive_summary(
    composite_signal: dict | None = None,
    signal_trend: dict | None = None,
    indicators: dict | None = None,
    support_resistance: dict | None = None,
    trend_reversal: dict | None = None,
) -> list[str]:
    """핵심 요약(Executive Summary) 섹션을 생성한다.

    투자자가 이 섹션만 읽어도 오늘의 시장 상황을 파악할 수 있도록
    종합 등급, 주요 축, 방향 변화, 주의 이벤트를 압축 표시한다.
    """
    if composite_signal is None:
        return []

    lines = []
    sig = composite_signal
    grade = sig["grade"]
    score = sig["score"]

    lines.append(f"<b>📊 핵심 요약</b>")

    # (1) 종합 시그널 점수와 등급 한 줄 표시
    lines.append(f"  {_grade_emoji(grade)} {grade} ({score:+.1f}점)")

    # (2) 가장 강한 매수/매도 축 2개 하이라이트
    axis_names = {
        "technical_score": "기술적",
        "supply_score": "수급",
        "exchange_score": "환율",
        "rs_score": "상대강도",
        "fundamentals_score": "펀더멘털",
        "news_score": "뉴스",
        "consensus_score": "컨센서스",
        "semiconductor_score": "반도체",
        "volatility_score": "변동성",
        "candlestick_score": "캔들스틱",
    }
    axes = []
    for key, name in axis_names.items():
        if key in sig:
            axes.append((name, sig[key]))

    # 절대값 기준 상위 2개
    axes.sort(key=lambda x: abs(x[1]), reverse=True)
    top_axes = axes[:2]
    if top_axes:
        parts = []
        for name, val in top_axes:
            direction = "▲" if val > 0 else "▼" if val < 0 else "–"
            parts.append(f"{name}{direction}")
        lines.append(f"  주요 축: {' | '.join(parts)}")

    # (3) 전일 대비 시그널 방향 변화
    if signal_trend is not None:
        direction = signal_trend.get("direction", "횡보")
        score_change = signal_trend.get("score_change", 0)
        dir_emoji = "📈" if direction == "개선" else "📉" if direction == "악화" else "➡️"
        change_str = f"{score_change:+.1f}p" if score_change != 0 else "변동없음"
        lines.append(f"  방향: {dir_emoji} {direction} ({change_str})")

    # (4) 주의 이벤트
    alerts = []

    # 추세 전환 감지
    if trend_reversal is not None:
        convergence = trend_reversal.get("convergence", "none")
        if convergence in ("strong", "moderate"):
            tr_dir = trend_reversal.get("direction", "neutral")
            dir_kr = "강세" if tr_dir == "bullish" else "약세"
            alerts.append(f"추세 전환({dir_kr}) 감지")

    # 지지/저항 근접 (현재가 대비 1% 이내)
    if support_resistance is not None and indicators is not None:
        price = indicators.get("current_price", 0)
        if price > 0:
            ns = support_resistance.get("nearest_support")
            nr = support_resistance.get("nearest_resistance")
            if ns is not None:
                dist = (price - ns) / price * 100
                if dist <= 1.0:
                    alerts.append(f"지지선 근접({_format_price(ns)}원)")
            if nr is not None:
                dist = (nr - price) / price * 100
                if dist <= 1.0:
                    alerts.append(f"저항선 근접({_format_price(nr)}원)")

    # 극단적 RSI
    if indicators is not None:
        rsi = indicators.get("rsi_14")
        rsi_status = classify_rsi(rsi)
        if rsi_status in ("과매수", "과매도"):
            alerts.append(f"RSI {rsi_status}({rsi:.0f})")

    if alerts:
        lines.append(f"  ⚠️ {' / '.join(alerts)}")

    lines.append("")
    return lines


def _build_watchpoints_section(watchpoints: dict, current_price: float) -> list[str]:
    """핵심 관찰 포인트(Key Watchpoints) 섹션을 생성한다."""
    if watchpoints is None:
        return []

    lines = []
    lines.append("<b>🔭 핵심 관찰 포인트</b>")

    # (1) 지지/저항 시나리오
    sc = watchpoints.get("scenarios", {})
    ns = sc.get("nearest_support")
    nr = sc.get("nearest_resistance")
    if ns is not None or nr is not None:
        lines.append("  <b>시나리오:</b>")
        if ns is not None:
            next_sup = sc.get("next_support")
            if next_sup is not None:
                lines.append(f"  ▼ {_format_price(ns)} 지지 이탈 시 → {_format_price(next_sup)} 주목")
            else:
                lines.append(f"  ▼ 최근접 지지선: {_format_price(ns)}")
        if nr is not None:
            next_res = sc.get("next_resistance")
            if next_res is not None:
                lines.append(f"  ▲ {_format_price(nr)} 저항 돌파 시 → {_format_price(next_res)} 주목")
            else:
                lines.append(f"  ▲ 최근접 저항선: {_format_price(nr)}")

    # (2) ATR 기반 예상 일일 변동 범위
    dr = watchpoints.get("daily_range", {})
    exp_high = dr.get("expected_high")
    exp_low = dr.get("expected_low")
    atr_pct = dr.get("atr_pct")
    if exp_high is not None and exp_low is not None:
        lines.append(f"  <b>예상 범위:</b> {_format_price(exp_low)} ~ {_format_price(exp_high)}"
                     + (f" (ATR {atr_pct:.1f}%)" if atr_pct is not None else ""))

    # (3) 핵심 리스크/기회 요인
    factors = watchpoints.get("factors", [])
    if factors:
        lines.append("  <b>주목 요인:</b>")
        for f in factors:
            emoji = "⚠️" if f["type"] == "risk" else "💡"
            lines.append(f"  {emoji} {f['text']}")

    lines.append("")
    return lines


def _build_timeframe_section(alignment: dict, weekly_ind: dict) -> list[str]:
    """멀티타임프레임 분석 섹션을 생성한다."""
    lines = ["", "<b>🔭 멀티타임프레임 분석</b>"]

    trend = weekly_ind.get("weekly_trend")
    ma5w = weekly_ind.get("ma5w")
    ma13w = weekly_ind.get("ma13w")
    rsi_w = weekly_ind.get("rsi_weekly")
    n_weeks = weekly_ind.get("weekly_data_weeks", 0)

    trend_kr = {"up": "상승 ↑", "down": "하락 ↓", "sideways": "횡보 →"}.get(
        trend or "", "N/A",
    )
    lines.append(f"  주봉 추세: {trend_kr} ({n_weeks}주 데이터)")

    if ma5w is not None and ma13w is not None:
        ma_order = "정배열" if ma5w > ma13w else "역배열" if ma5w < ma13w else "수렴"
        lines.append(f"  MA5w: {_format_price(ma5w)} | MA13w: {_format_price(ma13w)} ({ma_order})")

    if rsi_w is not None:
        lines.append(f"  RSI(주봉): {rsi_w:.1f}")

    label = alignment.get("alignment", "neutral")
    interp = alignment.get("interpretation", "")
    modifier = alignment.get("score_modifier", 0)

    label_kr = {
        "aligned_bullish": "🟢 강세 정합",
        "aligned_bearish": "🔴 약세 정합",
        "divergent_bullish": "🟡 강세 발산",
        "divergent_bearish": "🟡 약세 발산",
        "neutral": "⚪ 중립",
    }.get(label, "⚪ 중립")

    mod_str = f"+{modifier:.1f}" if modifier >= 0 else f"{modifier:.1f}"
    lines.append(f"  일봉-주봉 정합성: {label_kr} (보정: {mod_str})")

    if interp:
        lines.append(f"  → {interp}")

    lines.append("")
    return lines


def _build_pattern_match_section(pm: dict) -> list[str]:
    """유사 패턴 검색 결과 섹션을 생성한다."""
    lines = ["", "<b>🔍 유사 패턴 분석</b>"]
    summary = pm.get("summary", {})
    count = summary.get("match_count", 0)
    if count == 0:
        lines.append("  유사 패턴을 찾지 못했습니다.")
        lines.append("")
        return lines

    lines.append(f"  최근 시그널과 유사한 과거 {count}개 패턴 분석:")
    lines.append("")

    for m in pm.get("matches", [])[:5]:
        sim_pct = m["similarity"] * 100
        fr = m.get("forward_returns", {})
        r1 = fr.get("1d")
        r3 = fr.get("3d")
        r5 = fr.get("5d")
        r1_str = f"{r1:+.1%}" if r1 is not None else "N/A"
        r3_str = f"{r3:+.1%}" if r3 is not None else "N/A"
        r5_str = f"{r5:+.1%}" if r5 is not None else "N/A"
        lines.append(f"  📅 {m['date']} (유사도 {sim_pct:.0f}%)")
        lines.append(f"     이후 수익률: 1일 {r1_str} | 3일 {r3_str} | 5일 {r5_str}")

    lines.append("")
    avg1 = summary.get("avg_return_1d")
    avg3 = summary.get("avg_return_3d")
    avg5 = summary.get("avg_return_5d")
    up1 = summary.get("up_ratio_1d")
    up5 = summary.get("up_ratio_5d")
    if avg1 is not None:
        lines.append(f"  평균: 1일 {avg1:+.1%} | 3일 {avg3:+.1%} | 5일 {avg5:+.1%}" if avg3 is not None and avg5 is not None else f"  평균 1일 수익률: {avg1:+.1%}")
    if up1 is not None and up5 is not None:
        lines.append(f"  상승 확률: 1일 {up1:.0%} | 5일 {up5:.0%}")
    lines.append("")
    return lines


def _build_scenario_section(scenario: dict) -> list[str]:
    """가격 시나리오 분석 섹션을 생성한다."""
    lines = ["", "<b>🎯 가격 시나리오</b>"]
    dominant = scenario.get("dominant_scenario", "기본")
    lines.append(f"  주도 시나리오: <b>{dominant}</b>")
    lines.append("")
    for s in scenario.get("scenarios", []):
        label = s["label"]
        conv = s.get("conviction", "보통")
        trigger = s.get("trigger", "")
        icon = {"상승": "📈", "기본": "📊", "하락": "📉"}.get(label, "•")
        if "target" in s:
            lines.append(f"  {icon} {label} (확신: {conv}): 목표 {_format_price(s['target'])}원")
        elif "range" in s:
            r = s["range"]
            lines.append(f"  {icon} {label} (확신: {conv}): {_format_price(r[0])}~{_format_price(r[1])}원")
        if trigger:
            lines.append(f"     └ {trigger}")
    comment = scenario.get("risk_reward_comment")
    if comment:
        lines.append(f"  ⚖️ {comment}")
    key_level = scenario.get("key_level")
    if key_level is not None:
        lines.append(f"  핵심 가격대: {_format_price(key_level)}원")
    lines.append("")
    return lines


def _build_health_section(health: dict) -> list[str]:
    """데이터 수집 상태 섹션을 생성한다."""
    lines = ["", "<b>📡 데이터 상태</b>"]
    ok = health["ok"]
    total = health["total"]
    lines.append(f"정상 수집: {ok}/{total}")

    failed = health.get("failed_sources", [])
    if failed:
        lines.append(f"⚠️ 수집 실패: {', '.join(failed)}")

    stale = health.get("stale_sources", [])
    if stale:
        lines.append(f"⏰ 데이터 미갱신: {', '.join(stale)}")

    if not failed and not stale:
        lines.append("✅ 모든 데이터 정상")

    lines.append("")
    return lines


def generate_daily_report(
    indicators: dict,
    supply_demand: dict | None = None,
    exchange_rate: dict | None = None,
    composite_signal: dict | None = None,
    support_resistance: dict | None = None,
    accuracy_summary: dict | None = None,
    relative_strength: dict | None = None,
    trend_reversal: dict | None = None,
    signal_trend: dict | None = None,
    fundamentals: dict | None = None,
    news_sentiment: dict | None = None,
    news_headlines: list[dict] | None = None,
    consensus: dict | None = None,
    weekly_summary: dict | None = None,
    rel_perf: dict | None = None,
    sox_trend: dict | None = None,
    semiconductor_momentum: int | None = None,
    volatility: dict | None = None,
    candlestick: dict | None = None,
    watchpoints: dict | None = None,
    convergence: dict | None = None,
    nasdaq_trend: dict | None = None,
    vix_risk: dict | None = None,
    global_macro_score: int | None = None,
    timeframe_alignment: dict | None = None,
    weekly_indicators: dict | None = None,
    scenario: dict | None = None,
    pattern_match: dict | None = None,
    data_health: dict | None = None,
    daily_delta: dict | None = None,
) -> str:
    """기술적 지표 dict를 HTML 텔레그램 메시지로 변환한다.

    Args:
        indicators: compute_technical_indicators()의 반환값.
        supply_demand: analyze_supply_demand()의 반환값 (선택).
        exchange_rate: analyze_exchange_rate()의 반환값 (선택).

    Returns:
        HTML 형식 문자열 (Telegram HTML parse_mode용).
    """
    date = indicators["current_date"]
    price = indicators["current_price"]
    change_1d = indicators.get("change_1d_pct")
    change_5d = indicators.get("change_5d_pct")
    change_20d = indicators.get("change_20d_pct")

    rsi_14 = indicators.get("rsi_14")

    macd = indicators.get("macd")
    macd_signal = indicators.get("macd_signal")
    macd_histogram = indicators.get("macd_histogram")

    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")
    bb_width = indicators.get("bb_width")
    bb_pctb = indicators.get("bb_pctb")

    ma_alignment = classify_ma_alignment(indicators)
    volume_status = assess_volume(indicators.get("volume_ratio_5d"))
    rsi_status = classify_rsi(rsi_14)
    macd_cross = classify_macd(macd, macd_signal, macd_histogram)
    bb_position = classify_bb_position(bb_pctb)
    temperature = assess_market_temperature(
        change_1d, ma_alignment, volume_status, rsi_14=rsi_14, macd_cross=macd_cross,
        bb_pctb=bb_pctb,
    )

    lines = []

    # 헤더
    lines.append(f"<b>📊 삼성전자 일일 리포트</b>")
    lines.append(f"<b>{date}</b>")
    lines.append("")

    # 0) 핵심 요약 (Executive Summary) — 최상단
    lines.extend(_build_executive_summary(
        composite_signal=composite_signal,
        signal_trend=signal_trend,
        indicators=indicators,
        support_resistance=support_resistance,
        trend_reversal=trend_reversal,
    ))

    # 0.02) 오늘의 변화 (Executive Summary 바로 아래)
    if daily_delta is not None:
        lines.extend(_build_daily_delta_section(daily_delta))
        lines.append("")

    # 0.05) 핵심 관찰 포인트
    if watchpoints is not None:
        lines.extend(_build_watchpoints_section(watchpoints, price))

    # 0.1) 종합 투자 시그널
    if composite_signal is not None:
        lines.extend(_build_composite_signal_section(composite_signal))

    # 0.2) 가격 시나리오
    if scenario is not None:
        lines.extend(_build_scenario_section(scenario))

    # 0.25) 유사 패턴 분석
    if pattern_match is not None:
        lines.extend(_build_pattern_match_section(pattern_match))

    # 0.3) 시그널 추이 (종합 시그널 바로 아래)
    if signal_trend is not None:
        lines.extend(_build_signal_trend_section(signal_trend))

    # 0.4) 주간 추이 요약 (시그널 추이 아래)
    if weekly_summary is not None:
        lines.extend(_build_weekly_summary_section(weekly_summary))
        lines.append("")

    # 0.5) 자연어 마켓 코멘터리 (종합 판정 바로 아래)
    from src.analysis.commentary import generate_commentary
    commentary = generate_commentary(
        indicators, supply_demand, exchange_rate, composite_signal, support_resistance,
        relative_strength, trend_reversal=trend_reversal, signal_trend=signal_trend,
        fundamentals=fundamentals, news_sentiment=news_sentiment, consensus=consensus,
        weekly_summary=weekly_summary, rel_perf=rel_perf, sox_trend=sox_trend,
        semiconductor_momentum=semiconductor_momentum, volatility=volatility,
        candlestick=candlestick, convergence=convergence,
        nasdaq_trend=nasdaq_trend, vix_risk=vix_risk,
        timeframe_alignment=timeframe_alignment,
        weekly_indicators=weekly_indicators,
        scenario=scenario,
        pattern_match=pattern_match,
        daily_delta=daily_delta,
    )
    if commentary:
        lines.append(f"💬 {commentary}")
        lines.append("")

    # 1) 현재가 및 등락
    lines.append(f"<b>현재가:</b> {_format_price(price)}원 ({_format_change(change_1d)})")
    lines.append(f"  5일: {_format_change(change_5d)} | 20일: {_format_change(change_20d)}")
    lines.append("")

    # 2) 이동평균선 해석
    lines.append(f"<b>이동평균선:</b> {ma_alignment}")
    ma5 = indicators.get("ma5")
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    if ma5 is not None:
        lines.append(f"  MA5: {_format_price(ma5)} | MA20: {_format_price(ma20) if ma20 else 'N/A'} | MA60: {_format_price(ma60) if ma60 else 'N/A'}")
    lines.append("")

    # 3) 거래량
    vol_ratio = indicators.get("volume_ratio_5d")
    vol_text = f"{vol_ratio:.1f}x" if vol_ratio is not None else "N/A"
    vol_label = volume_status or "N/A"
    lines.append(f"<b>거래량(5일비):</b> {vol_text} ({vol_label}) {_volume_emoji(volume_status)}")
    lines.append("")

    # 4) RSI
    if rsi_14 is not None:
        rsi_emoji = "🔴" if rsi_status == "과매수" else "🟢" if rsi_status == "과매도" else ""
        lines.append(f"<b>RSI(14):</b> {rsi_14:.1f} ({rsi_status}) {rsi_emoji}".rstrip())
        lines.append("")

    # 4.5) 스토캐스틱 오실레이터
    stoch_k = indicators.get("stoch_k")
    stoch_d = indicators.get("stoch_d")
    if stoch_k is not None:
        stoch_status = classify_stochastic(stoch_k, stoch_d)
        stoch_emoji = "🔴" if stoch_status == "과매수" else "🟢" if stoch_status == "과매도" else ""
        d_str = f" / %D: {stoch_d:.1f}" if stoch_d is not None else ""
        lines.append(f"<b>Stoch(14,3):</b> %K {stoch_k:.1f}{d_str} ({stoch_status}) {stoch_emoji}".rstrip())
        lines.append("")

    # 5) MACD
    if macd is not None:
        macd_emoji = "🟢" if macd_cross == "골든크로스" else "🔴" if macd_cross == "데드크로스" else ""
        hist_dir = _histogram_direction(macd_histogram)
        lines.append(f"<b>MACD(12,26,9):</b> {macd:.1f} / 시그널: {macd_signal:.1f}" if macd_signal is not None else f"<b>MACD(12,26,9):</b> {macd:.1f} / 시그널: N/A")
        if macd_signal is not None:
            lines.append(f"  크로스: {macd_cross} {macd_emoji} | 히스토그램: {macd_histogram:.1f} ({hist_dir})")
        lines.append("")

    # 6) 볼린저 밴드
    if bb_pctb is not None:
        bb_emoji = "🔴" if bb_position == "상단 돌파" else "🟢" if bb_position == "하단 이탈" else ""
        lines.append(f"<b>BB(20,2):</b> %B {bb_pctb:.2f} ({bb_position}) {bb_emoji}".rstrip())
        if bb_width is not None:
            lines.append(f"  밴드폭: {bb_width:.3f} | 상단: {_format_price(bb_upper)} | 하단: {_format_price(bb_lower)}")
        lines.append("")

    # 6.5) ADX 추세 강도
    adx_val = indicators.get("adx")
    if adx_val is not None:
        plus_di = indicators.get("plus_di")
        minus_di = indicators.get("minus_di")
        if adx_val > 25:
            adx_grade = "강한 추세"
            adx_emoji = "💪"
        elif adx_val >= 20:
            adx_grade = "약한 추세"
            adx_emoji = "〰️"
        else:
            adx_grade = "추세 부재"
            adx_emoji = "😶"
        lines.append(f"<b>ADX(14):</b> {adx_val:.1f} ({adx_grade}) {adx_emoji}")
        di_parts = []
        if plus_di is not None:
            di_parts.append(f"+DI: {plus_di:.1f}")
        if minus_di is not None:
            di_parts.append(f"-DI: {minus_di:.1f}")
        if di_parts:
            lines.append(f"  {' | '.join(di_parts)}")
        lines.append("")

    # 7) OBV 다이버전스 경고
    obv_div = indicators.get("obv_divergence")
    if obv_div == "bearish":
        lines.append("<b>⚠️ 가격-거래량 괴리:</b> 가격은 상승 중이나 거래량이 동반되지 않음 (OBV 하락)")
        lines.append("")
    elif obv_div == "bullish":
        lines.append("<b>💡 거래량 선행 신호:</b> 가격은 하락 중이나 거래량 흐름은 반등 조짐 (OBV 상승)")
        lines.append("")

    # 8) 종합 시장 온도
    lines.append(f"<b>시장 온도:</b> {_temp_emoji(temperature)} {temperature}")

    # 환율 동향 (선택)
    if exchange_rate is not None:
        lines.extend(_build_exchange_rate_section(exchange_rate))

    # 수급 동향 (선택)
    if supply_demand is not None:
        lines.extend(_build_supply_demand_section(supply_demand))

    # 상대강도 (선택)
    if relative_strength is not None:
        lines.extend(_build_relative_strength_section(relative_strength))

    # 추세 전환 감지 (선택)
    if trend_reversal is not None:
        lines.extend(_build_trend_reversal_section(trend_reversal))

    # 멀티타임프레임 분석 (선택)
    if timeframe_alignment is not None and weekly_indicators is not None:
        lines.extend(_build_timeframe_section(timeframe_alignment, weekly_indicators))

    # 펀더멘털 분석 (선택)
    if fundamentals is not None:
        lines.extend(_build_fundamentals_section(fundamentals))

    # 뉴스 심리 (선택)
    if news_sentiment is not None:
        lines.extend(_build_news_sentiment_section(news_sentiment, news_headlines))

    # 캔들스틱 패턴 (선택)
    if candlestick is not None:
        lines.extend(_build_candlestick_section(candlestick))

    # 변동성 분석 (선택)
    if volatility is not None:
        lines.extend(_build_volatility_section(volatility))

    # 반도체 업황 (선택)
    if rel_perf is not None and sox_trend is not None and semiconductor_momentum is not None:
        lines.extend(_build_semiconductor_section(rel_perf, sox_trend, semiconductor_momentum))

    # 글로벌 매크로 (선택)
    if nasdaq_trend is not None and vix_risk is not None and global_macro_score is not None:
        lines.extend(_build_global_macro_section(nasdaq_trend, vix_risk, global_macro_score))

    # 수렴 분석 (선택)
    if convergence is not None:
        lines.extend(_build_convergence_section(convergence))

    # 증권사 컨센서스 (선택)
    if consensus is not None:
        lines.extend(_build_consensus_section(consensus))

    # 지지/저항선 (선택)
    if support_resistance is not None:
        lines.extend(_build_support_resistance_section(support_resistance, price))

    # 시그널 정확도 (선택)
    if accuracy_summary is not None:
        lines.extend(_build_accuracy_section(accuracy_summary, composite_signal))

    # 데이터 상태 (선택)
    if data_health is not None:
        lines.extend(_build_health_section(data_health))

    return "\n".join(lines)
