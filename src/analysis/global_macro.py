"""글로벌 매크로 분석: NASDAQ 추세 + VIX 리스크 해석 + 종합 스코어.

src/data/global_macro.py에서 수집한 NASDAQ/VIX 데이터를 해석하여
글로벌 매크로 환경이 삼성전자에 미치는 영향을 정량화한다.
"""

from __future__ import annotations


def _simple_ma(values: list[float], period: int) -> float | None:
    """마지막 period개의 단순이동평균. 부족 시 None."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def analyze_nasdaq_trend(closes: list[float]) -> dict | None:
    """NASDAQ 종가 배열에서 추세·모멘텀을 분석한다.

    Args:
        closes: NASDAQ 종가 (날짜 오름차순, 최소 5개).

    Returns:
        분석 결과 dict. 데이터 부족 시 None.
    """
    if len(closes) < 5:
        return None

    current = closes[-1]
    ma5 = _simple_ma(closes, 5)
    ma20 = _simple_ma(closes, 20)

    # 5일/20일 변동률
    change_5d = (current / closes[-5] - 1) * 100 if len(closes) >= 5 else 0
    lookback_20 = min(20, len(closes) - 1)
    change_20d = (current / closes[-1 - lookback_20] - 1) * 100

    # 모멘텀 강도: MA5 vs MA20 위치 기반 (-1.0 ~ 1.0)
    if ma20 is not None and ma5 is not None:
        ma_diff_pct = (ma5 / ma20 - 1) * 100
    else:
        ma_diff_pct = change_5d

    momentum_strength = max(-1.0, min(1.0, ma_diff_pct / 10.0))

    # 추세 판정
    if change_20d > 3:
        trend = "상승"
    elif change_20d < -3:
        trend = "하락"
    else:
        # 20일 변동이 작으면 5일도 확인
        if abs(change_5d) <= 2:
            trend = "보합"
        elif change_5d > 0:
            trend = "상승"
        else:
            trend = "하락"

    return {
        "trend": trend,
        "change_5d_pct": round(change_5d, 2),
        "change_20d_pct": round(change_20d, 2),
        "ma5": round(ma5, 2) if ma5 is not None else None,
        "ma20": round(ma20, 2) if ma20 is not None else None,
        "current": current,
        "momentum_strength": round(momentum_strength, 3),
    }


def analyze_vix_risk(closes: list[float]) -> dict | None:
    """VIX 종가 배열에서 리스크 레벨과 추세를 판정한다.

    Args:
        closes: VIX 종가 (날짜 오름차순, 최소 3개).

    Returns:
        분석 결과 dict. 데이터 부족 시 None.
    """
    if len(closes) < 3:
        return None

    current = closes[-1]

    # 리스크 레벨
    if current < 20:
        risk_level = "안정"
    elif current < 30:
        risk_level = "경계"
    else:
        risk_level = "공포"

    # VIX 추세: 최근 3일 변동 기준
    lookback = min(5, len(closes) - 1)
    change_pct = (current / closes[-1 - lookback] - 1) * 100

    if change_pct > 5:
        vix_trend = "상승"
    elif change_pct < -5:
        vix_trend = "하락"
    else:
        vix_trend = "보합"

    # 해석 텍스트
    interpretation = _build_vix_interpretation(risk_level, vix_trend)

    return {
        "risk_level": risk_level,
        "current": current,
        "vix_trend": vix_trend,
        "change_pct": round(change_pct, 2),
        "interpretation": interpretation,
    }


def _build_vix_interpretation(risk_level: str, vix_trend: str) -> str:
    """VIX 상태에 대한 자연어 해석을 생성한다."""
    level_text = {
        "안정": "시장 변동성이 낮아 투자 심리가 안정적",
        "경계": "시장 불확실성이 높아지고 있어 주의 필요",
        "공포": "시장 공포 심리가 극대화되어 리스크 관리 필수",
    }
    trend_text = {
        "상승": "변동성이 확대되는 추세로 리스크 증가",
        "하락": "변동성이 완화되는 추세로 리스크 감소",
        "보합": "변동성이 횡보 중",
    }
    return f"{level_text[risk_level]}. {trend_text[vix_trend]}."


def compute_global_macro_score(
    nasdaq_analysis: dict | None,
    vix_analysis: dict | None,
) -> int:
    """NASDAQ 추세 + VIX 리스크를 종합하여 매크로 스코어를 산출한다 (-100 ~ +100).

    양수 = 글로벌 환경 긍정, 음수 = 부정.

    가중치: NASDAQ 모멘텀 50%, VIX 리스크 30%, 방향성 보너스 20%.
    """
    if nasdaq_analysis is None or vix_analysis is None:
        return 0

    # 1. NASDAQ 모멘텀 점수 (-50 ~ +50)
    momentum = nasdaq_analysis.get("momentum_strength", 0)
    change_20d = nasdaq_analysis.get("change_20d_pct", 0)
    nasdaq_raw = momentum * 30 + change_20d * 0.5
    nasdaq_score = max(-50, min(50, nasdaq_raw))

    # 2. VIX 리스크 점수 (-50 ~ +50): VIX 낮으면 긍정, 높으면 부정
    vix_current = vix_analysis.get("current", 20)
    vix_change = vix_analysis.get("change_pct", 0)
    # VIX 20 기준: 낮을수록 긍정, 높을수록 부정
    vix_level_score = (20 - vix_current) * 2  # VIX 10 → +20, VIX 30 → -20
    vix_trend_score = -vix_change * 0.5  # VIX 상승 → 부정
    vix_raw = vix_level_score + vix_trend_score
    vix_score = max(-50, min(50, vix_raw))

    # 3. 방향성 보너스 (-20 ~ +20)
    nasdaq_trend = nasdaq_analysis.get("trend", "보합")
    risk_level = vix_analysis.get("risk_level", "경계")
    vix_trend = vix_analysis.get("vix_trend", "보합")

    bonus = 0
    if nasdaq_trend == "상승" and risk_level == "안정":
        bonus = 20
    elif nasdaq_trend == "하락" and risk_level == "공포":
        bonus = -20
    elif nasdaq_trend == "상승" or (risk_level == "안정" and vix_trend == "하락"):
        bonus = 10
    elif nasdaq_trend == "하락" or (risk_level == "공포" and vix_trend == "상승"):
        bonus = -10

    total = nasdaq_score * 0.5 + vix_score * 0.3 + bonus
    return max(-100, min(100, int(round(total))))
