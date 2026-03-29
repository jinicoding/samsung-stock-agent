## Session Plan

### Task 1: 뉴스 헤드라인 수집기 구축 (src/data/news.py)
Files: src/data/news.py, tests/test_news.py
Description: Naver 모바일 증권 API (`m.stock.naver.com/api/news/stock/005930`)를 활용하여 삼성전자 관련 뉴스 헤드라인을 수집하는 모듈을 구축한다. 최근 20개 뉴스의 제목, 출처, 날짜를 파싱하고, 키워드 기반 간이 감정 분류(positive/negative/neutral)를 수행한다. 긍정 키워드(실적개선, 상승, 반등, 목표가상향 등)와 부정 키워드(하락, 매도, 적자, 리스크, 전쟁 등)를 사전 정의하여 각 헤드라인에 점수를 부여하고, 전체 감정 요약(bullish/bearish/neutral + 점수)을 반환한다. HTML 엔티티(&quot; 등) 디코딩 포함. 테스트는 API 모킹으로 작성하여 오프라인 실행 보장.

### Task 2: 뉴스 감정을 종합 시그널·리포트·코멘터리에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py
Description: Task 1의 뉴스 감정 결과를 파이프라인에 통합한다. (1) signal.py에 `_score_news_sentiment()` 함수를 추가하고, 6축 가중치 체계로 확장한다 (기술 25%, 수급 25%, 환율 15%, RS 10%, 펀더멘털 15%, 뉴스 10%). (2) report.py에 `_build_news_section()` 함수를 추가하여 주요 헤드라인 3개와 감정 요약을 표시한다. (3) commentary.py에 `_build_news_sentence()` 함수를 추가하여 뉴스 감정이 강할 때 자연어 문장을 생성한다. (4) main.py의 파이프라인에 뉴스 수집 단계를 추가한다. 기존 테스트가 깨지지 않도록 뉴스 데이터는 optional 파라미터로 처리한다.
