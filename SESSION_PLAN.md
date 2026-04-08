## Session Plan

Day 17에서 10축 분석 체계 완성을 선언했으나, 코드를 정밀 검증한 결과 글로벌 매크로(10축)가 **signal.py 가중합에만 반영**되고 나머지 6개 접점에서 누락되어 있다:
- report.py: 파라미터만 받고 HTML 섹션 미생성, 종합 시그널 점수 표시에서도 빠짐
- commentary.py: 글로벌 매크로 파라미터·문장 생성 함수 없음
- database.py: signal_history에 global_macro_score 컬럼 없음
- accuracy.py: AXES 튜플에 global_macro_score 없음 → 축별 적중률 추적 불가
- main.py: conv_scores에 global_macro_score 미포함 → 수렴 분석에서 제외

이번 세션에서 이 미완성 통합을 완료하여 10축이 데이터 수집→분석→시그널→수렴→DB→정확도→리포트→코멘터리 전체를 관통하게 한다.

### Task 1: 글로벌 매크로 10축 통합 — DB·정확도·수렴 연결
Files: src/data/database.py, src/analysis/accuracy.py, src/main.py, tests/test_database.py
Description: (1) database.py의 signal_history 테이블에 global_macro_score 컬럼 추가 (init_db에 ALTER TABLE IF NOT EXISTS 패턴). upsert_signal_history()에 global_macro_score keyword 파라미터 추가, INSERT OR REPLACE 쿼리에 포함. get_signal_history() SELECT에 global_macro_score 추가. (2) accuracy.py의 AXES 튜플에 "global_macro_score" 추가하여 축별 적중률 추적 대상에 포함. (3) main.py의 upsert_signal_history() 호출(라인 208-222)에 global_macro_score 전달. main.py의 conv_scores(라인 191-199)에 "global_macro_score" 키 추가. 테스트를 먼저 작성하고 구현한다.

### Task 2: 글로벌 매크로 리포트·코멘터리 완성 — 투자자 가시화
Files: src/analysis/report.py, src/analysis/commentary.py, tests/test_report.py, tests/test_commentary.py
Description: (1) report.py에 _build_global_macro_section(nasdaq_trend, vix_risk, global_macro_score) 함수 추가: NASDAQ 추세(방향·모멘텀), VIX 리스크 수준, 매크로 스코어를 HTML 섹션으로 렌더링. generate_daily_report() 본문의 반도체 업황 섹션 아래에 글로벌 매크로 섹션 호출 추가. (2) _build_composite_signal_section()에 global_macro_score 라인 추가 (candlestick_score 아래). (3) commentary.py의 generate_commentary()에 nasdaq_trend, vix_risk, global_macro_score 파라미터 추가. _build_global_macro_sentence() 헬퍼 구현: NASDAQ 상승+VIX 안정→"글로벌 환경 우호적", NASDAQ 하락+VIX 급등→"글로벌 리스크 확대" 등. report.py의 generate_commentary() 호출(라인 1169-1176)에 글로벌 매크로 인자 전달. 테스트를 먼저 작성하고 구현한다.
