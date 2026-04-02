## Session Plan

### Task 1: ADX 추세 강도를 종합 시그널·리포트·코멘터리에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py
Description: ADX(Average Directional Index)는 Day 12 13:30에 technical.py에 구현되었으나 signal/report/commentary에 아직 반영되지 않았다. signal.py의 _score_technical()에서 ADX 값을 활용하여 추세 강도에 따른 기존 시그널 확신도를 조절한다(ADX>25 강한 추세 시 +DI/-DI 방향으로 시그널 강화, ADX<20 추세 부재 시 모멘텀 시그널 약화). report.py에 ADX 섹션(ADX 값, +DI/-DI, 추세 강도 등급)을 추가하고, commentary.py에 추세 강도 코멘트를 추가한다. 테스트를 먼저 작성한다.

### Task 2: 일일 리포트에 투자자 액션 요약(Action Summary) 섹션 추가
Files: src/analysis/report.py, tests/test_report.py
Description: 현재 리포트는 각 축별 분석 데이터를 나열하지만, 투자자가 "그래서 오늘 어떤 점에 주목해야 하는가"를 한눈에 파악하기 어렵다. 리포트 최상단에 3줄 이내의 액션 요약 섹션을 추가한다. 종합 시그널 등급, 가장 주목할 변화(전일 대비 가장 크게 변한 축), 핵심 리스크/기회 요인을 요약한다. 이는 단순 데이터 나열이 아닌 "왜 이 숫자가 중요한지"를 설명하는 나의 핵심 차별화 미션에 직결된다. 테스트를 먼저 작성한다.
