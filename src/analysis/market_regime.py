"""시장 체제(Market Regime) 인식 모듈.

현재 시장이 추세장/횡보장인지, 강세/약세 국면인지를 자동 판별한다.
ADX, 이동평균 배열, 볼린저 밴드, 거래량을 종합하여 체제를 분류한다.
"""

from src.analysis.technical import (
    _adx,
    _bollinger_bands,
    _ma,
)
from src.data.database import get_prices

_MIN_ROWS = 60


def _ma_alignment(closes: list[float]) -> str:
    """MA5 > MA20 > MA60 정배열/역배열/혼조 판별."""
    ma5 = _ma(closes, 5)
    ma20 = _ma(closes, 20)
    ma60 = _ma(closes, 60)
    if ma5 is None or ma20 is None or ma60 is None:
        return "unknown"
    if ma5 > ma20 > ma60:
        return "bullish"
    if ma5 < ma20 < ma60:
        return "bearish"
    return "mixed"


def _estimate_regime_duration(closes: list[float], regime: str) -> int:
    """현 체제 지속 추정 일수 — MA5/MA20 관계 연속 유지 일수로 근사."""
    if len(closes) < 20:
        return 1
    duration = 0
    for i in range(len(closes) - 1, 19, -1):
        segment = closes[: i + 1]
        ma5 = _ma(segment, 5)
        ma20 = _ma(segment, 20)
        if ma5 is None or ma20 is None:
            break
        if regime in ("trending_up", "breakout") and ma5 > ma20:
            duration += 1
        elif regime in ("trending_down", "breakdown") and ma5 < ma20:
            duration += 1
        elif regime == "range_bound" and abs(ma5 - ma20) / ma20 < 0.01:
            duration += 1
        else:
            break
    return max(duration, 1)


def _detect_regime(
    adx: float | None,
    alignment: str,
    bb_pctb: float | None,
    adx_rising: bool,
    volume_surge: bool,
) -> str:
    adx_val = adx if adx is not None else 0.0
    pctb = bb_pctb if bb_pctb is not None else 0.5

    if pctb > 1.0 and (adx_rising or volume_surge) and adx_val >= 20:
        return "breakout"
    if pctb < 0.0 and (adx_rising or volume_surge) and adx_val >= 20:
        return "breakdown"

    if adx_val >= 25:
        if alignment == "bullish":
            return "trending_up"
        if alignment == "bearish":
            return "trending_down"

    if adx_val < 20 or alignment == "mixed":
        return "range_bound"

    if alignment == "bullish":
        return "trending_up"
    if alignment == "bearish":
        return "trending_down"
    return "range_bound"


def _detect_phase(
    regime: str,
    volume_trend: float,
    price_momentum: float,
) -> str:
    if regime == "trending_up":
        return "markup"
    if regime == "trending_down":
        return "markdown"
    if regime == "breakout":
        return "markup"
    if regime == "breakdown":
        return "markdown"
    # range_bound
    if volume_trend > 1.2 and price_momentum > 0:
        return "accumulation"
    if volume_trend < 0.8 and price_momentum < 0:
        return "distribution"
    if price_momentum >= 0:
        return "accumulation"
    return "distribution"


def _calc_confidence(
    adx: float | None,
    alignment: str,
    regime: str,
    bb_pctb: float | None,
) -> int:
    score = 0.0
    adx_val = adx if adx is not None else 0.0

    # ADX 기여 (0~40점)
    if regime in ("trending_up", "trending_down"):
        score += min(adx_val / 50 * 40, 40)
    elif regime == "range_bound":
        score += max(0, (30 - adx_val)) / 30 * 40
    else:  # breakout/breakdown
        score += min(adx_val / 40 * 30, 30)

    # MA 정합성 (0~30점)
    if regime in ("trending_up", "breakout") and alignment == "bullish":
        score += 30
    elif regime in ("trending_down", "breakdown") and alignment == "bearish":
        score += 30
    elif regime == "range_bound" and alignment == "mixed":
        score += 30
    elif alignment != "unknown":
        score += 10

    # BB 위치 일관성 (0~30점)
    if bb_pctb is not None:
        if regime in ("trending_up", "breakout") and bb_pctb > 0.5:
            score += 30 * min(bb_pctb, 1.5) / 1.5
        elif regime in ("trending_down", "breakdown") and bb_pctb < 0.5:
            score += 30 * (1 - max(bb_pctb, -0.5) / 0.5) / 2
        elif regime == "range_bound" and 0.2 <= bb_pctb <= 0.8:
            score += 25

    return max(0, min(100, int(score)))


def _interpretation_hints(regime: str) -> dict:
    if regime in ("trending_up", "trending_down"):
        return {
            "rsi_thresholds": {"overbought": 80, "oversold": 20},
            "support_resistance_reliability": "low",
            "volume_confirmation_importance": "medium",
            "description": "추세장 — RSI 기준 완화, 지지/저항 신뢰도 하향",
        }
    if regime == "range_bound":
        return {
            "rsi_thresholds": {"overbought": 70, "oversold": 30},
            "support_resistance_reliability": "high",
            "volume_confirmation_importance": "medium",
            "description": "횡보장 — RSI 기준 유지, 지지/저항 신뢰도 상향",
        }
    # breakout / breakdown
    return {
        "rsi_thresholds": {"overbought": 80, "oversold": 20},
        "support_resistance_reliability": "low",
        "volume_confirmation_importance": "high",
        "description": "돌파장 — 거래량 확인 중요도 상향, 추세 추종 우선",
    }


def compute_market_regime() -> dict | None:
    """시장 체제를 판별한다.

    Returns:
        dict with regime, phase, confidence, duration, interpretation_hints.
        데이터 부족 시 None.
    """
    rows = get_prices(90)
    if len(rows) < _MIN_ROWS:
        return None

    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    volumes = [r["volume"] for r in rows]

    adx_val, plus_di, minus_di = _adx(highs, lows, closes)
    _, _, _, bb_pctb = _bollinger_bands(closes)
    alignment = _ma_alignment(closes)

    # ADX 상승 여부 (이전 5일 대비)
    adx_rising = False
    if len(closes) > 35:
        adx_prev, _, _ = _adx(highs[:-5], lows[:-5], closes[:-5])
        if adx_val is not None and adx_prev is not None:
            adx_rising = adx_val > adx_prev

    # 거래량 급등 여부
    vol_avg_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 1
    volume_surge = volumes[-1] > vol_avg_20 * 1.5 if vol_avg_20 > 0 else False

    regime = _detect_regime(adx_val, alignment, bb_pctb, adx_rising, volume_surge)

    # 가격 모멘텀 (5일 변화율)
    price_momentum = (closes[-1] - closes[-6]) / closes[-6] if len(closes) >= 6 else 0.0
    vol_trend = volumes[-1] / vol_avg_20 if vol_avg_20 > 0 else 1.0

    phase = _detect_phase(regime, vol_trend, price_momentum)
    confidence = _calc_confidence(adx_val, alignment, regime, bb_pctb)
    duration = _estimate_regime_duration(closes, regime)

    return {
        "regime": regime,
        "phase": phase,
        "confidence": confidence,
        "duration": duration,
        "interpretation_hints": _interpretation_hints(regime),
        "adx": adx_val,
        "ma_alignment": alignment,
        "bb_pctb": bb_pctb,
    }
