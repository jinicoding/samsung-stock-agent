"""반도체 업황 분석: 삼성전자 vs SK하이닉스 상대성과, SOX 추세, 모멘텀 스코어.

삼성전자의 메모리 반도체 사업 환경을 정량적으로 평가한다.
"""


def _return_pct(prices: list[float], n: int) -> float | None:
    """최근 n일 수익률(%). 데이터 부족 시 None."""
    if len(prices) <= n:
        return None
    return (prices[-1] / prices[-1 - n] - 1) * 100


def _simple_ma(values: list[float], period: int) -> float | None:
    """마지막 period개의 단순이동평균. 부족 시 None."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def compute_relative_performance(
    samsung_closes: list[float],
    hynix_closes: list[float],
) -> dict | None:
    """삼성전자 vs SK하이닉스 상대 성과를 분석한다.

    Args:
        samsung_closes: 삼성전자 종가 배열 (날짜 오름차순).
        hynix_closes: SK하이닉스 종가 배열 (같은 길이, 날짜 오름차순).

    Returns:
        분석 결과 dict. 데이터 부족(2개 미만) 또는 길이 불일치 시 None.
    """
    if len(samsung_closes) < 2 or len(hynix_closes) < 2:
        return None
    if len(samsung_closes) != len(hynix_closes):
        return None

    result: dict = {}

    for n in (5, 20):
        s_ret = _return_pct(samsung_closes, n)
        h_ret = _return_pct(hynix_closes, n)
        result[f"samsung_return_{n}d"] = s_ret
        result[f"hynix_return_{n}d"] = h_ret
        if s_ret is not None and h_ret is not None:
            result[f"alpha_{n}d"] = s_ret - h_ret
        else:
            result[f"alpha_{n}d"] = None

    # RS 시계열 (삼성전자 / SK하이닉스)
    rs = [s / h for s, h in zip(samsung_closes, hynix_closes)]
    result["rs_current"] = rs[-1]
    result["rs_ma20"] = _simple_ma(rs, 20)

    # 추세 판정
    result["relative_trend"] = _determine_relative_trend(rs, result["rs_ma20"])

    return result


def _determine_relative_trend(rs: list[float], rs_ma20: float | None) -> str:
    """RS 추세를 판정한다.

    MA20이 있으면: 현재 RS > MA20 → outperform, < → underperform
    MA20이 없으면: 최근 RS 변화 방향으로 판정
    ±2% 이내 차이는 neutral.
    """
    if rs_ma20 is not None:
        diff_pct = (rs[-1] / rs_ma20 - 1) * 100
        if diff_pct > 2:
            return "outperform"
        elif diff_pct < -2:
            return "underperform"
        return "neutral"

    lookback = min(5, len(rs) - 1)
    if lookback < 1:
        return "neutral"
    change_pct = (rs[-1] / rs[-1 - lookback] - 1) * 100
    if change_pct > 1:
        return "outperform"
    elif change_pct < -1:
        return "underperform"
    return "neutral"


def compute_sox_trend(closes: list[float]) -> dict | None:
    """SOX 지수 추세를 분석한다.

    Args:
        closes: SOX 종가 배열 (날짜 오름차순, 최소 5개).

    Returns:
        분석 결과 dict. 데이터 부족 시 None.
            trend: "상승" | "하락" | "횡보"
            change_pct: 20일(또는 전체) 변동률(%)
            ma20: 20일 이동평균
            current: 최신 종가
            strength: 추세 강도 (-1.0 ~ 1.0)
    """
    if len(closes) < 5:
        return None

    current = closes[-1]
    ma20 = _simple_ma(closes, 20)

    # 변동률: 20일 또는 가용 데이터
    lookback = min(20, len(closes) - 1)
    change_pct = (current / closes[-1 - lookback] - 1) * 100

    # 추세 강도: MA20 대비 위치 + 변동률 종합
    if ma20 is not None:
        ma_diff = (current / ma20 - 1) * 100
    else:
        ma_diff = change_pct

    # strength: -1.0 ~ 1.0 (변동률을 20%에서 클램핑)
    raw_strength = ma_diff / 20.0
    strength = max(-1.0, min(1.0, raw_strength))

    # 추세 판정
    if change_pct > 3:
        trend = "상승"
    elif change_pct < -3:
        trend = "하락"
    else:
        trend = "횡보"

    return {
        "trend": trend,
        "change_pct": round(change_pct, 2),
        "ma20": round(ma20, 2) if ma20 is not None else None,
        "current": current,
        "strength": round(strength, 3),
    }


def compute_semiconductor_momentum(
    rel_perf: dict | None,
    sox_trend: dict | None,
) -> int:
    """반도체 섹터 모멘텀 스코어를 산출한다 (-100 ~ +100).

    세 가지 요소의 가중합:
    1. 삼성전자 vs SK하이닉스 상대성과 (40%)
    2. SOX 지수 추세 (40%)
    3. 종합 방향성 보너스 (20%)

    입력이 None이면 0을 반환한다.
    """
    if rel_perf is None or sox_trend is None:
        return 0

    # 1. 상대성과 점수 (-50 ~ +50)
    alpha_5d = rel_perf.get("alpha_5d") or 0
    alpha_20d = rel_perf.get("alpha_20d") or 0
    # 단기(5d) 30%, 중기(20d) 70% 가중
    rel_raw = alpha_5d * 0.3 + alpha_20d * 0.7
    # 10%p 초과수익 → 50점으로 스케일링
    rel_score = max(-50, min(50, rel_raw * 5))

    # 2. SOX 추세 점수 (-50 ~ +50)
    sox_strength = sox_trend.get("strength", 0)
    sox_change = sox_trend.get("change_pct", 0)
    # strength(방향성) + change_pct(크기) 종합
    sox_raw = sox_strength * 30 + sox_change * 0.5
    sox_score = max(-50, min(50, sox_raw))

    # 3. 종합 방향성 보너스
    trend_label = rel_perf.get("relative_trend", "neutral")
    sox_label = sox_trend.get("trend", "횡보")

    bonus = 0
    if trend_label == "outperform" and sox_label == "상승":
        bonus = 20
    elif trend_label == "underperform" and sox_label == "하락":
        bonus = -20
    elif trend_label == "outperform" or sox_label == "상승":
        bonus = 10
    elif trend_label == "underperform" or sox_label == "하락":
        bonus = -10

    total = rel_score * 0.4 + sox_score * 0.4 + bonus
    return max(-100, min(100, int(round(total))))
