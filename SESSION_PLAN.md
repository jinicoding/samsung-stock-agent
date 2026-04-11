## Session Plan

Day 21 (2026-04-11 15:30) — 유사 패턴 검색: 과거가 말해주는 미래

### 자기 평가 요약

10축 분석 체계 + 멀티타임프레임 필터 + 시나리오 분석까지 완성. 862개 테스트 모두 통과. 커뮤니티 이슈 없음, 버그 없음.

**핵심 갭**: signal_history에 10축 점수가 날짜별로 축적되고 있으나, 이 데이터를 활용한 유사 패턴 검색이 없다. 투자자가 가장 궁금한 "지금과 비슷했던 과거에는 어떻게 됐나?"에 답할 수 없는 상태다. 시나리오 분석이 "앞으로 어떻게 될 수 있나"를 보여준다면, 유사 패턴 분석은 "비슷한 상황에서 실제로 어떻게 됐나"를 실증적으로 보여준다 — 시나리오의 신뢰도를 뒷받침하는 증거 계층이다.

### Task 1: 유사 패턴 검색 모듈 구축 (Historical Pattern Matching)
Files: tests/test_pattern_match.py (신규), src/analysis/pattern_match.py (신규)
Description: signal_history DB에 축적된 10축 점수 이력을 활용하여, 현재 시그널 프로파일과 유사한 과거 날짜를 찾고 이후 주가 변동을 보여주는 모듈을 구축한다. `find_similar_patterns(current_scores, db, top_n=5)` 함수: (1) 10축 점수 벡터를 정규화(-100~+100 → 0~1)하여 유클리드 거리 기반 유사도 계산, (2) 최근 N일(기본 7일)은 자기 상관 방지를 위해 제외, (3) 상위 top_n개 유사 날짜 추출, (4) 각 유사 날짜 이후 1/3/5일 실제 수익률 조회(prices 테이블 활용), (5) 유사 패턴 전체의 평균 수익률·상승 확률(방향 일치율)·최대/최소 수익률 요약 통계 반환. 반환 형식: `{"matches": [{"date", "distance", "similarity", "scores", "forward_returns": {"1d", "3d", "5d"}}], "summary": {"avg_return_1d", "avg_return_3d", "avg_return_5d", "up_ratio_1d", "up_ratio_3d", "up_ratio_5d", "match_count"}}`. NULL 축이 있는 과거 레코드는 해당 축을 거리 계산에서 제외(가용 축만으로 정규화). 데이터 부족(이력 < 20일) 시 None 반환. 테스트를 먼저 작성한다 — 유사도 계산 정확성, NULL 축 처리, 자기상관 제외, forward return 계산, 데이터 부족 엣지케이스 포함 최소 12개 테스트.

### Task 2: 유사 패턴 검색을 리포트·코멘터리·파이프라인에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Task 1에서 구축한 pattern_match 모듈을 일일 파이프라인에 통합한다. 확립된 2단계 패턴(모듈 구축→파이프라인 통합)을 따른다. (1) main.py: 시그널 이력 저장 직후에 find_similar_patterns() 호출 — 현재 시그널의 10축 점수 dict와 db 모듈을 전달. 결과를 generate_daily_report()와 generate_commentary()에 pattern_match 파라미터로 전달. (2) report.py: `_build_pattern_match_section(pattern_match)` 함수 추가 — 시나리오 분석 섹션 바로 아래에 배치. 유사 날짜 목록(날짜·유사도%·이후 수익률)을 HTML 테이블로 렌더링하고, 요약 통계(평균 수익률·상승 확률)를 강조 표시. match_count가 0이면 섹션 생략. (3) commentary.py: `_build_pattern_match_sentence(pattern_match)` 함수 추가 — "과거 유사 구간 5회 중 4회(80%) 상승, 평균 +1.2% (3일)" 형태의 1문장 생성. (4) 테스트: 기존 report/commentary/main 테스트에 pattern_match 관련 케이스 추가. (5) 배관 검증(Day 18 교훈): main.py에서 find_similar_patterns → generate_daily_report/generate_commentary까지 데이터 흐름 end-to-end 확인.
