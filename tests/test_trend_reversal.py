"""추세 전환 감지 모듈 테스트.

5개 카테고리(모멘텀/추세/변동성/거래량/구조)에서 시그널 컨버전스를 감지하고
가중 점수(0~100)와 등급(strong/moderate/weak/none)을 판정한다.
"""

import pytest

from src.analysis.trend_reversal import detect_reversal_signals


# ---------------------------------------------------------------------------
# 헬퍼: 기본 tech_indicators / support_resistance 딕셔너리
# ---------------------------------------------------------------------------

def _base_tech(**overrides) -> dict:
    """중립 기술적 지표. overrides로 특정 값만 변경."""
    base = {
        "current_price": 55000,
        "rsi_14": 50.0,
        "stoch_k": 50.0,
        "stoch_d": 50.0,
        "macd": 0.0,
        "macd_signal": 0.0,
        "macd_histogram": 0.0,
        "price_vs_ma5_pct": 0.0,
        "price_vs_ma20_pct": 0.0,
        "price_vs_ma60_pct": 0.0,
        "bb_pctb": 0.5,
        "bb_width": 0.05,
        "obv_divergence": None,
        "volume_ratio_5d": 1.0,
    }
    base.update(overrides)
    return base


def _base_sr(**overrides) -> dict:
    """중립 지지/저항선 정보."""
    base = {
        "nearest_support": 53000,
        "nearest_resistance": 57000,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. 강한 강세 반전 (4+ 카테고리 동시 신호)
# ---------------------------------------------------------------------------

class TestStrongBullishReversal:
    def test_4_categories_bullish(self):
        """모멘텀+추세+변동성+거래량 4개 카테고리에서 강세 반전 신호."""
        tech = _base_tech(
            rsi_14=22.0,          # 모멘텀: 과매도 반등
            stoch_k=15.0,
            stoch_d=12.0,
            macd_histogram=50.0,  # 추세: MACD 상승 교차
            price_vs_ma20_pct=-5.0,  # 추세: MA 아래에서 반등
            bb_pctb=0.05,         # 변동성: 하단밴드 접근
            obv_divergence="bullish",  # 거래량: OBV 강세 다이버전스
            volume_ratio_5d=2.5,  # 거래량: 거래량 급증
        )
        sr = _base_sr(nearest_support=54800)  # 구조: 지지선 근접

        result = detect_reversal_signals(tech, sr)

        assert result["direction"] == "bullish"
        assert result["convergence"] == "strong"
        assert result["score"] >= 70
        assert result["active_categories"] >= 4

    def test_5_categories_bullish(self):
        """5개 카테고리 모두에서 강세 반전 → 최대 수준."""
        tech = _base_tech(
            current_price=54900,
            rsi_14=20.0,
            stoch_k=10.0,
            stoch_d=8.0,
            macd_histogram=80.0,
            price_vs_ma20_pct=-6.0,
            bb_pctb=0.02,
            obv_divergence="bullish",
            volume_ratio_5d=3.0,
        )
        sr = _base_sr(nearest_support=54800)  # 지지선 바로 위

        result = detect_reversal_signals(tech, sr)

        assert result["direction"] == "bullish"
        assert result["convergence"] == "strong"
        assert result["score"] >= 80
        assert result["active_categories"] == 5


# ---------------------------------------------------------------------------
# 2. 강한 약세 반전 (4+ 카테고리 동시 신호)
# ---------------------------------------------------------------------------

class TestStrongBearishReversal:
    def test_4_categories_bearish(self):
        """모멘텀+추세+변동성+거래량 4개 카테고리에서 약세 반전 신호."""
        tech = _base_tech(
            rsi_14=78.0,          # 모멘텀: 과매수
            stoch_k=88.0,
            stoch_d=85.0,
            macd_histogram=-60.0, # 추세: MACD 하락 교차
            price_vs_ma20_pct=6.0,   # 추세: MA 위로 과열
            bb_pctb=0.98,         # 변동성: 상단밴드 접근
            obv_divergence="bearish",  # 거래량: OBV 약세 다이버전스
            volume_ratio_5d=2.0,
        )
        sr = _base_sr(nearest_resistance=55200)

        result = detect_reversal_signals(tech, sr)

        assert result["direction"] == "bearish"
        assert result["convergence"] == "strong"
        assert result["score"] >= 70
        assert result["active_categories"] >= 4


# ---------------------------------------------------------------------------
# 3. 중간 약세 반전 (3 카테고리)
# ---------------------------------------------------------------------------

class TestModerateReversal:
    def test_3_categories_bearish(self):
        """모멘텀+변동성+거래량 3개 카테고리 약세 반전 → moderate."""
        tech = _base_tech(
            rsi_14=75.0,
            stoch_k=82.0,
            stoch_d=80.0,
            macd_histogram=10.0,   # 추세는 아직 양수 (신호 없음)
            price_vs_ma20_pct=1.0,
            bb_pctb=0.95,          # 변동성: 상단 접근
            obv_divergence="bearish",
            volume_ratio_5d=2.0,
        )
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)

        assert result["direction"] == "bearish"
        assert result["convergence"] == "moderate"
        assert result["active_categories"] == 3

    def test_3_categories_bullish(self):
        """모멘텀+추세+변동성 3개 카테고리 강세 반전 → moderate."""
        tech = _base_tech(
            rsi_14=25.0,
            stoch_k=18.0,
            stoch_d=15.0,
            macd_histogram=30.0,
            price_vs_ma20_pct=-4.0,
            bb_pctb=0.08,
            obv_divergence=None,   # 거래량 신호 없음
            volume_ratio_5d=1.0,
        )
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)

        assert result["direction"] == "bullish"
        assert result["convergence"] == "moderate"
        assert result["active_categories"] == 3


