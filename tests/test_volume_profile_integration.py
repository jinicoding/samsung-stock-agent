"""Volume Profile 파이프라인 통합 테스트.

volume_profile 모듈이 report.py, commentary.py, main.py에
올바르게 통합되었는지 검증한다.
"""

from src.analysis.volume_profile import analyze_volume_profile
from src.analysis.report import generate_daily_report, _build_volume_profile_section
from src.analysis.commentary import generate_commentary, _build_volume_profile_sentence


SAMPLE_OHLCV = [
    {"date": f"2026-04-{d:02d}", "open": 55000 + d * 100, "high": 56000 + d * 100,
     "low": 54000 + d * 100, "close": 55500 + d * 100, "volume": 10_000_000}
    for d in range(1, 21)
]

SAMPLE_INDICATORS = {
    "current_date": "2026-04-20",
    "current_price": 57500,
    "change_1d_pct": 0.5,
    "change_5d_pct": 1.2,
    "change_20d_pct": 3.0,
    "ma5": 57000,
    "ma20": 56000,
    "ma60": None,
    "volume_ratio_5d": 1.1,
    "rsi_14": 55.0,
    "macd": 100,
    "macd_signal": 80,
    "macd_histogram": 20,
    "bb_upper": 58000,
    "bb_lower": 54000,
    "bb_width": 0.07,
    "bb_pctb": 0.65,
}


def test_analyze_volume_profile_returns_expected_keys():
    """analyze_volume_profile가 필요한 키를 모두 반환하는지 확인."""
    result = analyze_volume_profile(SAMPLE_OHLCV)
    assert "poc" in result
    assert "value_area" in result
    assert "hvn" in result
    assert "lvn" in result
    assert "current_price" in result
    assert "position" in result
    assert result["poc"] is not None
    assert result["value_area"]["vah"] is not None
    assert result["value_area"]["val"] is not None


def test_build_volume_profile_section_with_data():
    """_build_volume_profile_section이 올바른 HTML 섹션을 생성하는지 확인."""
    vp = analyze_volume_profile(SAMPLE_OHLCV)
    lines = _build_volume_profile_section(vp)
    assert len(lines) > 0
    assert any("Volume Profile" in line or "거래량 프로파일" in line for line in lines)
    assert any("POC" in line for line in lines)
    assert any("Value Area" in line or "VA" in line for line in lines)


def test_build_volume_profile_section_empty():
    """빈 데이터일 때 빈 리스트를 반환하는지 확인."""
    vp = analyze_volume_profile([])
    lines = _build_volume_profile_section(vp)
    assert lines == []


def test_generate_daily_report_includes_volume_profile():
    """generate_daily_report에 volume_profile 파라미터를 전달하면 섹션이 포함되는지 확인."""
    vp = analyze_volume_profile(SAMPLE_OHLCV)
    report = generate_daily_report(SAMPLE_INDICATORS, volume_profile=vp)
    assert "POC" in report
    assert "Volume Profile" in report or "거래량 프로파일" in report


def test_generate_daily_report_without_volume_profile():
    """volume_profile=None이면 Volume Profile 섹션이 없는지 확인."""
    report = generate_daily_report(SAMPLE_INDICATORS, volume_profile=None)
    assert "거래량 프로파일" not in report


def test_build_volume_profile_sentence_above_poc():
    """현재가가 POC 위에 있을 때 적절한 코멘터리를 생성하는지 확인."""
    vp = {
        "poc": 55000,
        "value_area": {"poc": 55000, "vah": 56000, "val": 54000},
        "hvn": [{"price": 55000, "volume": 50000000}],
        "lvn": [{"price": 53000, "volume": 5000000}],
        "current_price": 57000,
        "position": {
            "vs_poc": "above",
            "in_value_area": False,
            "nearest_hvn": {"price": 55000, "volume": 50000000},
            "nearest_lvn": {"price": 53000, "volume": 5000000},
        },
    }
    sentence = _build_volume_profile_sentence(vp)
    assert sentence != ""
    assert "POC" in sentence or "거래 밀집" in sentence


def test_build_volume_profile_sentence_in_value_area():
    """현재가가 Value Area 안에 있을 때 적절한 코멘터리를 생성하는지 확인."""
    vp = {
        "poc": 55000,
        "value_area": {"poc": 55000, "vah": 56000, "val": 54000},
        "hvn": [],
        "lvn": [],
        "current_price": 55500,
        "position": {
            "vs_poc": "above",
            "in_value_area": True,
            "nearest_hvn": None,
            "nearest_lvn": None,
        },
    }
    sentence = _build_volume_profile_sentence(vp)
    assert sentence != ""
    assert "Value Area" in sentence or "가치 영역" in sentence or "거래 밀집" in sentence


def test_build_volume_profile_sentence_empty():
    """POC가 None이면 빈 문자열을 반환하는지 확인."""
    vp = {
        "poc": None,
        "value_area": {"poc": None, "vah": None, "val": None},
        "hvn": [],
        "lvn": [],
        "current_price": None,
        "position": {"vs_poc": None, "in_value_area": None, "nearest_hvn": None, "nearest_lvn": None},
    }
    sentence = _build_volume_profile_sentence(vp)
    assert sentence == ""


def test_commentary_includes_volume_profile():
    """generate_commentary에 volume_profile을 전달하면 관련 내용이 포함되는지 확인."""
    vp = analyze_volume_profile(SAMPLE_OHLCV)
    commentary = generate_commentary(SAMPLE_INDICATORS, volume_profile=vp)
    assert "POC" in commentary or "거래 밀집" in commentary or "Value Area" in commentary or "가치 영역" in commentary
