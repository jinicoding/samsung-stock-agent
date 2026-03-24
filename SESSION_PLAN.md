## Session Plan

### Task 1: USD/KRW 환율 분석 모듈 구축
Files: tests/test_exchange_rate_analysis.py (신규), src/analysis/exchange_rate.py (신규)
Description: 수집만 하고 분석에 전혀 사용하지 않던 USD/KRW 환율 데이터를 활용하는 분석 모듈을 구축한다. 삼성전자는 매출의 ~80%가 해외에서 발생하는 수출 기업이므로 환율은 실적과 직결된다. 구현 항목: (1) 환율 현재가·등락률(1일/5일/20일), (2) 환율 이동평균(5일/20일) 및 추세 판정(원화강세/원화약세/보합), (3) 주가-환율 상관관계 분석(최근 20일 종가 기준 피어슨 상관계수). 테스트를 먼저 작성하고 구현한다.

### Task 2: 환율 분석을 일일 리포트·파이프라인에 통합
Files: src/analysis/report.py, tests/test_report.py, src/main.py, tests/test_main.py
Description: Task 1에서 만든 환율 분석 결과를 리포트 HTML과 main.py 파이프라인에 연결한다. 리포트에 "💱 환율 동향" 섹션을 추가하여 USD/KRW 현재가, 추세(원화강세↓/약세↑), 주가-환율 상관계수, 투자 시사점(예: "원화 약세 구간 — 수출 실적 개선 기대")을 표시한다. main.py에서 get_exchange_rates(20)을 조회하고 분석 함수를 호출하여 generate_daily_report에 전달하는 흐름을 완성한다. 기존 테스트와의 하위 호환성을 유지한다(exchange_rate 파라미터 기본값 None).
