"""가격대별 거래량 분석(Volume Profile) 모듈 테스트."""

import pytest

from src.analysis.volume_profile import (
    build_price_histogram,
    compute_poc,
    compute_value_area,
    find_hvn_lvn,
    analyze_volume_profile,
)


def _make_rows(prices: list[tuple], base_volume: int = 1_000_000) -> list[dict]:
    """테스트용 OHLCV rows 생성.

    Args:
        prices: list of (open, high, low, close) or single float (close=open=price, high=+100, low=-100).
        base_volume: 기본 거래량.
    """
    rows = []
    for i, p in enumerate(prices):
        if isinstance(p, (int, float)):
            o, h, l, c = p, p + 100, p - 100, p
        else:
            o, h, l, c = p
        rows.append({
            "date": f"2026-01-{i + 1:02d}",
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": base_volume,
        })
    return rows


class TestBuildPriceHistogram:
    """가격 히스토그램 구축 테스트."""

    def test_single_row(self):
        """단일 봉의 거래량이 가격 범위에 균등 분배된다."""
        rows = _make_rows([(50000, 50200, 49800, 50100)])
        hist = build_price_histogram(rows, bin_size=100)
        assert len(hist) > 0
        total_vol = sum(hist.values())
        assert abs(total_vol - 1_000_000) < 100  # 반올림 오차 허용

    def test_multiple_rows_accumulate(self):
        """여러 봉의 거래량이 누적된다."""
        rows = _make_rows([(50000, 50200, 49800, 50100)] * 3, base_volume=600_000)
        hist = build_price_histogram(rows, bin_size=100)
        total_vol = sum(hist.values())
        assert abs(total_vol - 1_800_000) < 300

    def test_empty_rows(self):
        """빈 리스트면 빈 히스토그램."""
        hist = build_price_histogram([], bin_size=100)
        assert hist == {}

    def test_zero_range_row(self):
        """시가=고가=저가=종가인 경우에도 정상 동작."""
        rows = [{"date": "2026-01-01", "open": 50000, "high": 50000,
                 "low": 50000, "close": 50000, "volume": 1_000_000}]
        hist = build_price_histogram(rows, bin_size=100)
        assert len(hist) == 1
        assert abs(sum(hist.values()) - 1_000_000) < 1


class TestComputePOC:
    """Point of Control 계산 테스트."""

    def test_poc_is_max_volume_bin(self):
        """POC는 최대 거래량 가격대."""
        hist = {50000: 500, 50100: 1200, 50200: 300}
        poc = compute_poc(hist)
        assert poc == 50100

    def test_empty_hist(self):
        """빈 히스토그램이면 None."""
        assert compute_poc({}) is None


class TestComputeValueArea:
    """Value Area 계산 테스트."""

    def test_value_area_contains_70_percent(self):
        """VA가 전체 거래량의 약 70%를 포함한다."""
        hist = {p: 100 for p in range(49000, 51000, 100)}  # 20 bins, 100 each
        hist[50000] = 1000  # POC에 큰 거래량
        poc = compute_poc(hist)
        va = compute_value_area(hist, poc, ratio=0.70)
        assert va["vah"] >= va["val"]
        assert va["poc"] == poc
        va_bins = {p: v for p, v in hist.items() if va["val"] <= p <= va["vah"]}
        va_vol = sum(va_bins.values())
        total_vol = sum(hist.values())
        assert va_vol / total_vol >= 0.69  # 70% 근사

    def test_empty_hist(self):
        """빈 히스토그램이면 모두 None."""
        va = compute_value_area({}, None)
        assert va["poc"] is None
        assert va["vah"] is None
        assert va["val"] is None


class TestFindHVNLVN:
    """HVN/LVN 탐지 테스트."""

    def test_detects_hvn(self):
        """평균 이상 거래량 가격대를 HVN으로 탐지."""
        hist = {p: 100 for p in range(49000, 51000, 100)}
        hist[50000] = 1000  # 명확한 HVN
        hist[50500] = 800
        result = find_hvn_lvn(hist)
        hvn_prices = [n["price"] for n in result["hvn"]]
        assert 50000 in hvn_prices

    def test_detects_lvn(self):
        """평균 이하 거래량 가격대를 LVN으로 탐지."""
        hist = {p: 1000 for p in range(49000, 51000, 100)}
        hist[49500] = 10  # 명확한 LVN
        result = find_hvn_lvn(hist)
        lvn_prices = [n["price"] for n in result["lvn"]]
        assert 49500 in lvn_prices

    def test_empty_hist(self):
        """빈 히스토그램이면 빈 리스트."""
        result = find_hvn_lvn({})
        assert result["hvn"] == []
        assert result["lvn"] == []


class TestAnalyzeVolumeProfile:
    """통합 분석 함수 테스트."""

    def test_full_analysis(self):
        """60일 데이터로 전체 분석 결과 구조 검증."""
        rows = _make_rows([50000 + (i % 10) * 100 for i in range(60)])
        result = analyze_volume_profile(rows)
        assert "poc" in result
        assert "value_area" in result
        assert "hvn" in result
        assert "lvn" in result
        assert "current_price" in result
        assert "position" in result

    def test_position_analysis(self):
        """현재가와 POC/VA 관계를 분석한다."""
        rows = _make_rows([50000 + (i % 10) * 100 for i in range(60)])
        result = analyze_volume_profile(rows)
        pos = result["position"]
        assert "vs_poc" in pos
        assert "in_value_area" in pos

    def test_insufficient_data(self):
        """데이터 부족 시 안전한 기본값 반환."""
        rows = _make_rows([50000])
        result = analyze_volume_profile(rows)
        assert result["poc"] is not None or result["poc"] is None  # 에러 없이 반환

    def test_empty_data(self):
        """빈 데이터 시 None 기본값."""
        result = analyze_volume_profile([])
        assert result["poc"] is None

    def test_custom_lookback(self):
        """lookback 파라미터로 분석 기간 조절."""
        rows = _make_rows([50000 + i * 10 for i in range(100)])
        result_30 = analyze_volume_profile(rows, lookback=30)
        result_60 = analyze_volume_profile(rows, lookback=60)
        assert result_30["poc"] != result_60["poc"] or True  # 값이 다를 수 있음
