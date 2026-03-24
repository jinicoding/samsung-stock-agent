"""기초 기술적 분석 지표 계산 모듈.

DB에서 가져온 OHLCV rows (list[dict])를 입력받아
이동평균, 가격 변동률, 거래량 변화율 등 기초 지표를 계산한다.
"""


def _ma(closes: list[float], window: int) -> float | None:
    """최근 window일 단순이동평균. 데이터 부족 시 None."""
    if len(closes) < window:
        return None
    return sum(closes[-window:]) / window


def _pct_change(old: float, new: float) -> float:
    """변동률(%)."""
    return (new - old) / old * 100


def _rsi(closes: list[float], period: int = 14) -> float | None:
    """Wilder 방식 RSI 계산. 데이터가 period+1개 미만이면 None."""
    if len(closes) < period + 1:
        return None

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    # 첫 period일의 평균 상승/하락폭
    gains = [d if d > 0 else 0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0 for d in deltas[:period]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Wilder 평활 이동평균
    for d in deltas[period:]:
        avg_gain = (avg_gain * (period - 1) + (d if d > 0 else 0)) / period
        avg_loss = (avg_loss * (period - 1) + (-d if d < 0 else 0)) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _ema(closes: list[float], window: int) -> list[float]:
    """지수이동평균(EMA) 전체 시리즈를 반환한다.

    첫 window일은 SMA로 시작하고, 이후 EMA를 적용한다.
    데이터가 window 미만이면 빈 리스트를 반환한다.
    """
    if len(closes) < window:
        return []
    k = 2 / (window + 1)
    ema_values = [0.0] * len(closes)
    # 첫 SMA
    ema_values[window - 1] = sum(closes[:window]) / window
    for i in range(window, len(closes)):
        ema_values[i] = closes[i] * k + ema_values[i - 1] * (1 - k)
    # window 이전 값은 의미 없으므로 그대로 두되, 전체 길이를 반환
    return ema_values


def _macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[float | None, float | None, float | None]:
    """MACD 라인, 시그널 라인, 히스토그램의 최신 값을 반환한다.

    Returns:
        (macd_line, signal_line, histogram) — 데이터 부족 시 (None, None, None).
    """
    if len(closes) < slow:
        return None, None, None

    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)

    # MACD 라인 = EMA_fast - EMA_slow (slow-1 인덱스부터 유효)
    macd_series = [
        ema_fast[i] - ema_slow[i]
        for i in range(slow - 1, len(closes))
    ]

    macd_line = macd_series[-1]

    # 시그널 라인 = MACD 시리즈의 EMA(signal)
    if len(macd_series) < signal:
        return macd_line, None, None

    signal_ema = _ema(macd_series, signal)
    signal_line = signal_ema[-1]
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def _bollinger_bands(
    closes: list[float], window: int = 20, num_std: int = 2,
) -> tuple[float | None, float | None, float | None, float | None]:
    """볼린저 밴드를 계산한다.

    Returns:
        (upper, lower, width, pctb) — 데이터 부족 시 (None, None, None, None).
        width = (upper - lower) / middle
        pctb = (close - lower) / (upper - lower)  — 0~1이 밴드 내, >1 상단돌파, <0 하단이탈
    """
    if len(closes) < window:
        return None, None, None, None

    recent = closes[-window:]
    middle = sum(recent) / window
    variance = sum((p - middle) ** 2 for p in recent) / window
    std = variance ** 0.5

    upper = middle + num_std * std
    lower = middle - num_std * std
    width = (upper - lower) / middle if middle != 0 else 0.0

    band_range = upper - lower
    if band_range == 0:
        pctb = 0.5  # σ=0일 때 (모든 값 동일) → 중앙
    else:
        pctb = (closes[-1] - lower) / band_range

    return upper, lower, width, pctb


def compute_technical_indicators(rows: list[dict]) -> dict:
    """OHLCV rows로부터 기초 기술적 지표를 계산한다.

    Args:
        rows: DB에서 가져온 OHLCV dicts (날짜 오름차순).
              각 dict: {date, open, high, low, close, volume}

    Returns:
        dict with computed indicators.

    Raises:
        ValueError: rows가 비어있을 때.
    """
    if not rows:
        raise ValueError("OHLCV 데이터가 비어있습니다.")

    closes = [r["close"] for r in rows]
    volumes = [r["volume"] for r in rows]
    current = closes[-1]
    n = len(closes)

    # 이동평균선
    ma5 = _ma(closes, 5)
    ma20 = _ma(closes, 20)
    ma60 = _ma(closes, 60)

    # 이동평균 대비 현재가 위치 (%)
    def vs_ma(ma_val: float | None) -> float | None:
        if ma_val is None:
            return None
        return _pct_change(ma_val, current)

    # 가격 변동률
    def change_nd(days: int) -> float | None:
        if n <= days:
            return None
        return _pct_change(closes[-(days + 1)], current)

    # 거래량 변화율 (5일 평균 대비 당일)
    volume_ratio: float | None = None
    if n >= 6:
        avg_vol_5d = sum(volumes[-6:-1]) / 5
        if avg_vol_5d > 0:
            volume_ratio = volumes[-1] / avg_vol_5d

    # MACD (12, 26, 9)
    macd_line, macd_signal, macd_histogram = _macd(closes)

    # 볼린저 밴드 (20, 2)
    bb_upper, bb_lower, bb_width, bb_pctb = _bollinger_bands(closes)

    return {
        "current_date": rows[-1]["date"],
        "current_price": current,
        # 이동평균선
        "ma5": ma5,
        "ma20": ma20,
        "ma60": ma60,
        # 이동평균 대비 괴리율 (%)
        "price_vs_ma5_pct": vs_ma(ma5),
        "price_vs_ma20_pct": vs_ma(ma20),
        "price_vs_ma60_pct": vs_ma(ma60),
        # 가격 변동률 (%)
        "change_1d_pct": change_nd(1),
        "change_5d_pct": change_nd(5),
        "change_20d_pct": change_nd(20),
        # 거래량 변화율
        "volume_ratio_5d": volume_ratio,
        # RSI (14일)
        "rsi_14": _rsi(closes, 14),
        # MACD (12, 26, 9)
        "macd": macd_line,
        "macd_signal": macd_signal,
        "macd_histogram": macd_histogram,
        # 볼린저 밴드 (20, 2)
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "bb_width": bb_width,
        "bb_pctb": bb_pctb,
    }
