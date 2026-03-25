## Session Plan

### Task 1: 시그널 이력 저장 시스템 구축 — 정확도 추적의 기반
Files: src/data/database.py, src/main.py, tests/test_database.py
Description: 매일의 종합 시그널 결과(점수, 등급, 각 축 점수, 당일 종가)를 기록하는 `signal_history` 테이블을 추가한다. `upsert_signal_history(date, score, grade, technical_score, supply_score, exchange_score, price)` 함수와 `get_signal_history(days)` 조회 함수를 구현한다. init_db()에 테이블 생성 DDL을 추가하고, main.py에서 시그널 계산 후 자동 기록하도록 연결한다. 테스트를 먼저 작성한다. 이 테이블이 쌓이면 "N일 전 매수 신호 후 실제 주가가 올랐는가?"를 검증할 수 있는 기반이 된다.

### Task 2: 리포트에 "오늘의 핵심" 한 줄 요약 추가
Files: src/analysis/report.py, tests/test_report.py
Description: generate_daily_report()의 최상단(종합 판정 바로 아래)에 "오늘의 핵심" 한 줄 요약을 추가한다. `generate_key_insight(indicators, supply_demand, exchange_rate, support_resistance)` 함수를 만들어, 당일 지표 중 가장 주목할 만한 변화(RSI 과매도/과매수 진입, 외국인 N일 연속 매수/매도, 지지선·저항선 근접/돌파, 거래량 급증, 골든/데드크로스 등)를 우선순위 규칙 기반으로 1-2개 선별하여 한 문장으로 압축한다. 테스트를 먼저 작성한다. 숫자 나열이 아닌 "왜 이 숫자가 중요한지"를 설명하는 첫 걸음이다.
