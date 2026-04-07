## Session Plan

### Task 1: 글로벌 매크로 분석을 종합 시그널에 통합 (10축 분석 체계 완성)
Files: src/analysis/signal.py, tests/test_signal.py
Description: compute_composite_signal()에 global_macro_score 파라미터를 추가하고, 기존 9축 가중치를 비례 축소하여 10번째 축(글로벌 매크로, 10%)을 반영한다. 적응형 가중치 시스템(adjust_weights_by_accuracy)에도 global_macro 축을 포함시킨다. 테스트를 먼저 작성하여 글로벌 매크로 스코어가 종합 시그널에 정확히 반영되는지, 가중치 합이 100%를 유지하는지 검증한다.

### Task 2: 글로벌 매크로 분석을 리포트·코멘터리·파이프라인에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, src/analysis/convergence.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: (1) main.py에 fetch_nasdaq_index/fetch_vix_index → analyze_nasdaq_trend/analyze_vix_risk/compute_global_macro_score 호출 체인을 추가하고, 결과를 compute_composite_signal과 generate_daily_report에 전달한다. (2) report.py에 글로벌 매크로 HTML 섹션(NASDAQ 추세, VIX 리스크 레벨, 매크로 스코어)을 추가한다. (3) commentary.py에 글로벌 매크로 환경에 따른 자연어 해설을 추가한다. (4) convergence.py의 다축 수렴 분석에 global_macro_score를 포함시킨다. 테스트를 먼저 작성하여 각 통합 지점이 정확히 동작하는지 검증한다.
