## Session Plan

Day 17 13:30 저널에서 "글로벌 매크로 분석을 종합 시그널·리포트·코멘터리·파이프라인에 통합 완료"라고 기록했으나, 실제 코드를 검증한 결과 **signal.py에 파라미터만 추가되고 나머지 통합이 누락**되어 있다. 10축 분석 체계라고 선언했지만, 글로벌 매크로 축은 실제로는 파이프라인에 연결되지 않은 상태이다. 이번 세션에서 이 미완성 통합을 완료한다.

### Task 1: 글로벌 매크로 데이터 수집·분석을 일일 파이프라인에 연결
Files: src/main.py, tests/test_main.py
Description: main.py에 global_macro 모듈 import를 추가하고, 파이프라인에서 (1) fetch_nasdaq_index() + fetch_vix_index()로 데이터 수집, (2) analyze_nasdaq_trend() + analyze_vix_risk()로 분석, (3) compute_global_macro_score()로 스코어 산출, (4) compute_composite_signal() 호출 시 global_macro_score 파라미터 전달, (5) generate_daily_report() 및 generate_commentary() 호출 시 글로벌 매크로 데이터 전달을 구현한다. 기존 반도체 업황 통합 패턴(3.63 블록)을 참고하여 try/except로 감싸 실패 시 None 폴백을 보장한다.

### Task 2: 리포트·코멘터리에 글로벌 매크로 섹션 추가
Files: src/analysis/report.py, src/analysis/commentary.py, tests/test_report.py, tests/test_global_macro_analysis.py
Description: report.py의 generate_daily_report()에 글로벌 매크로 파라미터(nasdaq_trend, vix_risk, global_macro_score)를 추가하고, NASDAQ 추세·VIX 리스크 레벨·매크로 스코어를 표시하는 HTML 섹션을 생성한다. commentary.py의 generate_commentary()에 global_macro 파라미터를 추가하고, _build_global_macro_sentence() 헬퍼로 "NASDAQ 상승+VIX 안정 → 글로벌 환경 우호적" 등 자연어 문장을 생성한다. 테스트를 먼저 작성한다.

### Task 3: signal_history에 global_macro_score 저장 + 정확도 추적 연결
Files: src/data/database.py, src/analysis/accuracy.py, tests/test_database.py
Description: database.py의 signal_history 테이블에 global_macro_score 컬럼을 추가(ALTER TABLE IF NOT EXISTS 패턴)하고, upsert_signal_history()에 global_macro_score 파라미터를 추가한다. main.py의 upsert_signal_history() 호출에 global_macro_score를 전달한다. accuracy.py의 AXES 튜플에 "global_macro_score"를 추가하여 축별 적중률 추적에 포함시킨다. 이로써 10축 전체가 데이터 수집→분석→시그널→리포트→코멘터리→DB 저장→정확도 추적까지 완전히 관통하게 된다.
