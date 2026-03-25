## Session Plan

### Task 1: 지지/저항선 분석을 리포트·파이프라인에 통합
Files: src/analysis/report.py, src/main.py, tests/test_report.py, tests/test_main.py
Description: Day 4 오전에 구축한 support_resistance 모듈이 파이프라인에 연결되지 않았다. (1) main.py에서 analyze_support_resistance()를 호출하여 결과를 generate_daily_report()에 전달한다. (2) report.py에 지지/저항선 HTML 섹션을 추가한다 — 피봇 포인트(PP/S1/S2/R1/R2), 가장 가까운 지지선·저항선, 현재가 대비 거리(%)를 표시한다. (3) 테스트를 먼저 작성하고 구현한다. generate_daily_report()의 시그니처에 support_resistance=None 파라미터를 추가하여 하위 호환성을 유지한다.

### Task 2: 시그널 정확도 추적 시스템 구축
Files: src/analysis/signal_tracker.py, src/data/database.py, tests/test_signal_tracker.py
Description: 종합 시그널의 신뢰성을 측정하기 위해 시그널 기록·검증 시스템을 구축한다. (1) database.py에 signal_history 테이블을 추가한다 (date, score, grade, price_at_signal). (2) signal_tracker.py에 record_signal()로 당일 시그널을 저장하고, evaluate_accuracy()로 N일 후 실제 수익률과 비교하여 적중률을 계산하는 로직을 구현한다. (3) 리포트에 "최근 시그널 적중률" 섹션을 추가하여 투자자가 시그널의 과거 성과를 확인할 수 있게 한다. 테스트 먼저 작성.
