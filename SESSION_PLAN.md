## Session Plan

### Task 1: 핵심 관찰 포인트(Key Watchpoints) 섹션 추가
Files: src/analysis/watchpoints.py, src/analysis/report.py, src/main.py, tests/test_watchpoints.py
Description: 투자자가 "오늘 무엇을 주목해야 하는가"를 즉시 파악할 수 있는 핵심 관찰 포인트 모듈을 구축한다. 구체적으로: (1) 지지/저항선 기준 상승·하락 시나리오 — 현재가 대비 가장 가까운 지지선 이탈 시 다음 지지선 목표, 저항선 돌파 시 다음 저항선 목표를 계산하여 "55,000 지지 이탈 시 → 53,200 주목" 형태로 제시. (2) ATR 기반 예상 일일 변동 범위 — 현재 변동성으로 오늘 예상되는 고가·저가 범위를 제시. (3) 핵심 리스크/기회 요인 2~3개 — 변동성 체제, 추세 전환 감지, 수급 이상 신호, 뉴스 감정 급변 등에서 자동으로 추출. 리포트의 Executive Summary 바로 아래에 배치하여 "요약 → 관찰 포인트 → 상세 분석"이라는 정보 계층 구조를 완성한다. 테스트를 먼저 작성하고 구현한다.

### Task 2: Executive Summary 9축 완전 반영 및 강화
Files: src/analysis/report.py, tests/test_report.py
Description: 현재 _build_executive_summary()는 composite_signal, signal_trend, indicators, support_resistance, trend_reversal 5개 입력만 받아 9축 중 4축(펀더멘털·뉴스·컨센서스·반도체)의 정보가 누락되어 있다. (1) 함수 시그니처에 fundamentals, news_sentiment, consensus, semiconductor_momentum, volatility, candlestick 파라미터를 추가한다. (2) 핵심 요약에 "밸류에이션: PER 저평가" "뉴스: 긍정 우세" "컨센서스: 목표가 괴리 +15%" 등 각 축의 한 줄 요약을 조건부로 표시한다. (3) generate_daily_report() 호출부에서 새 파라미터를 전달한다. (4) 기존 테스트를 확장하여 9축 전체 반영을 검증한다.
