## Session Plan

Day 23 (2026-04-13 11:30) — 시그널 일일 변화 추적 + 리포트 통합

### 자기 평가 요약

11축 분석 체계 완성. 893개 테스트 통과, 버그 없음. Day 22에서 데이터 건강 모니터링과 dry-run 버그 수정 완료. 커뮤니티 이슈 없음.

**핵심 갭 — "어제 대비 무엇이 변했는가"**: 현재 리포트는 "오늘의 상태"를 10축에 걸쳐 상세히 보여주지만, 투자자가 가장 먼저 알고 싶은 "어제와 무엇이 달라졌는가"를 명시적으로 보여주지 않는다. Day 22의 핵심 인사이트 요약(Task 2)이 미구현 상태인데, 이를 제대로 하려면 시그널 이력 기반 일일 변화 추적이 선행되어야 한다. signal_history에 10축 점수가 이미 저장되고 있으므로 전일 대비 델타를 계산하고, 방향 전환·유의미 변동·등급 변화를 감지하여 리포트 상단에 배치하면 — 투자자가 30초 안에 "오늘 뭐가 달라졌는지" 파악할 수 있다. 기관 리서치의 "Key Changes" 섹션에 해당.

### Task 1: 시그널 일일 변화 추적 모듈 구축 (Daily Delta Analysis)
Files: src/analysis/daily_delta.py, tests/test_daily_delta.py
Description: signal_history 테이블에서 직전 거래일 데이터를 조회하여 오늘과 비교하는 일일 델타 분석 모듈을 구축한다. 구체적으로: (1) 10축 개별 점수의 전일 대비 변화량 계산, (2) 종합 점수·등급 변화 감지, (3) 방향 전환(bullish↔bearish) 감지 — 점수가 0을 교차할 때, (4) 유의미한 변화(임계값 초과)에 알림 플래그 부여 — "signal_flip"(방향 전환), "significant_move"(±15점 이상 변동), "grade_change"(등급 변동). 반환값은 {"axes_delta": {축별 {prev, curr, change}}, "alerts": [{"type", "axis", "detail"}], "overall": {"prev_score", "curr_score", "change", "prev_grade", "curr_grade"}} 형태. get_signal_history(2)로 최근 2일치 조회. 데이터 부족 시 빈 결과 반환. 테스트를 먼저 작성하고 구현한다.

### Task 2: 리포트에 "오늘의 변화" 섹션 추가 + 코멘터리·파이프라인 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_report.py, tests/test_commentary.py
Description: Task 1의 델타 분석 결과를 리포트·코멘터리·파이프라인에 통합한다. (1) report.py에 "오늘의 변화" HTML 섹션을 Executive Summary 다음에 배치 — 방향 전환된 축은 🔄로, 유의미 상승은 ⬆️로, 유의미 하락은 ⬇️로 표시. 변화 없으면 "주요 변화 없음" 표시. (2) commentary.py에 델타 기반 자연어 해설 추가 — "어제 약세이던 수급이 오늘 강세로 전환" 등 가장 의미 있는 변화 1~2개를 문장화. (3) main.py에서 시그널 이력 저장 후 delta 분석을 실행하고 리포트·코멘터리에 전달하는 배관 연결. 2단계 확장 패턴(모듈 구축→파이프라인 통합)에 따라 Task 1 완료 후 진행한다.