# ---------------------------------------------------------------------------
# 4. 혼합 신호 (카테고리마다 방향이 다름)
# ---------------------------------------------------------------------------

class TestMixedSignals:
    def test_conflicting_signals(self):
        """모멘텀 강세 + 추세 약세 + 변동성 약세 → 방향이 혼합."""
        tech = _base_tech(
            rsi_14=25.0,          # 모멘텀: 강세
            stoch_k=18.0,
            stoch_d=15.0,
            macd_histogram=-50.0, # 추세: 약세
            price_vs_ma20_pct=5.0,
            bb_pctb=0.92,         # 변동성: 약세
            obv_divergence=None,
            volume_ratio_5d=1.0,
        )
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)

        # 혼합 신호: convergence가 강하지 않아야 함
        assert result["convergence"] in ("weak", "none")
        # category_signals에 양방향이 존재
        signals = result["category_signals"]
        directions = {s["direction"] for s in signals.values() if s["direction"] != "neutral"}
        assert len(directions) >= 2  # bullish와 bearish 모두 존재


# ---------------------------------------------------------------------------
# 5. 신호 없음 (모든 지표 중립)
# ---------------------------------------------------------------------------

class TestNoSignal:
    def test_all_neutral(self):
        """모든 지표가 중립 → 신호 없음."""
        tech = _base_tech()  # 모든 값 중립
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)

        assert result["convergence"] == "none"
        assert result["score"] < 20
        assert result["active_categories"] == 0

    def test_one_weak_signal(self):
        """하나의 카테고리에서만 약한 신호."""
        tech = _base_tech(rsi_14=35.0)  # 약간 과매도이지만 극단 아님
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)

        assert result["convergence"] in ("weak", "none")
        assert result["score"] < 40


# ---------------------------------------------------------------------------
# 6. 데이터 부족 (None 값이 많은 경우)
# ---------------------------------------------------------------------------

class TestInsufficientData:
    def test_all_none(self):
        """모든 지표가 None → 안전하게 처리."""
        tech = {
            "current_price": 55000,
            "rsi_14": None,
            "stoch_k": None,
            "stoch_d": None,
            "macd": None,
            "macd_signal": None,
            "macd_histogram": None,
            "price_vs_ma5_pct": None,
            "price_vs_ma20_pct": None,
            "price_vs_ma60_pct": None,
            "bb_pctb": None,
            "bb_width": None,
            "obv_divergence": None,
            "volume_ratio_5d": None,
        }
        sr = {"nearest_support": None, "nearest_resistance": None}

        result = detect_reversal_signals(tech, sr)

        assert result["convergence"] == "none"
        assert result["score"] == 0
        assert result["active_categories"] == 0

    def test_partial_data(self):
        """일부 지표만 있는 경우 — 있는 것만으로 판단."""
        tech = _base_tech(
            rsi_14=20.0,
            stoch_k=None,
            stoch_d=None,
            macd_histogram=None,
            bb_pctb=0.03,
        )
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)

        # 모멘텀(RSI만)과 변동성(BB)은 감지 가능
        assert result["active_categories"] >= 1
        assert result["direction"] == "bullish"


# ---------------------------------------------------------------------------
# 7. 반환 구조 검증
# ---------------------------------------------------------------------------

