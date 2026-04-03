## Session Plan

### Task 1: 종합 시그널 섹션에 변동성·캔들스틱 점수 표시 누락 버그 수정
Files: src/analysis/report.py, tests/test_report.py
Description: `_build_composite_signal_section()`에서 `volatility_score`와 `candlestick_score`가 종합 판정 섹션에 표시되지 않는 버그를 수정한다. signal.py에서 두 축의 점수를 계산하고 가중치도 반영하지만, 리포트의 종합 판정 섹션에는 semiconductor_score까지만 표시되고 변동성·캔들스틱은 누락되어 있다. 기존 semiconductor_score 표시 블록 아래에 volatility_score(가중치 포함)와 candlestick_score(가중치 포함)를 추가 표시한다. 테스트를 먼저 작성하여 누락을 확인한 뒤 수정한다.

### Task 2: 리포트 상단에 핵심 대시보드 섹션 추가
Files: src/analysis/report.py, tests/test_report.py
Description: 리포트 최상단(종합 판정 위)에 3-4줄짜리 핵심 대시보드를 추가한다. 현재가·등락률·종합 등급·점수·전일 대비 점수 변화·오늘의 주목 포인트(가장 점수가 높거나 낮은 축, 또는 특이 이벤트) 1가지를 한눈에 볼 수 있도록 압축 표시한다. 투자자가 리포트를 열었을 때 3초 안에 핵심을 파악할 수 있어야 한다. `generate_daily_report()`에 `_build_dashboard_section()` 함수를 추가하고, signal_trend의 score_change를 활용하여 전일 대비 변화를 표시한다. 테스트를 먼저 작성한다.
