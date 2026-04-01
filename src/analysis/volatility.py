"""변동성 분석 모듈.

ATR(14), 역사적 변동성(HV20), 변동성 백분위, 변동성 체제, 볼린저 밴드폭 수축 감지.
"""

import math


def _true_ranges(rows: list[dict]) -> list[float]:
    """True Range 시리즈를 계산한다. 첫 번째 행은 H-L로 처리."""
    trs: list[float] = []
    for i, r in enumerate(rows):
        hl = r["high"] - r["low"]
        if i == 0:
            trs.append(hl)
        else:
            prev_c = rows[i - 1]["close"]
            trs.append(max(hl, abs(r["high"] - prev_c), abs(prev_c - r["low"])))
    return trs


def _atr(trs: list[float], period: int = 14) -> list[float]:
    """ATR 시리즈를 계산한다 (Wilder 평활). period 미만이면 빈 리스트."""
    if len(trs) < period:
        return []
    atr_vals = [sum(trs[:period]) / period]
    for i in range(period, len(trs)):
        atr_vals.append((atr_vals[-1] * (period - 1) + trs[i]) / period)
    return atr_vals


def _hv(closes: list[float], window: int = 20) -> float | None:
    """역사적 변동성: window일 로그수익률 표준편차를 연율화."""
    if len(closes) < window + 1:
        return None
    log_returns = [
        math.log(closes[i] / closes[i - 1])
        for i in range(len(closes) - window, len(closes))
        if closes[i - 1] > 0
    ]
    if len(log_returns) < window:
        return None
    mean = sum(log_returns) / len(log_returns)
    variance = sum((r - mean) ** 2 for r in log_returns) / len(log_returns)
    return math.sqrt(variance) * math.sqrt(252)


def _bollinger_bandwidth(closes: list[float], window: int = 20) -> list[float]:
    """볼린저 밴드폭 시리즈를 반환한다."""
    bws: list[float] = []
    for i in range(window - 1, len(closes)):
        segment = closes[i - window + 1:i + 1]
        middle = sum(segment) / window
        if middle == 0:
            bws.append(0.0)
            continue
        variance = sum((p - middle) ** 2 for p in segment) / window
        std = math.sqrt(variance)
        upper = middle + 2 * std
        lower = middle - 2 * std
        bws.append((upper - lower) / middle)
    return bws


def compute_volatility(rows: list[dict]) -> dict:
    """OHLCV rows로부터 변동성 지표를 계산한다.

    Args:
        rows: DB에서 가져온 OHLCV dicts (날짜 오름차순).
              각 dict: {date, open, high, low, close, volume}

    Returns:
        dict: atr, atr_pct, hv20, volatility_percentile, volatility_regime, bandwidth_squeeze

    Raises:
        ValueError: rows가 비어있을 때.
    """
    if not rows:
        raise ValueError("OHLCV 데이터가 비어있습니다.")

    closes = [r["close"] for r in rows]
    current = closes[-1]

    # ATR(14)
    trs = _true_ranges(rows)
    atr_series = _atr(trs, 14)
    atr_val = atr_series[-1] if atr_series else None
    atr_pct = (atr_val / current * 100) if atr_val is not None and current != 0 else None

    # HV20
    hv20 = _hv(closes, 20)

    # 변동성 백분위 (현재 ATR이 최근 60일 ATR 분포에서 몇 번째인지)
    vol_percentile: float | None = None
    vol_regime: str | None = None
    if len(atr_series) >= 60:
        recent_atrs = atr_series[-60:]
        current_atr = atr_series[-1]
        count_below = sum(1 for a in recent_atrs if a < current_atr)
        vol_percentile = count_below / len(recent_atrs) * 100

        # 변동성 체제
        if vol_percentile >= 80:
            vol_regime = "고변동성"
        elif vol_percentile <= 20:
            vol_regime = "저변동성"
        else:
            vol_regime = "보통"

    # 볼린저 밴드폭 수축 감지
    bw_squeeze: bool | None = None
    bw_series = _bollinger_bandwidth(closes, 20)
    if len(bw_series) >= 60:
        recent_bws = bw_series[-60:]
        current_bw = bw_series[-1]
        count_below = sum(1 for b in recent_bws if b < current_bw)
        bw_percentile = count_below / len(recent_bws) * 100
        bw_squeeze = bw_percentile <= 20

    return {
        "atr": atr_val,
        "atr_pct": atr_pct,
        "hv20": hv20,
        "volatility_percentile": vol_percentile,
        "volatility_regime": vol_regime,
        "bandwidth_squeeze": bw_squeeze,
    }
