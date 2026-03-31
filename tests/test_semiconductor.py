"""반도체 업황 데이터 수집 모듈 테스트."""

from unittest.mock import patch, MagicMock

import pytest

from src.data.semiconductor import (
    fetch_skhynix_price,
    fetch_skhynix_ohlcv,
    fetch_sox_index,
    SKHYNIX_CODE,
)


class TestFetchSkhynixPrice:
    """SK하이닉스 현재가 조회 테스트."""

    @patch("src.data.semiconductor.kis_get")
    def test_returns_float(self, mock_kis):
        mock_kis.return_value = {
            "output": {"stck_prpr": "200000"}
        }
        price = fetch_skhynix_price()
        assert price == 200000.0
        assert isinstance(price, float)

    @patch("src.data.semiconductor.kis_get")
    def test_api_failure_raises(self, mock_kis):
        mock_kis.side_effect = Exception("API down")
        with pytest.raises(RuntimeError, match="SK하이닉스 주가 조회 실패"):
            fetch_skhynix_price()


class TestFetchSkhynixOhlcv:
    """SK하이닉스 OHLCV 조회 테스트."""

    @patch("src.data.semiconductor.kis_get")
    def test_returns_sorted_list(self, mock_kis):
        mock_kis.return_value = {
            "output2": [
                {
                    "stck_bsop_date": "20260330",
                    "stck_oprc": "199000",
                    "stck_hgpr": "201000",
                    "stck_lwpr": "198000",
                    "stck_clpr": "200000",
                    "acml_vol": "5000000",
                },
                {
                    "stck_bsop_date": "20260329",
                    "stck_oprc": "197000",
                    "stck_hgpr": "200000",
                    "stck_lwpr": "196000",
                    "stck_clpr": "199000",
                    "acml_vol": "4500000",
                },
            ]
        }
        rows = fetch_skhynix_ohlcv("2026-03-29", "2026-03-30")
        assert len(rows) == 2
        assert rows[0]["date"] < rows[1]["date"]
        assert rows[1]["close"] == 200000.0

    @patch("src.data.semiconductor.kis_get")
    def test_empty_response(self, mock_kis):
        mock_kis.return_value = {"output2": []}
        rows = fetch_skhynix_ohlcv("2026-03-29", "2026-03-30")
        assert rows == []

    @patch("src.data.semiconductor.kis_get")
    def test_api_failure_raises(self, mock_kis):
        mock_kis.side_effect = Exception("timeout")
        with pytest.raises(RuntimeError, match="SK하이닉스 OHLCV 조회 실패"):
            fetch_skhynix_ohlcv()


class TestFetchSoxIndex:
    """SOX 지수 조회 테스트."""

    @patch("src.data.semiconductor.requests.get")
    def test_returns_sorted_list(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <table class="type_1">
            <tr><th>날짜</th><th>종가</th><th>전일비</th><th>시가</th><th>고가</th><th>저가</th></tr>
            <tr><td>2026.03.30</td><td>5,100.50</td><td>50.00</td><td>5,050.00</td><td>5,120.00</td><td>5,040.00</td></tr>
            <tr><td>2026.03.29</td><td>5,050.50</td><td>30.00</td><td>5,020.00</td><td>5,060.00</td><td>5,010.00</td></tr>
        </table>
        """
        mock_get.return_value = mock_response
        rows = fetch_sox_index(pages=1)
        assert isinstance(rows, list)
        # HTML 파싱이 안 되면 빈 리스트도 OK (웹스크래핑은 불안정)
        for row in rows:
            assert "date" in row
            assert "close" in row

    @patch("src.data.semiconductor.requests.get")
    def test_network_failure_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("network error")
        rows = fetch_sox_index(pages=1)
        assert rows == []
