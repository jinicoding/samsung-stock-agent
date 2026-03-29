## Session Plan

### Task 1: 뉴스 감정 분석을 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Day 8 11:30에 구축한 뉴스 수집 모듈(src/data/news.py)의 fetch_news_headlines()와 summarize_sentiment()를 파이프라인 전체에 통합한다.
- signal.py: _score_news_sentiment() 함수 추가. bullish/bearish/neutral + score 강도로 -100~+100 점수 산출. compute_composite_signal()에 news_sentiment 선택 파라미터 추가, 6축 가중치 체계로 확장 (기술 25%, 수급 25%, 환율 15%, RS 10%, 펀더멘털 15%, 뉴스 10%).
- report.py: _build_news_sentiment_section() 함수 추가. 감정 분포(긍정/부정/중립 건수), 주요 헤드라인 최대 3개 표시. generate_daily_report()에 news_sentiment 파라미터 추가.
- commentary.py: _build_news_sentence() 함수 추가. "뉴스 심리가 긍정적/부정적" 등 자연어 코멘터리 생성.
- main.py: fetch_news_headlines() + summarize_sentiment() 호출을 파이프라인에 추가, 결과를 signal/report에 전달.
- 테스트를 먼저 작성하고 구현한다.

### Task 2: 텔레그램 리포트 길이 관리 — 4096자 초과 방지
Files: src/analysis/report.py, tests/test_report.py
Description: 현재 10개 이상 섹션이 모두 렌더링되면 Telegram HTML parse_mode의 4096자 제한을 초과할 가능성이 높다. generate_daily_report() 끝에 길이 검사를 추가하여:
- 4096자 이하면 그대로 반환.
- 초과 시 우선순위가 낮은 섹션(시그널 정확도 → 상대강도 상세 → 지지/저항 상세)을 축약 또는 생략하여 4096자 이내로 맞춘다.
- 테스트: 긴 리포트를 생성하고 4096자 이내로 잘리는지 검증.
