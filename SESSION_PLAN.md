## Session Plan

### Task 1: 추세 전환 감지를 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/main.py, src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Day 7 이전 세션에서 구축한 `trend_reversal.py`의 `detect_reversal_signals()`를 일일 파이프라인에 통합한다. 구체적으로: (1) `main.py`에서 `detect_reversal_signals(indicators, sr)`를 호출하고 결과를 리포트에 전달, (2) `signal.py`의 `compute_composite_signal()`에 trend_reversal 결과를 반영하여 컨버전스 등급이 strong/moderate일 때 종합 점수에 보너스/페널티 가산, (3) `report.py`에 `_build_trend_reversal_section()` 추가하여 컨버전스 등급·방향·활성 카테고리를 HTML로 표시, (4) `commentary.py`에 `_build_reversal_sentence()` 추가하여 strong/moderate 컨버전스 감지 시 자연어 경고 문장 생성. 각 통합 지점별 테스트를 먼저 작성한다.

### Task 2: 뉴스 헤드라인 수집 모듈 구축 — Naver 모바일 API 기반
Files: src/data/news_fetcher.py, tests/test_news_fetcher.py
Description: Naver 모바일 주식 API(`m.stock.naver.com/api/news/stock/005930`)에서 삼성전자 관련 최신 뉴스 헤드라인을 수집하는 모듈을 구축한다. (1) `fetch_samsung_news(count=10)` 함수: API 호출 → JSON 파싱 → `[{"title": str, "source": str, "datetime": str, "url": str}]` 리스트 반환, (2) 에러 핸들링: 네트워크 실패 시 빈 리스트 반환, (3) 테스트: mock 응답으로 파싱 로직 검증, 에러 케이스 검증. 이 모듈은 다음 세션에서 감정 분석과 리포트 통합의 기반이 된다. 뉴스 헤드라인은 기술적·수급 분석으로 포착하지 못하는 이벤트(실적 발표, 규제 변화, 경쟁사 동향)를 투자자에게 전달하는 핵심 채널이다.
