"""멀티타임프레임 분석 모듈.

일봉 OHLCV 데이터를 주봉으로 리샘플링하여
주간 추세(MA5w/MA13w, RSI_weekly, 주봉 추세방향)를 산출한다.
일봉-주봉 시그널 정합성(alignment)을 판정하여
"숲을 보는" 멀티타임프레임 맥락을 제공한다.
"""

import datetime


def resample_daily_to_weekly(rows: list[dict]) -> list[dict]:
    """일봉 OHLCV를 주봉으로 리샘플링한다.

    Args:
        rows: 일봉 OHLCV dicts (날짜 오름차순).
              각 dict: {date, open, high, low, close, volume}

    Returns:
        주봉 OHLCV list[dict]. date는 해당 주 월요일 ISO 날짜.
    """
    if not rows:
        return []

    weeks: dict[str, list[dict]] = {}
    for row in rows:
        dt = datetime.date.fromisoformat(row["date"])
        # ISO 주의 월요일을 키로 사용
        monday = dt - datetime.timedelta(days=dt.weekday())
        key = monday.isoformat()
        if key not in weeks:
            weeks[key] = []
        weeks[key].append(row)

    result = []
    for monday_str in sorted(weeks):
        week_rows = weeks[monday_str]
        result.append({
            "date": monday_str,
            "open": week_rows[0]["open"],
            "high": max(r["high"] for r in week_rows),
            "low": min(r["low"] for r in week_rows),
            "close": week_rows[-1]["close"],
            "volume": sum(r["volume"] for r in week_rows),
        })
    return result


def _ma(values: list[float], window: int) -> float | None:
    """단순이동평균. 데이터 부족 시 None."""
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def _rsi(closes: list[float], period: int = 14) -> float | None:
    """Wilder RSI. 데이터가 period+1개 미만이면 None."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0 for d in deltas[:period]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    for d in deltas[period:]:
        avg_gain = (avg_gain * (period - 1) + (d if d > 0 else 0)) / period
        avg_loss = (avg_loss * (period - 1) + (-d if d < 0 else 0)) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _weekly_trend(closes: list[float], ma5: float | None,
                  ma13: float | None) -> str | None:
    """주봉 추세 방향을 판정한다.

    - MA5w > MA13w 이고 현재가 > MA5w → 'up'
    - MA5w < MA13w 이고 현재가 < MA5w → 'down'
    - 그 외 → 'sideways'
    - MA 계산 불가 시 None
    """
    if ma5 is None or ma13 is None or not closes:
        return None
    current = closes[-1]
    if ma5 > ma13 and current > ma5:
        return "up"
    if ma5 < ma13 and current < ma5:
        return "down"
    return "sideways"


def compute_weekly_indicators(daily_rows: list[dict]) -> dict:
    """일봉 데이터로부터 주봉 지표를 계산한다.

    Args:
        daily_rows: 일봉 OHLCV (날짜 오름차순, 최소 60일 권장).

    Returns:
        dict with: ma5w, ma13w, rsi_weekly, weekly_trend,
                   weekly_close, weekly_data_weeks
    """
    if not daily_rows:
        return {
            "ma5w": None,
            "ma13w": None,
            "rsi_weekly": None,
            "weekly_trend": None,
            "weekly_close": None,
            "weekly_data_weeks": 0,
        }

    weekly = resample_daily_to_weekly(daily_rows)
    closes = [w["close"] for w in weekly]
    n_weeks = len(closes)

    ma5w = _ma(closes, 5)
    ma13w = _ma(closes, 13)
    rsi_weekly = _rsi(closes, 14)
    trend = _weekly_trend(closes, ma5w, ma13w)

    return {
        "ma5w": ma5w,
        "ma13w": ma13w,
        "rsi_weekly": rsi_weekly,
        "weekly_trend": trend,
        "weekly_close": closes[-1] if closes else None,
        "weekly_data_weeks": n_weeks,
    }


def assess_timeframe_alignment(
    weekly_trend: str | None,
    weekly_rsi: float | None,
    daily_rsi: float | None,
) -> dict:
    """일봉-주봉 시그널 정합성을 판정한다.

    Args:
        weekly_trend: 'up', 'down', 'sideways', or None
        weekly_rsi: 주봉 RSI (0-100) or None
        daily_rsi: 일봉 RSI (0-100) or None

    Returns:
        dict with: alignment, interpretation, score_modifier
        - alignment: 'aligned_bullish', 'aligned_bearish',
                     'divergent_bullish', 'divergent_bearish', 'neutral'
        - interpretation: 한국어 해석 문자열
        - score_modifier: 종합 시그널 스코어 보정치 (-0.5 ~ +0.5)
    """
    if weekly_trend is None or weekly_rsi is None or daily_rsi is None:
        return {
            "alignment": "neutral",
            "interpretation": "데이터 부족으로 멀티타임프레임 판정 불가",
            "score_modifier": 0.0,
        }

    OVERSOLD = 30
    OVERBOUGHT = 70

    # 주봉 상승 추세
    if weekly_trend == "up":
        if daily_rsi < OVERSOLD:
            return {
                "alignment": "aligned_bullish",
                "interpretation": (
                    "주봉 상승 추세에서 일봉 과매도 — "
                    "매수 기회 가능성 (추세 방향 조정 매수)"
                ),
                "score_modifier": 0.5,
            }
        return {
            "alignment": "divergent_bullish",
            "interpretation": (
                "주봉 상승 추세 유지 — 단기 조정 시 지지 기대"
            ),
            "score_modifier": 0.2,
        }

    # 주봉 하락 추세
    if weekly_trend == "down":
        if daily_rsi > OVERBOUGHT:
            return {
                "alignment": "aligned_bearish",
                "interpretation": (
                    "주봉 하락 추세에서 일봉 과매수 — "
                    "추가 하락 경계 (반등 매도 구간)"
                ),
                "score_modifier": -0.5,
            }
        return {
            "alignment": "divergent_bearish",
            "interpretation": (
                "주봉 하락 추세 지속 — 반등 시에도 저항 예상"
            ),
            "score_modifier": -0.2,
        }

    # sideways
    return {
        "alignment": "neutral",
        "interpretation": "주봉 횡보 구간 — 방향성 확인 후 대응 권장",
        "score_modifier": 0.0,
    }
