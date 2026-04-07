"""글로벌 매크로 데이터 수집 모듈 테스트 (NASDAQ + VIX)."""

from unittest.mock import patch, MagicMock

from src.data.global_macro import fetch_nasdaq_index, fetch_vix_index, _parse_index_page


# Naver Finance 해외지수 페이지 모의 HTML
SAMPLE_HTML = """
<table class="type_1">
    <tr>
        <td class="date"> 2026.04.03 </td>
        <td class="num"> 16,780.36 </td>
        <td class="num">something</td>
    </tr>
    <tr>
        <td class="date"> 2026.04.02 </td>
        <td class="num"> 16,550.12 </td>
        <td class="num">something</td>
    </tr>
    <tr>
        <td class="date"> 2026.04.01 </td>
        <td class="num"> 16,400.00 </td>
        <td class="num">something</td>
    </tr>
</table>
"""

VIX_HTML = """
<table class="type_1">
    <tr>
        <td class="date"> 2026.04.03 </td>
        <td class="num"> 18.25 </td>
        <td class="num">something</td>
    </tr>
    <tr>
        <td class="date"> 2026.04.02 </td>
        <td class="num"> 19.50 </td>
        <td class="num">something</td>
    </tr>
</table>
"""


class TestParseIndexPage:
    """Naver 해외지수 HTML 파싱 테스트."""

    def test_parses_dates_and_closes(self):
        rows = _parse_index_page(SAMPLE_HTML)
        assert len(rows) == 3
        assert rows[0]["date"] == "2026-04-03"
        assert rows[0]["close"] == 16780.36
        assert rows[2]["date"] == "2026-04-01"
        assert rows[2]["close"] == 16400.00

    def test_empty_html(self):
        rows = _parse_index_page("<html></html>")
        assert rows == []

    def test_vix_values(self):
        rows = _parse_index_page(VIX_HTML)
        assert len(rows) == 2
        assert rows[0]["close"] == 18.25
        assert rows[1]["close"] == 19.50


class TestFetchNasdaqIndex:
    """NASDAQ 지수 수집 테스트."""

    @patch("src.data.global_macro.requests.get")
    def test_returns_sorted_ascending(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = SAMPLE_HTML
        mock_get.return_value = mock_resp

        rows = fetch_nasdaq_index(days=60)
        assert isinstance(rows, list)
        assert len(rows) == 3
        # 날짜 오름차순 확인
        assert rows[0]["date"] == "2026-04-01"
        assert rows[-1]["date"] == "2026-04-03"
        # Naver URL 호출 확인
        call_args = mock_get.call_args
        assert call_args[1]["params"]["symbol"] == "CCMP"

    @patch("src.data.global_macro.requests.get")
    def test_deduplicates(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = SAMPLE_HTML
        mock_get.return_value = mock_resp

        # 2페이지 요청 시 중복 제거 확인
        rows = fetch_nasdaq_index(days=60)
        dates = [r["date"] for r in rows]
        assert len(dates) == len(set(dates))

    @patch("src.data.global_macro.requests.get")
    def test_network_failure_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        rows = fetch_nasdaq_index(days=60)
        assert rows == []


class TestFetchVixIndex:
    """VIX 지수 수집 테스트."""

    @patch("src.data.global_macro.requests.get")
    def test_returns_sorted_ascending(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = VIX_HTML
        mock_get.return_value = mock_resp

        rows = fetch_vix_index(days=60)
        assert isinstance(rows, list)
        assert len(rows) == 2
        assert rows[0]["date"] == "2026-04-02"
        assert rows[-1]["date"] == "2026-04-03"
        # VIX 심볼 확인
        call_args = mock_get.call_args
        assert call_args[1]["params"]["symbol"] == "CBOEVIX"

    @patch("src.data.global_macro.requests.get")
    def test_network_failure_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("network error")
        rows = fetch_vix_index(days=60)
        assert rows == []
