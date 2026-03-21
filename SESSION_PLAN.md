## Session Plan

### Task 1: 일일 분석 리포트 생성기 구축
Files: src/analysis/report.py, tests/test_report.py
Description: 기술적 지표(compute_technical_indicators 결과)를 투자자가 읽기 좋은 HTML 텔레그램 메시지로 변환하는 모듈을 만든다. 포맷: (1) 현재가 및 전일 대비 등락, (2) 이동평균선 위치 해석 (정배열/역배열/골든크로스/데드크로스), (3) 거래량 이상 감지, (4) 종합 시장 온도 (강세/중립/약세). 테스트를 먼저 작성한다.

### Task 2: main.py 일일 파이프라인 완성
Files: src/main.py, tests/test_main.py
Description: main.py를 실제 동작하는 일일 파이프라인으로 완성한다: DB 초기화 → 주가 데이터 수집(fetch + upsert) → 기술적 분석 실행 → 리포트 생성 → 텔레그램 발송. 각 단계의 실패를 처리하고, 데이터 수집 없이도 기존 DB 데이터로 분석/리포트가 동작하도록 fallback을 둔다. KIS API 호출을 mock하는 테스트를 작성한다.

### Task 3: 수급 분석 모듈 구축
Files: src/analysis/supply_demand.py, tests/test_supply_demand_analysis.py
Description: 외국인/기관 순매매 데이터와 외인 지분율을 분석하는 모듈을 만든다. 핵심 지표: (1) 외국인 N일 연속 순매수/순매도 카운트, (2) 기관 순매매 추세, (3) 외인 지분율 변화 방향, (4) 수급 종합 신호 (외인+기관 동시 매수 = 강력 매수세 등). 이 분석 결과를 Task 1의 리포트에 통합할 수 있는 dict 형태로 반환한다.
