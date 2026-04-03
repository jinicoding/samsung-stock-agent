## Session Plan

### Task 1: 리포트 핵심 요약(Executive Summary) 섹션 추가
Files: src/analysis/report.py, tests/test_report.py
Description: 현재 리포트는 20개 이상의 기술적 섹션이 나열되지만 투자자가 가장 먼저 읽어야 할 "오늘의 핵심"이 없다. 실무 증권사 리포트는 항상 executive summary로 시작한다. report.py의 generate_daily_report() 상단에 "📊 핵심 요약" 섹션을 추가한다. 이 섹션은: (1) 종합 시그널 점수와 등급을 한 줄로 표시, (2) 가장 강한 매수/매도 축 2개를 하이라이트, (3) 전일 대비 시그널 방향 변화(개선/악화/유지) — signal_trend의 score_change 활용, (4) 주의가 필요한 이벤트(추세 전환 감지, 지지/저항 근접, 극단적 RSI 등)를 1~2문장으로 압축. _build_executive_summary() 헬퍼 함수를 만들고, generate_daily_report() 최상단에 배치한다. 투자자가 이 섹션만 읽어도 오늘의 시장 상황을 파악할 수 있어야 한다. 테스트를 먼저 작성한다.

### Task 2: 축별 정확도 기반 시그널 신뢰도 표시
Files: src/analysis/accuracy.py, src/analysis/report.py, tests/test_accuracy.py, tests/test_report.py
Description: 현재 accuracy.py는 종합 시그널의 방향 적중률만 계산한다. 이를 확장하여 각 축(기술/수급/환율)별로 시그널 방향과 실제 주가 변동을 대조한 축별 적중률을 계산하는 함수 evaluate_axis_accuracy()를 추가한다. signal_history 테이블에 이미 technical_score, supply_score, exchange_score가 저장되어 있으므로, 각 축 점수의 방향(양/음)이 이후 실제 주가 변동과 일치했는지를 추적한다. 리포트의 시그널 정확도 섹션에 축별 적중률을 표시하여, 투자자가 "어떤 분석축이 최근 잘 맞고 있는지"를 파악하고 시그널의 신뢰도를 판단할 수 있게 한다. 테스트를 먼저 작성한다.
