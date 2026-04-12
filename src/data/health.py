"""데이터 수집 상태 모니터링.

각 데이터 소스의 수집 성공/실패 상태와 데이터 최신성을 추적한다.
"""

from __future__ import annotations

from datetime import date, timedelta


class DataHealthTracker:
    """파이프라인 데이터 소스 상태 추적기."""

    def __init__(self, today: date | None = None):
        self._today = today or date.today()
        self._sources: dict[str, dict] = {}

    def record(self, source_name: str, success: bool, latest_date: str | None = None):
        """데이터 소스의 수집 결과를 등록한다.

        Args:
            source_name: 소스 이름 (예: "주가", "수급", "환율")
            success: 수집 성공 여부
            latest_date: 가장 최근 데이터 날짜 (YYYY-MM-DD 문자열, 선택)
        """
        self._sources[source_name] = {
            "success": success,
            "latest_date": latest_date,
        }

    def summary(self) -> dict:
        """전체 상태 요약을 반환한다.

        Returns:
            dict with keys: total, ok, failed, failed_sources, stale_sources, sources
        """
        total = len(self._sources)
        ok = sum(1 for s in self._sources.values() if s["success"])
        failed = total - ok

        failed_sources = [
            name for name, s in self._sources.items() if not s["success"]
        ]

        stale_threshold = self._today - timedelta(days=2)
        stale_sources = []
        for name, s in self._sources.items():
            if not s["success"]:
                continue
            if s["latest_date"] is None:
                continue
            try:
                d = date.fromisoformat(s["latest_date"])
                if d < stale_threshold:
                    stale_sources.append(name)
            except ValueError:
                pass

        return {
            "total": total,
            "ok": ok,
            "failed": failed,
            "failed_sources": failed_sources,
            "stale_sources": stale_sources,
            "sources": dict(self._sources),
        }
