## Session Plan

### Task 1: 기초 기술적 분석 모듈 구축
Files: src/analysis/__init__.py, src/analysis/technical.py, tests/test_technical.py
Description: src/analysis/가 완전히 비어있다. 투자자가 가장 먼저 보는 기초 기술적 지표를 계산하는 모듈을 만든다. DB에서 가격 데이터를 읽어 다음을 계산: (1) 이동평균선 (5일, 20일, 60일), (2) 이동평균 대비 현재가 위치 (%), (3) 최근 N일 가격 변동률, (4) 거래량 변화율 (5일 평균 대비 당일). 입력: list[dict] (DB에서 가져온 OHLCV rows). 출력: dict with all computed indicators. 테스트를 먼저 작성한다.

### Task 2: 일일 파이프라인 완성 (main.py)
Files: src/main.py
Description: 현재 main.py는 init_db()만 호출하고 끝난다. 실제 일일 파이프라인으로 완성한다: (1) DB 초기화, (2) 주가 데이터 수집 (backfill.py 로직 인라인 또는 호출), (3) 수급/환율 데이터 수집, (4) Task 1의 기술적 분석 실행, (5) 텔레그램 리포트 생성 및 발송. 각 단계에서 에러가 발생해도 나머지 단계는 계속 실행. 기존 backfill.py/backfill_supply_demand.py의 로직을 재사용한다.

### Task 3: 텔레그램 일일 리포트 포맷 설계
Files: src/delivery/report.py, tests/test_report.py
Description: 분석 결과를 투자자가 한눈에 파악할 수 있는 HTML 텔레그램 메시지로 포맷한다. 포함 내용: (1) 오늘 종가 및 전일 대비 변동, (2) 이동평균선 상태 (정배열/역배열), (3) 거래량 시그널, (4) 외국인/기관 수급 요약, (5) USD/KRW 환율 동향. 테스트를 먼저 작성한다 — 샘플 데이터로 포맷 함수가 올바른 HTML을 생성하는지 검증.
