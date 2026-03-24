## Session Plan

### Task 1: 종합 투자 시그널을 일일 리포트·파이프라인에 통합
Files: src/analysis/report.py, src/main.py, tests/test_report.py, tests/test_main.py
Description: signal.py의 compute_composite_signal()을 main.py 파이프라인에서 호출하고, 결과를 generate_daily_report()에 전달하여 리포트 HTML 최상단에 종합 시그널 섹션(점수 게이지, 5단계 판정, 3축 내역)을 표시한다. 투자자가 리포트를 열었을 때 가장 먼저 "오늘의 종합 판정"을 볼 수 있게 한다. 테스트를 먼저 작성한다.

### Task 2: 삼성전자 뉴스 헤드라인 수집기 구축
Files: src/data/news_fetcher.py, tests/test_news_fetcher.py
Description: Naver 증권 삼성전자 뉴스 페이지에서 최근 뉴스 헤드라인(제목, 날짜, 출처)을 스크래핑하는 모듈을 만든다. HTML 파싱은 표준라이브러리(html.parser 또는 re)만 사용하여 외부 의존성을 추가하지 않는다. 수집한 헤드라인은 다음 세션에서 감정 분석·리포트 통합에 활용한다. 테스트를 먼저 작성한다.
