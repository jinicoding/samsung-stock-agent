## Session Plan

### Task 1: 글로벌 매크로 코멘터리 누락 버그 수정 — NASDAQ·VIX 자연어 해설 추가
Files: src/analysis/commentary.py, src/analysis/report.py, tests/test_commentary.py
Description: 10번째 축인 글로벌 매크로(NASDAQ 추세 + VIX 리스크)가 종합 시그널·리포트에는 통합되었으나 자연어 코멘터리(commentary.py)에 반영되지 않는 버그를 수정한다. generate_commentary() 함수에 nasdaq_trend와 vix_risk 파라미터를 추가하고, _build_global_macro_sentence() 헬퍼를 구현한다. 시나리오별 문장: NASDAQ 상승+VIX 안정→"글로벌 기술주 환경이 우호적", NASDAQ 하락+VIX 급등→"글로벌 리스크 확대로 외국인 수급에 부담", 중립→생략. report.py의 generate_commentary() 호출부(line 1169-1176)에도 글로벌 매크로 파라미터를 전달한다. 테스트에서 다양한 매크로 시나리오(강세/약세/중립/데이터 없음)의 코멘터리 생성을 검증한다.

### Task 2: 축별 정확도 대시보드를 리포트에 통합 — 투자자 신뢰도 강화
Files: src/analysis/report.py, tests/test_report.py
Description: 현재 정확도 섹션은 전체 적중률(1/3/5일)만 표시한다. accuracy_summary["per_axis"]에 이미 축별 적중률·평균수익률 데이터가 있으므로, _build_accuracy_section()을 확장하여 각 축(기술적·수급·환율 등)의 5일 적중률을 한 눈에 볼 수 있는 대시보드로 표시한다. 적중률이 70% 이상인 축은 "높음", 50% 미만은 "낮음"으로 라벨링하여 투자자가 어떤 분석 축을 더 신뢰할 수 있는지 즉시 판단할 수 있도록 한다. 적응형 가중치가 적용된 경우(composite_signal에 adapted_weights=True) 가중치 변동 사실도 종합시그널 섹션에 표기하여 "왜 이번 시그널의 가중치가 달라졌는지" 투자자가 이해할 수 있도록 한다.
