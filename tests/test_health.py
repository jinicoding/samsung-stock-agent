"""데이터 수집 상태 모니터링 모듈 테스트."""

import pytest
from datetime import date

from src.data.health import DataHealthTracker


class TestDataHealthTracker:
    """DataHealthTracker 기본 기능 테스트."""

    def test_record_success(self):
        """성공 상태를 기록할 수 있다."""
        tracker = DataHealthTracker()
        tracker.record("주가", True, latest_date="2026-04-11")
        s = tracker.summary()
        assert s["total"] == 1
        assert s["ok"] == 1
        assert s["failed"] == 0
        assert s["sources"]["주가"]["success"] is True
        assert s["sources"]["주가"]["latest_date"] == "2026-04-11"

    def test_record_failure(self):
        """실패 상태를 기록할 수 있다."""
        tracker = DataHealthTracker()
        tracker.record("수급", False)
        s = tracker.summary()
        assert s["total"] == 1
        assert s["ok"] == 0
        assert s["failed"] == 1
        assert s["sources"]["수급"]["success"] is False
        assert s["sources"]["수급"]["latest_date"] is None

    def test_multiple_sources(self):
        """여러 소스를 등록하면 total/ok/failed 카운트가 맞아야 한다."""
        tracker = DataHealthTracker()
        tracker.record("주가", True, latest_date="2026-04-11")
        tracker.record("수급", True, latest_date="2026-04-10")
        tracker.record("환율", False)
        tracker.record("뉴스", True)
        s = tracker.summary()
        assert s["total"] == 4
        assert s["ok"] == 3
        assert s["failed"] == 1
        assert s["failed_sources"] == ["환율"]

    def test_stale_detection(self):
        """2영업일 이상 미갱신 소스를 stale로 감지한다."""
        tracker = DataHealthTracker(today=date(2026, 4, 12))
        # 4/10 금요일 → 4/12 일요일: 영업일 기준 2일이지만 달력 기준 2일 이상
        tracker.record("주가", True, latest_date="2026-04-09")
        s = tracker.summary()
        assert "주가" in s["stale_sources"]

    def test_not_stale_when_recent(self):
        """최근 데이터가 있으면 stale이 아니다."""
        tracker = DataHealthTracker(today=date(2026, 4, 12))
        tracker.record("주가", True, latest_date="2026-04-11")
        s = tracker.summary()
        assert "주가" not in s["stale_sources"]

    def test_no_latest_date_not_stale(self):
        """latest_date 없이 성공이면 stale에 포함하지 않는다."""
        tracker = DataHealthTracker(today=date(2026, 4, 12))
        tracker.record("뉴스", True)
        s = tracker.summary()
        assert "뉴스" not in s["stale_sources"]

    def test_failed_source_not_stale(self):
        """실패한 소스는 stale이 아닌 failed로만 분류한다."""
        tracker = DataHealthTracker(today=date(2026, 4, 12))
        tracker.record("환율", False, latest_date="2026-04-01")
        s = tracker.summary()
        assert "환율" not in s["stale_sources"]
        assert "환율" in s["failed_sources"]

    def test_summary_empty_tracker(self):
        """아무 소스도 등록하지 않으면 빈 요약이 반환된다."""
        tracker = DataHealthTracker()
        s = tracker.summary()
        assert s["total"] == 0
        assert s["ok"] == 0
        assert s["failed"] == 0
        assert s["failed_sources"] == []
        assert s["stale_sources"] == []


class TestHealthReportSection:
    """리포트 섹션 생성 테스트."""

    def test_all_healthy(self):
        """모든 소스가 정상이면 간략 상태만 표시."""
        from src.analysis.report import _build_health_section
        tracker = DataHealthTracker(today=date(2026, 4, 12))
        tracker.record("주가", True, latest_date="2026-04-11")
        tracker.record("수급", True, latest_date="2026-04-11")
        result = _build_health_section(tracker.summary())
        text = "\n".join(result)
        assert "📡" in text
        assert "2/2" in text

    def test_with_failure(self):
        """실패 소스가 있으면 경고를 표시한다."""
        from src.analysis.report import _build_health_section
        tracker = DataHealthTracker(today=date(2026, 4, 12))
        tracker.record("주가", True, latest_date="2026-04-11")
        tracker.record("환율", False)
        result = _build_health_section(tracker.summary())
        text = "\n".join(result)
        assert "1/2" in text
        assert "환율" in text

    def test_with_stale(self):
        """stale 소스가 있으면 경고를 표시한다."""
        from src.analysis.report import _build_health_section
        tracker = DataHealthTracker(today=date(2026, 4, 12))
        tracker.record("주가", True, latest_date="2026-04-05")
        result = _build_health_section(tracker.summary())
        text = "\n".join(result)
        assert "주가" in text
