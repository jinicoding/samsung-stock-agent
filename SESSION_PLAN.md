## Session Plan

### Task 1: 적응형 가중치 시스템 — 정확도 기반 축별 가중치 자동 조정
Files: src/analysis/signal.py, tests/test_signal.py
Description: 현재 종합 시그널의 축별 가중치는 정적(예: 기술 25%, 수급 25% 등)이다. 오늘 구축한 축별 정확도 추적 데이터(accuracy.py의 per_axis hit_rate)를 활용하여 가중치를 동적으로 조정하는 함수를 signal.py에 추가한다. 구체적으로: (1) `adapt_weights(base_weights, accuracy_summary)` 함수를 구현 — 각 축의 최근 적중률(hit_rate_5d)을 기반으로 기본 가중치를 ±30% 범위 내에서 조정. 적중률이 높은 축은 가중치 증가, 낮은 축은 감소. 가중치 합계는 항상 100% 유지. (2) `compute_composite_signal()`에 `accuracy_summary` 파라미터 추가(선택적) — 제공되면 적응형 가중치 사용, 미제공 시 기존 정적 가중치 유지 (하위 호환). (3) 적중률 데이터가 부족하면(evaluated_signals < 5) 해당 축은 조정하지 않는 안전장치. 테스트를 먼저 작성한다.

### Task 2: 리포트에 축별 시그널 신뢰도(적중률) 표시
Files: src/analysis/report.py, tests/test_report.py
Description: 종합 시그널 섹션에서 각 축의 점수 옆에 과거 적중률(hit_rate)을 표시하여, 투자자가 "이 축이 과거에 얼마나 맞았는가"를 즉시 파악할 수 있게 한다. `generate_daily_report()`에 `accuracy_summary` 파라미터의 `per_axis` 데이터를 활용하여, 종합 시그널 테이블의 각 축 행에 적중률(%)을 병기한다. 예: "기술적: +42 (적중률 72%)". evaluated_signals가 5건 미만이면 "데이터 부족"으로 표시. 테스트를 먼저 작성한다.
