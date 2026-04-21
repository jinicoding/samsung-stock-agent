"""가격대별 거래량 분석(Volume Profile) 모듈.

일봉 OHLCV 데이터에서 가격대별 거래량 분포를 계산하여
POC, Value Area, HVN, LVN을 산출한다.
"""

from statistics import mean


def build_price_histogram(rows: list[dict], bin_size: int = 100) -> dict[int, float]:
    """각 일봉의 거래량을 OHLC 범위에 균등 분배하여 가격 히스토그램을 구축한다.

    Args:
        rows: OHLCV dicts (날짜 오름차순).
        bin_size: 가격 구간 크기 (원 단위). 기본 100원.

    Returns:
        {가격대(int): 누적거래량(float)} 딕셔너리.
    """
    histogram: dict[int, float] = {}
    for row in rows:
        high = row["high"]
        low = row["low"]
        volume = row["volume"]

        low_bin = int(low // bin_size) * bin_size
        high_bin = int(high // bin_size) * bin_size

        if low_bin == high_bin:
            histogram[low_bin] = histogram.get(low_bin, 0) + volume
            continue

        num_bins = (high_bin - low_bin) // bin_size + 1
        vol_per_bin = volume / num_bins
        for b in range(low_bin, high_bin + bin_size, bin_size):
            histogram[b] = histogram.get(b, 0) + vol_per_bin

    return histogram


def compute_poc(histogram: dict[int, float]) -> int | None:
    """Point of Control — 최대 거래량 가격대를 반환한다."""
    if not histogram:
        return None
    return max(histogram, key=histogram.get)


def compute_value_area(
    histogram: dict[int, float],
    poc: int | None,
    ratio: float = 0.70,
) -> dict:
    """전체 거래량의 ratio(기본 70%)가 집중된 가격 범위를 계산한다.

    POC에서 시작하여 양쪽으로 확장하며 목표 비율을 달성한다.

    Returns:
        {"poc": int|None, "vah": int|None, "val": int|None}
    """
    none_result = {"poc": None, "vah": None, "val": None}
    if not histogram or poc is None:
        return none_result

    total_vol = sum(histogram.values())
    target_vol = total_vol * ratio

    sorted_prices = sorted(histogram.keys())
    poc_idx = sorted_prices.index(poc)

    included = {poc}
    current_vol = histogram[poc]
    lo_idx = poc_idx
    hi_idx = poc_idx

    while current_vol < target_vol and (lo_idx > 0 or hi_idx < len(sorted_prices) - 1):
        lo_vol = histogram[sorted_prices[lo_idx - 1]] if lo_idx > 0 else -1
        hi_vol = histogram[sorted_prices[hi_idx + 1]] if hi_idx < len(sorted_prices) - 1 else -1

        if lo_vol >= hi_vol and lo_idx > 0:
            lo_idx -= 1
            current_vol += histogram[sorted_prices[lo_idx]]
        elif hi_idx < len(sorted_prices) - 1:
            hi_idx += 1
            current_vol += histogram[sorted_prices[hi_idx]]
        else:
            lo_idx -= 1
            current_vol += histogram[sorted_prices[lo_idx]]

    return {
        "poc": poc,
        "val": sorted_prices[lo_idx],
        "vah": sorted_prices[hi_idx],
    }


def find_hvn_lvn(
    histogram: dict[int, float],
    hvn_threshold: float = 1.5,
    lvn_threshold: float = 0.5,
) -> dict:
    """High Volume Node와 Low Volume Node를 탐지한다.

    Args:
        histogram: 가격 히스토그램.
        hvn_threshold: 평균 대비 이 배수 이상이면 HVN.
        lvn_threshold: 평균 대비 이 배수 이하이면 LVN.

    Returns:
        {"hvn": [{"price": int, "volume": float}], "lvn": [...]}
    """
    if not histogram:
        return {"hvn": [], "lvn": []}

    volumes = list(histogram.values())
    avg_vol = mean(volumes)

    hvn = []
    lvn = []
    for price in sorted(histogram.keys()):
        vol = histogram[price]
        if vol >= avg_vol * hvn_threshold:
            hvn.append({"price": price, "volume": vol})
        elif vol <= avg_vol * lvn_threshold:
            lvn.append({"price": price, "volume": vol})

    return {"hvn": hvn, "lvn": lvn}


def analyze_volume_profile(
    rows: list[dict],
    lookback: int = 60,
    bin_size: int = 100,
) -> dict:
    """Volume Profile 종합 분석.

    Args:
        rows: OHLCV dicts (날짜 오름차순).
        lookback: 분석 기간 (일). 기본 60일.
        bin_size: 가격 구간 크기. 기본 100원.

    Returns:
        {"poc", "value_area", "hvn", "lvn", "current_price", "position", "histogram"}
    """
    none_result = {
        "poc": None,
        "value_area": {"poc": None, "vah": None, "val": None},
        "hvn": [],
        "lvn": [],
        "current_price": None,
        "position": {"vs_poc": None, "in_value_area": None, "nearest_hvn": None, "nearest_lvn": None},
        "histogram": {},
    }
    if not rows:
        return none_result

    target_rows = rows[-lookback:]
    histogram = build_price_histogram(target_rows, bin_size=bin_size)
    if not histogram:
        return none_result

    poc = compute_poc(histogram)
    value_area = compute_value_area(histogram, poc)
    nodes = find_hvn_lvn(histogram)

    current_price = target_rows[-1]["close"]

    position = _analyze_position(current_price, poc, value_area, nodes)

    return {
        "poc": poc,
        "value_area": value_area,
        "hvn": nodes["hvn"],
        "lvn": nodes["lvn"],
        "current_price": current_price,
        "position": position,
        "histogram": histogram,
    }


def _analyze_position(
    current_price: float,
    poc: int | None,
    value_area: dict,
    nodes: dict,
) -> dict:
    """현재가와 POC/VA/HVN/LVN 간 위치 관계를 분석한다."""
    result = {
        "vs_poc": None,
        "in_value_area": None,
        "nearest_hvn": None,
        "nearest_lvn": None,
    }
    if poc is None:
        return result

    result["vs_poc"] = "above" if current_price > poc else ("below" if current_price < poc else "at")

    val = value_area.get("val")
    vah = value_area.get("vah")
    if val is not None and vah is not None:
        result["in_value_area"] = val <= current_price <= vah

    if nodes["hvn"]:
        result["nearest_hvn"] = min(nodes["hvn"], key=lambda n: abs(n["price"] - current_price))
    if nodes["lvn"]:
        result["nearest_lvn"] = min(nodes["lvn"], key=lambda n: abs(n["price"] - current_price))

    return result
