## Session Plan

### Task 1: RSI를 일일 리포트에 표시 + 시장온도 판정에 반영
Files: src/analysis/report.py, tests/test_report.py
Description: RSI(14)가 technical.py에서 계산되지만 리포트에 전혀 표시되지 않는 버그를 수정한다. (1) 리포트에 RSI 값과 과매수(70↑)/과매도(30↓)/중립 상태를 표시하는 섹션 추가. (2) assess_market_temperature()에 RSI를 반영하여 과매수 시 약세 가산, 과매도 시 강세 가산. 테스트를 먼저 작성하고 구현한다.

### Task 2: MACD 지표 추가 (계산 + 리포트)
Files: src/analysis/technical.py, src/analysis/report.py, tests/test_technical.py, tests/test_report.py
Description: MACD(12,26,9) 지표를 구현한다. (1) technical.py에 EMA 헬퍼와 MACD 계산 함수 추가 — MACD line(EMA12-EMA26), Signal line(MACD의 EMA9), Histogram(MACD-Signal) 반환. compute_technical_indicators()에 macd, macd_signal, macd_histogram 키 추가. (2) report.py에 MACD 크로스 상태(골든크로스/데드크로스/수렴/발산) 표시. 테스트 먼저 작성.

### Task 3: 환율 분석을 리포트에 통합
Files: src/analysis/technical.py, src/analysis/report.py, src/main.py, tests/test_report.py
Description: 수집만 되고 사용되지 않는 exchange_rate 데이터를 분석하여 리포트에 추가한다. (1) 환율 분석 함수 추가 — 현재 환율, 5일/20일 변동률, 추세 판단(원화강세/약세/보합). (2) main.py에서 get_exchange_rates()를 호출하여 분석 후 리포트에 전달. (3) 리포트에 "💱 환율 동향" 섹션 추가 — 삼성전자 주가와의 연관성(원화 약세 시 수출 경쟁력↑) 맥락 설명 포함. 테스트 먼저 작성.
