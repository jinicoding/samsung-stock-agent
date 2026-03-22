## Session Plan

### Task 1: main.py 일일 파이프라인 완성 (수집→분석→리포트→발송)
Files: src/main.py, tests/test_main.py
Description: main.py는 init_db()만 호출하는 빈 껍데기다. 실제 동작하는 일일 파이프라인을 구현한다: (1) 백필 — 주가/수급/환율 데이터 최신화 (backfill 모듈 재활용) (2) DB에서 최근 60일 주가 + 20일 수급/보유비율 데이터 조회 (3) compute_technical_indicators + analyze_supply_demand 실행 (4) generate_daily_report로 HTML 생성 (5) telegram send_message로 발송. --dry-run 플래그로 발송 없이 리포트만 stdout 출력하는 옵션 추가. 주가 데이터가 없으면 리포트 생성하지 않는 안전장치. 테스트는 DB/API를 모킹하여 파이프라인 흐름만 검증.

### Task 2: 환율 분석을 리포트에 통합
Files: src/analysis/report.py, tests/test_report.py
Description: 환율 데이터는 이미 수집·저장되지만 리포트에 쓰이지 않는다. 리포트에 환율 섹션을 추가한다: (1) 당일 USD/KRW 종가 (2) 전일 대비 변동률 (3) 환율 5일/20일 이동평균 대비 위치. 환율은 삼성전자의 수출 매출(반도체/디스플레이)에 직접 영향하므로 투자 판단에 필수. generate_daily_report에 exchange_rate 파라미터 추가 (선택, 하위호환). DB의 exchange_rate 테이블에서 최근 20일 데이터를 조회하여 간단한 분석 후 리포트에 반영. 테스트 먼저 작성.

### Task 3: RSI(상대강도지수) 기술적 지표 추가
Files: src/analysis/technical.py, tests/test_technical.py, src/analysis/report.py, tests/test_report.py
Description: RSI는 과매수/과매도를 판단하는 가장 보편적인 모멘텀 지표. 14일 RSI를 compute_technical_indicators 반환값에 추가한다. 계산: 14일간 상승폭/하락폭 평균 → RS = 평균상승/평균하락 → RSI = 100 - 100/(1+RS). 리포트에 RSI 값과 상태(과매수>70/중립/과매도<30) 표시. 시장 온도(assess_market_temperature)에 RSI를 4번째 스코어링 요소로 반영. 테스트 먼저 작성.
