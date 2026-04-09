## Session Plan

### Task 1: 글로벌 매크로 리포트 섹션 추가 — NASDAQ·VIX 현황 HTML 표시
Files: src/analysis/report.py, tests/test_report.py
Description:
10축 중 글로벌 매크로만 유일하게 리포트에 독립 섹션이 없다.
`nasdaq_trend`, `vix_risk`, `global_macro_score`가 `generate_daily_report()`에 전달되지만
코멘터리에만 반영될 뿐 리포트 본문에 HTML 섹션이 빠져 있다.
`_build_global_macro_section()` 함수를 구현하여:
1. NASDAQ 추세(상승/하락/보합, MA 대비 위치)
2. VIX 리스크 수준(안정/경계/공포/극단)
3. 매크로 스코어(-100~+100)
를 한눈에 보여주는 HTML 섹션을 추가한다.
반도체 업황 섹션(`_build_semiconductor_section`) 다음, 수렴 분석 섹션 앞에 배치한다.
테스트를 먼저 작성한다.

### Task 2: 리포트 섹션 간결화 — 중복 정보 제거 및 핵심 지표 압축
Files: src/analysis/report.py, tests/test_report.py
Description:
10축 분석 체계가 완성되면서 리포트가 과도하게 길어져 Telegram 4096자 제한에 걸릴
가능성이 높고 가독성이 떨어진다. 각 분석 섹션의 HTML을 감사하여:
1. 수치와 라벨이 코멘터리와 본문에서 이중 표시되는 부분 식별
2. 각 섹션의 핵심 정보 1~2줄로 압축 가능한 부분 리팩토링
3. 데이터가 없거나 중립인 축은 섹션 자체를 생략하여 리포트 길이를 줄인다
기존 테스트가 깨지지 않도록 주의하며, 압축 전후 예상 길이 비교 테스트를 추가한다.
