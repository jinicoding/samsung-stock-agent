## Session Plan

### Task 1: signal_history 테이블에 9축 점수 전체 저장 확대
Files: src/data/database.py, src/main.py, tests/test_database.py, tests/test_main.py
Description: 현재 signal_history 테이블이 technical_score, supply_score, exchange_score 3축만 저장하고 나머지 6축(fundamentals, news, consensus, semiconductor, volatility, candlestick)은 버리고 있다. 9축 전체를 저장해야 축별 정확도 분석이 가능하다. (1) init_db()에서 CREATE TABLE에 6개 컬럼 추가 (REAL DEFAULT NULL — 기존 데이터 호환). 기존 DB 마이그레이션을 위해 ALTER TABLE ADD COLUMN도 init_db() 내에 추가. (2) upsert_signal_history()가 optional kwargs로 6축 점수를 받아 저장. (3) get_signal_history()가 9축 점수 전부 반환. (4) main.py에서 sig dict의 축별 점수를 upsert에 전달. 테스트 먼저 작성.

### Task 2: 축별 예측 정확도 분석 (Per-Axis Accuracy Decomposition)
Files: src/analysis/accuracy.py, src/analysis/report.py, tests/test_accuracy.py, tests/test_report.py
Description: Task 1에서 저장된 9축 점수를 활용하여 각 축이 독립적으로 얼마나 예측력이 있는지 분석한다. (1) accuracy.py에 evaluate_axis_accuracy() 함수 추가: 각 축의 score 부호(양수=강세, 음수=약세)와 실제 forward return 방향을 대조하여 축별 hit rate를 산출. (2) report.py의 시그널 정확도 섹션에 축별 hit rate 테이블 추가: "어떤 축이 가장 예측력이 높은가"를 투자자에게 보여준다. (3) 수렴 강도별 정확도 비교: convergence_level이 strong일 때 vs mixed일 때 overall hit rate 차이를 보여줘서 수렴 분석의 유효성을 검증한다. 테스트 먼저 작성.
