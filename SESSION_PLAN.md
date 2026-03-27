## Session Plan

### Task 1: KOSPI 지수 데이터 수집 및 시장 상대강도(RS) 분석 모듈 구축
Files: src/data/kospi_index.py (신규), src/analysis/relative_strength.py (신규), tests/test_relative_strength.py (신규)
Description: KIS API를 사용하여 KOSPI 지수 일봉 데이터를 수집하는 fetcher를 만들고, 삼성전자 vs KOSPI 상대강도를 분석하는 모듈을 구축한다. (1) src/data/kospi_index.py — KIS API 국내주식 업종기간별시세 엔드포인트(/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice, tr_id: FHKUP03500100)로 KOSPI(업종코드 0001) 일봉을 조회. stock_price.py와 동일한 패턴으로 페이지네이션, 중복 제거, 날짜 오름차순 정렬. (2) src/analysis/relative_strength.py — 삼성전자 종가 배열과 KOSPI 종가 배열을 받아 분석: N일(1/5/20) 수익률 비교(삼성전자 vs KOSPI), 상대강도선(RS = 삼성전자/KOSPI) 20일 이동평균 대비 위치로 추세 판정(outperform/underperform/neutral), 초과수익률(alpha) 계산. (3) 테스트를 먼저 작성 — RS 계산 정확성, 추세 판정 로직, 데이터 부족 시 처리를 검증한다.

### Task 2: 상대강도 분석을 종합 시그널·리포트·코멘터리에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Task 1에서 구축한 상대강도 분석을 파이프라인 끝단까지 통합한다. (1) signal.py: compute_composite_signal()에 relative_strength 파라미터 추가(선택적, 하위호환). 상대강도가 outperform이면 종합 점수에 +10~15점, underperform이면 -10~15점 가감. (2) report.py: generate_daily_report()에 relative_strength 파라미터 추가. "📈 시장 대비" 섹션 — KOSPI 등락률(1일/5일/20일), 삼성전자 초과수익률, RS 추세(시장 대비 강세/약세/중립)를 표시. (3) commentary.py: generate_commentary()에 relative_strength 파라미터 추가. "KOSPI 대비 N일 연속 아웃퍼폼" 또는 "시장 대비 약세 전환" 코멘터리 규칙 추가. (4) main.py: KOSPI 데이터 수집→상대강도 분석→리포트 전달 파이프라인 연결. 기존 테스트 호환성 유지하면서 새 테스트 추가.
