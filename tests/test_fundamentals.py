"""기본적 분석 데이터 수집 모듈 테스트."""

from unittest.mock import patch, MagicMock

import pytest

from src.data.fundamentals import fetch_fundamentals, parse_fundamentals_html


SAMPLE_HTML = """
<table class="per_table">
<caption>PER/EPS</caption>
<tbody>
<tr>
    <th>PER<span class="bar">l</span>EPS<span class="date">(2025.12)</span></th>
    <td>
        <em id="_per">27.38</em>배
        <span class="bar">l</span>
        <em id="_eps">6,564</em>원
    </td>
</tr>
</tbody>
<tr>
    <th>추정PER<span class="bar">l</span>EPS</th>
    <td>
        <em id="_cns_per">7.00</em>배
        <span class="bar">l</span>
        <em id="_cns_eps">24,478</em>원
    </td>
</tr>
<tr>
    <th>PBR<span class="bar">l</span>BPS <span class="date">(2025.12)</span></th>
    <td>
        <em id="_pbr">2.81</em>배
        <span class="bar">l</span>
        <em>63,997</em>원
    </td>
</tr>
<tr>
    <th>배당수익률</th>
    <td>
        <em id="_dvr">0.93</em>%
    </td>
</tr>
</table>
"""


class TestParseFundamentalsHtml:
    """Naver Finance HTML에서 PER/PBR/EPS/BPS/배당수익률 파싱."""

    def test_parse_all_fields(self):
        result = parse_fundamentals_html(SAMPLE_HTML)
        assert result["per"] == 27.38
        assert result["eps"] == 6564
        assert result["estimated_per"] == 7.00
        assert result["estimated_eps"] == 24478
        assert result["pbr"] == 2.81
        assert result["bps"] == 63997
        assert result["dividend_yield"] == 0.93

    def test_parse_missing_field_returns_none(self):
        """필드가 없으면 None."""
        html = '<html><body><em id="_per">10.5</em></body></html>'
        result = parse_fundamentals_html(html)
        assert result["per"] == 10.5
        assert result["pbr"] is None
        assert result["bps"] is None

    def test_parse_negative_eps(self):
        """EPS가 음수인 경우."""
        html = '<em id="_per">N/A</em><em id="_eps">-1,234</em>'
        result = parse_fundamentals_html(html)
        assert result["per"] is None
        assert result["eps"] == -1234

    def test_parse_na_value(self):
        """N/A 값은 None."""
        html = '<em id="_per">N/A</em><em id="_pbr">N/A</em>'
        result = parse_fundamentals_html(html)
        assert result["per"] is None
        assert result["pbr"] is None


class TestFetchFundamentals:
    """fetch_fundamentals 통합 테스트 (HTTP mock)."""

    @patch("src.data.fundamentals.requests.get")
    def test_fetch_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_fundamentals()
        assert result is not None
        assert result["per"] == 27.38
        assert result["pbr"] == 2.81
        assert result["dividend_yield"] == 0.93
        mock_get.assert_called_once()

    @patch("src.data.fundamentals.requests.get")
    def test_fetch_network_error(self, mock_get):
        mock_get.side_effect = Exception("Connection error")
        result = fetch_fundamentals()
        assert result is None
