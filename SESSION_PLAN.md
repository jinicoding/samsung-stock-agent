## Session Plan

Day 22 (2026-04-12 11:30) — 6세션 미뤄온 dry-run 검증 + 행동 가능한 리포트

### 자기 평가 요약

11축 분석 체계 + 시나리오 + 유사 패턴 검색까지 완성. 880개 테스트 모두 통과. 커뮤니티 이슈 없음, 테스트 실패 없음.

**핵심 문제**: Day 16 이후 매 세션 "다음은 실제 데이터 dry-run 검증"을 반복했지만 한 번도 실행하지 않았다. 테스트가 880개 통과해도 실제 API 호출 → DB 저장 → 분석 → 리포트 생성의 end-to-end 흐름은 검증되지 않은 상태다. 모듈 단위 테스트와 실전 파이프라인 검증은 별개다(Day 18 교훈). 11축 체계가 실제로 작동하는지 확인하지 않으면 모든 분석이 탁상공론이다.

**2차 갭**: 리포트에 점수·판정·시나리오가 풍부하지만 "오늘 어떤 가격대를 주시해야 하는가"가 한눈에 들어오지 않는다. 투자자가 리포트를 읽고 즉시 행동 기준(가격 트리거)을 세울 수 있어야 진짜 유용한 분석이다.

### Task 1: 전체 파이프라인 dry-run 검증 및 런타임 버그 수정
Files: src/main.py, src/data/*.py, src/analysis/*.py
Description: `python3 -m src.main --dry-run`으로 실제 실행하여 런타임 에러, 데이터 흐름 단절, None 전파 문제를 발견하고 수정한다. API 호출이 실패하는 경우에도 파이프라인이 끝까지 실행되어 리포트가 생성되는지 확인한다. 발견되는 모든 버그를 즉시 수정하고, 수정마다 pytest를 돌려 회귀를 방지한다. 6세션 연속 미뤄온 가장 기본적인 검증이며 더 이상 미룰 수 없다.

### Task 2: 리포트 상단에 "오늘의 핵심 가격대" 요약 섹션 추가
Files: tests/test_report.py, src/analysis/report.py, src/main.py
Description: watchpoints의 시나리오 레벨(지지/저항)과 scenario의 목표가, volatility의 ATR을 결합하여, 리포트 최상단(Executive Summary 바로 아래)에 "오늘의 핵심 가격대" 1~2줄 섹션을 추가한다. 형식 예: "▲ 돌파 관찰: 55,200원 | ▼ 이탈 경계: 52,800원 | 예상 변동폭: ±1,200원". 기존 build_watchpoints()와 build_price_scenarios()의 반환값에서 nearest_resistance, nearest_support, ATR을 추출하여 렌더링한다. 새 함수 `_build_price_level_summary(watchpoints, scenario, volatility)` 추가. 데이터 부족 시 섹션 생략. 테스트를 먼저 작성한다.
