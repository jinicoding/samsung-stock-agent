## Session Plan

### Task 1: 수급 분석 모듈 구축 — 외국인/기관 매매 동향 해석
Files: tests/test_supply_demand_analysis.py, src/analysis/supply_demand.py
Description: DB의 foreign_trading, foreign_ownership 데이터를 분석하는 모듈을 구축한다. 테스트를 먼저 작성한다. 핵심 기능: (1) 외국인/기관 N일 연속 순매수/순매도 카운트, (2) N일 누적 순매매 합계, (3) 외국인 보유비율 변화 추이(증가/감소/횡보), (4) 수급 종합 판정(매수 우위/매도 우위/중립). 입력은 list[dict] 형태의 DB rows, 출력은 분석 결과 dict. foreign_trading rows: {date, institution, foreign_total, individual, other_corp}. foreign_ownership rows: {date, ownership_pct, foreign_shares, ...}.

### Task 2: 일일 리포트에 수급 섹션 추가
Files: src/analysis/report.py, tests/test_report.py
Description: generate_daily_report()가 수급 분석 결과도 받아서 리포트에 포함하도록 확장한다. 기존 indicators 파라미터에 더해 supply_demand 파라미터를 선택적으로 받는다(하위호환 유지). 리포트에 추가할 섹션: (1) 외국인/기관 순매매(당일 + 5일 누적), (2) 연속 순매수/순매도 일수, (3) 외국인 보유비율 변화, (4) 수급 종합 판정. 기존 테스트가 깨지지 않도록 supply_demand=None이면 수급 섹션을 생략한다. 시장 온도 판정(assess_market_temperature)에도 수급 요소를 반영한다.

### Task 3: main.py 일일 파이프라인 완성 — 데이터 수집 → 분석 → 리포트 → 발송
Files: src/main.py, tests/test_main.py
Description: main()을 실제 동작하는 일일 파이프라인으로 구현한다. 흐름: (1) init_db(), (2) fetch_samsung_ohlcv()로 최근 90일 주가 수집 → DB 저장, (3) fetch_foreign_trading()으로 수급 수집 → DB 저장, (4) DB에서 데이터 조회, (5) compute_technical_indicators() 실행, (6) compute_supply_demand_indicators() 실행, (7) generate_daily_report() 실행, (8) send_message()로 텔레그램 발송. 각 단계에서 API 실패 시 해당 섹션만 스킵하고 나머지는 계속 진행(graceful degradation). 테스트에서는 외부 API를 mock하여 파이프라인 흐름을 검증한다.
