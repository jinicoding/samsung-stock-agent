## Session Plan

### Task 1: 볼린저 밴드(20,2) 지표 추가 — 변동성 분석 도입
Files: src/analysis/technical.py, src/analysis/report.py, tests/test_technical.py, tests/test_report.py
Description: 볼린저 밴드(20일 SMA ± 2σ)를 기술적 분석 모듈에 추가한다. compute_technical_indicators에 bb_upper, bb_lower, bb_width, bb_pctb(현재가의 밴드 내 위치, 0~1) 키를 추가. 리포트에 밴드 위치(%B)와 밴드폭(변동성 수준)을 표시하고, 시장온도 판정에 반영한다(%B > 1.0이면 밴드 상단 돌파 = 과열, %B < 0이면 하단 이탈 = 침체). 테스트를 먼저 작성한다.

### Task 2: 환율(USD/KRW) 분석을 일일 리포트에 통합
Files: src/analysis/exchange_rate.py (신규), src/analysis/report.py, src/main.py, tests/test_exchange_rate_analysis.py (신규), tests/test_report.py
Description: 수집만 하고 사용하지 않는 환율 데이터를 분석 모듈로 만들어 리포트에 통합한다. exchange_rate.py에서 당일 환율, 전일 대비 변동, 5일/20일 이동평균, 추세(원화 강세/약세/보합)를 계산. 삼성전자는 수출 비중이 높아 원화 약세 → 실적 긍정 / 원화 강세 → 실적 부정 맥락을 리포트에 한 줄 해설로 추가. main.py에서 exchange_rate 데이터를 조회하여 report에 전달하도록 파이프라인을 확장한다. 테스트를 먼저 작성한다.
