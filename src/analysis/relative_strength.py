"""삼성전자 vs KOSPI 상대강도(Relative Strength) 분석.

삼성전자 종가와 KOSPI 종가 배열을 받아
N일 수익률 비교, RS 추세 판정, 초과수익률(alpha)을 계산한다.
"""


def _return_pct(prices: list[float], n: int) -> float | None:
    """최근 n일 수익률(%)을 계산한다. 데이터 부족 시 None."""
    if len(prices) <= n:
        return None
    return (prices[-1] / prices[-1 - n] - 1) * 100


def _rs_series(samsung: list[float], kospi: list[float]) -> list[float]:
    """상대강도선(RS = 삼성전자/KOSPI) 시계열을 반환한다."""
    return [s / k for s, k in zip(samsung, kospi)]


def _simple_ma(values: list[float], period: int) -> float | None:
    """마지막 period개의 단순이동평균. 부족 시 None."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def compute_relative_strength(
    samsung_closes: list[float],
    kospi_closes: list[float],
) -> dict | None:
    """삼성전자 vs KOSPI 상대강도를 분석한다.

    Args:
        samsung_closes: 삼성전자 종가 배열 (날짜 오름차순).
        kospi_closes: KOSPI 종가 배열 (날짜 오름차순, 같은 길이).

    Returns:
        분석 결과 dict. 데이터 부족(2개 미만 또는 길이 불일치) 시 None.
            samsung_return_1d/5d/20d: 삼성전자 N일 수익률(%)
            kospi_return_1d/5d/20d: KOSPI N일 수익률(%)
            alpha_1d/5d/20d: 초과수익률(%) = 삼성전자 - KOSPI
            rs_current: 현재 RS (삼성전자/KOSPI)
            rs_ma20: RS 20일 이동평균
            rs_trend: "outperform" | "underperform" | "neutral"
    """
    if len(samsung_closes) < 2 or len(kospi_closes) < 2:
        return None
    if len(samsung_closes) != len(kospi_closes):
        return None

    # N일 수익률
    result = {}
    for n in (1, 5, 20):
        s_ret = _return_pct(samsung_closes, n)
        k_ret = _return_pct(kospi_closes, n)
        result[f"samsung_return_{n}d"] = s_ret
        result[f"kospi_return_{n}d"] = k_ret
        if s_ret is not None and k_ret is not None:
            result[f"alpha_{n}d"] = s_ret - k_ret
        else:
            result[f"alpha_{n}d"] = None

    # RS 시계열
    rs = _rs_series(samsung_closes, kospi_closes)
    result["rs_current"] = rs[-1]
    result["rs_ma20"] = _simple_ma(rs, 20)

    # RS 추세 판정
    result["rs_trend"] = _determine_trend(rs, result["rs_ma20"])

    return result


def _determine_trend(
    rs: list[float], rs_ma20: float | None,
) -> str:
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

    # MA20 없을 때: 최근 5개(또는 전체) RS 변화율로 판정
    lookback = min(5, len(rs) - 1)
    if lookback < 1:
        return "neutral"
    change_pct = (rs[-1] / rs[-1 - lookback] - 1) * 100
    if change_pct > 1:
        return "outperform"
    elif change_pct < -1:
        return "underperform"
    return "neutral"
