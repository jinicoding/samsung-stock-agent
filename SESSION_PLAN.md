## Session Plan

### Task 1: 축별 정확도 대시보드를 리포트에 통합 — 적응형 가중치 투명성 확보
Files: src/analysis/report.py, tests/test_report.py
Description:
현재 `_build_accuracy_section()`은 전체 1/3/5일 적중률만 표시한다.
이를 확장하여:
1. 축별(10축) 5일 적중률을 테이블 형태로 표시 (accuracy_summary['per_axis'] 활용)
2. 적중률 수준 라벨: 70%+ "🟢높음", 50-70% "🟡보통", <50% "🔴낮음"
3. 적응형 가중치 활성 시 `adapted_weights=True`가 composite_signal에 있으면 "⚡ 적응형 가중치 활성" 표시
4. `build_daily_report()` 시그니처에 `composite_signal` dict를 전달받아 adapted_weights 여부 확인
5. 축 이름 한글 매핑: technical→기술적, supply→수급, exchange→환율 등
테스트: per_axis 데이터가 있을 때 축별 적중률이 출력에 포함되는지 검증

### Task 2: 방향성 반영 비대칭 예상 거래 범위 — 시그널 기반 가격 시나리오
Files: src/analysis/watchpoints.py, src/analysis/report.py, tests/test_watchpoints.py
Description:
현재 `compute_daily_range()`는 current_price ± ATR 대칭형이다.
시그널 점수를 활용하여 비대칭 범위를 생성한다:
1. `compute_daily_range()`에 `signal_score: float | None = None` 파라미터 추가
2. signal_score가 있으면 방향 편향 계산: bias_ratio = (signal_score / 100) * 0.3
   - 매수 신호(+) → 상단 확장, 하단 축소
   - 매도 신호(-) → 하단 확장, 상단 축소
   - expected_high = price + ATR * (0.5 + bias_ratio), expected_low = price - ATR * (0.5 - bias_ratio)
3. 결과에 `bias_direction` ("상승편향" | "하락편향" | "중립") 추가
4. 리포트의 watchpoints 섹션에 방향 편향 정보 표시
5. `build_watchpoints()`에도 signal_score 전달 경로 추가
6. main.py에서 signal score를 watchpoints로 전달
테스트: signal_score +50일 때 expected_high가 대칭보다 높고 expected_low가 대칭보다 높은지 검증
