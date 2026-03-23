## Session Plan

### Task 1: MACD(12,26,9) 지표 추가 — 추세/모멘텀 분석 완성
Files: src/analysis/technical.py, src/analysis/report.py, tests/test_technical.py, tests/test_report.py
Description: MACD 라인(EMA12 - EMA26), 시그널 라인(MACD의 EMA9), 히스토그램(MACD - Signal)을 계산하는 함수를 technical.py에 추가한다. compute_technical_indicators() 반환값에 macd, macd_signal, macd_histogram 키를 추가한다. report.py에 MACD 섹션을 추가하여 골든크로스/데드크로스 상태와 히스토그램 방향(확장/수축)을 표시한다. 시장온도 판정에도 MACD 크로스 상태를 반영한다. 테스트를 먼저 작성한다: EMA 계산 정확성, 골든/데드 크로스 판정, 데이터 부족 시 None 반환, 히스토그램 부호 검증.

### Task 2: 볼린저 밴드(20,2) 지표 추가 — 변동성 분석 도입
Files: src/analysis/technical.py, src/analysis/report.py, tests/test_technical.py, tests/test_report.py
Description: 20일 이동평균 기반 볼린저 밴드(상단/하단 = MA20 ± 2σ)를 계산하는 함수를 technical.py에 추가한다. compute_technical_indicators() 반환값에 bb_upper, bb_lower, bb_width(밴드폭%), bb_pctb(%B 위치)를 추가한다. report.py에 볼린저 밴드 섹션을 추가하여 현재가의 밴드 내 위치(상단 근접/하단 근접/중심대), 밴드폭 상태(수축=변동성 감소=돌파 임박 가능/확장=변동성 증가)를 표시한다. 테스트를 먼저 작성한다: 밴드 계산 정확성, %B 범위 검증, 데이터 부족 시 None 반환, 밴드폭 계산.
