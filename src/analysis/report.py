"""일일 분석 리포트 생성기.

compute_technical_indicators 결과를 투자자가 읽기 좋은
HTML 텔레그램 메시지로 변환한다.
"""


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


def generate_daily_report(
    indicators: dict,
    supply_demand: dict | None = None,
    exchange_rate: dict | None = None,
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

    # 7) 종합 시장 온도
    lines.append(f"<b>시장 온도:</b> {_temp_emoji(temperature)} {temperature}")

    # 환율 동향 (선택)
    if exchange_rate is not None:
        lines.extend(_build_exchange_rate_section(exchange_rate))

    # 수급 동향 (선택)
    if supply_demand is not None:
        lines.extend(_build_supply_demand_section(supply_demand))

    return "\n".join(lines)
