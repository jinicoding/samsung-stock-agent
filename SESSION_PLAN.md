## Session Plan

### Task 1: 축별(Per-Axis) 시그널 정확도 추적 시스템 구축
Files: src/analysis/accuracy.py, tests/test_accuracy.py
Description: 현재 accuracy.py는 종합 시그널 점수만 실제 주가 변동과 대조한다. Day 16 오전 세션에서 signal_history에 9축 개별 점수 저장이 확대되었으므로, 이제 각 축별로 독립적인 적중률(hit rate)과 평균 수익률(avg forward return)을 계산하는 기능을 추가한다. evaluate_signals()를 확장하여 summary에 per_axis 섹션을 포함시킨다. 축별 signal_history의 score → 실제 1d/3d/5d forward return 방향 일치 여부를 평가한다. 9축은: technical_score, supply_score, exchange_score, fundamentals_score, news_score, consensus_score, semiconductor_score, volatility_score, candlestick_score. 이를 통해 "어떤 축이 가장 예측력이 높은가"를 정량적으로 파악할 수 있는 피드백 루프의 기반이 마련된다. 테스트 먼저 작성.

### Task 2: 축별 정확도를 리포트·코멘터리에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, tests/test_report.py, tests/test_commentary.py
Description: Task 1에서 구현한 축별 정확도 통계를 리포트 HTML에 표시한다. (1) report.py에 축별 적중률 섹션 추가: 축 이름, 1d/3d/5d hit rate를 테이블 형태로 보여줌. 데이터 부족한 축은 "데이터 축적 중"으로 표시. (2) commentary.py에서 가장 정확한 축(best axis)과 가장 부정확한 축(worst axis)을 자연어로 해설. 예: "최근 기술적 분석 축의 적중률이 73%로 가장 높았으며, 뉴스 감정 축은 45%로 개선이 필요합니다." (3) 향후 가중치 자동 조정의 기반이 되는 "어떤 축을 더 신뢰할 것인가"의 데이터를 투자자와 에이전트 자신에게 모두 보여준다. 테스트 먼저 작성.