class TestOutputStructure:
    def test_result_keys(self):
        """반환 딕셔너리에 필수 키가 모두 존재."""
        result = detect_reversal_signals(_base_tech(), _base_sr())

        required_keys = {
            "direction", "convergence", "score", "active_categories",
            "category_signals", "summary",
        }
        assert required_keys.issubset(result.keys())

    def test_category_signals_structure(self):
        """category_signals에 5개 카테고리가 모두 존재."""
        result = detect_reversal_signals(_base_tech(), _base_sr())

        categories = {"momentum", "trend", "volatility", "volume", "structure"}
        assert set(result["category_signals"].keys()) == categories

        # 각 카테고리에 direction과 strength가 있어야 함
        for cat, sig in result["category_signals"].items():
            assert "direction" in sig
            assert "strength" in sig
            assert sig["direction"] in ("bullish", "bearish", "neutral")
            assert 0 <= sig["strength"] <= 100

    def test_score_range(self):
        """점수가 0~100 범위."""
        # 극단적 강세
        tech = _base_tech(rsi_14=15.0, stoch_k=8.0, stoch_d=5.0,
                          macd_histogram=100.0, price_vs_ma20_pct=-8.0,
                          bb_pctb=0.01, obv_divergence="bullish",
                          volume_ratio_5d=4.0)
        sr = _base_sr(nearest_support=54900, current_price=55000)

        result = detect_reversal_signals(tech, sr)
        assert 0 <= result["score"] <= 100


# ---------------------------------------------------------------------------
# 8. 구조 카테고리 (지지/저항선 근접)
# ---------------------------------------------------------------------------

class TestStructureCategory:
    def test_near_support_bullish(self):
        """현재가가 지지선에 매우 근접 → 구조 강세 신호."""
        tech = _base_tech(current_price=54000)
        sr = _base_sr(nearest_support=53800)  # 0.37% 거리

        result = detect_reversal_signals(tech, sr)
        assert result["category_signals"]["structure"]["direction"] == "bullish"

    def test_near_resistance_bearish(self):
        """현재가가 저항선에 매우 근접 → 구조 약세 신호."""
        tech = _base_tech(current_price=56800)
        sr = _base_sr(nearest_resistance=57000)  # 0.35% 거리

        result = detect_reversal_signals(tech, sr)
        assert result["category_signals"]["structure"]["direction"] == "bearish"

    def test_far_from_levels(self):
        """지지/저항선에서 멀리 있으면 구조 신호 없음."""
        tech = _base_tech(current_price=55000)
        sr = _base_sr(nearest_support=50000, nearest_resistance=60000)

        result = detect_reversal_signals(tech, sr)
        assert result["category_signals"]["structure"]["direction"] == "neutral"


# ---------------------------------------------------------------------------
# 9. 경계값 테스트
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_rsi_exactly_30(self):
        """RSI 정확히 30 — 과매도 경계."""
        tech = _base_tech(rsi_14=30.0, stoch_k=20.0, stoch_d=18.0)
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)
        # 경계값에서 강세 신호 감지되어야 함
        assert result["category_signals"]["momentum"]["direction"] == "bullish"

    def test_rsi_exactly_70(self):
        """RSI 정확히 70 — 과매수 경계."""
        tech = _base_tech(rsi_14=70.0, stoch_k=80.0, stoch_d=78.0)
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)
        assert result["category_signals"]["momentum"]["direction"] == "bearish"


# ---------------------------------------------------------------------------
# 10. convergence 등급 전환 기준
# ---------------------------------------------------------------------------

class TestConvergenceGrades:
    def test_weak_with_2_categories(self):
        """2개 카테고리 → weak."""
        tech = _base_tech(
            rsi_14=22.0, stoch_k=15.0, stoch_d=12.0,  # 모멘텀: 강세
            bb_pctb=0.04,                                # 변동성: 강세
            macd_histogram=0.0,                          # 추세: 중립
            obv_divergence=None, volume_ratio_5d=1.0,    # 거래량: 중립
        )
        sr = _base_sr(nearest_support=50000)  # 구조: 중립 (멀리)

        result = detect_reversal_signals(tech, sr)
        assert result["convergence"] == "weak"
        assert result["active_categories"] == 2

    def test_none_with_0_categories(self):
        """0개 카테고리 → none."""
        tech = _base_tech()
        sr = _base_sr()

        result = detect_reversal_signals(tech, sr)
        assert result["convergence"] == "none"
        assert result["active_categories"] == 0
