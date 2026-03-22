## Session Plan

### Task 1: RSI(상대강도지수) 기술적 지표 추가
Files: src/analysis/technical.py, tests/test_technical.py
Description: 14일 RSI를 compute_technical_indicators()에 추가한다. RSI는 가장 기본적인 모멘텀 오실레이터로, 과매수(70↑)/과매도(30↓) 판단에 필수적이다. Wilder 방식의 평활 이동평균(exponential smoothing)으로 계산하되, 데이터 부족 시 None 반환. 테스트를 먼저 작성한다: (1) 14일 이상 데이터로 정상 계산, (2) 데이터 부족 시 None, (3) 전부 상승일 때 100에 가까운 값, (4) 전부 하락일 때 0에 가까운 값, (5) 반반일 때 50 근처.

### Task 2: 환율 분석 모듈 구축 및 리포트 통합
Files: src/analysis/exchange_rate.py (신규), src/analysis/report.py, src/main.py, tests/test_exchange_rate_analysis.py (신규)
Description: 이미 수집 중인 USD/KRW 환율 데이터를 분석하여 리포트에 반영한다. (1) src/analysis/exchange_rate.py를 만들어 환율 현재가, 5일/20일 변동률, 추세 판정(원화강세/약세/보합)을 계산. (2) report.py에 환율 섹션을 추가하여 "USD/KRW: 1,380원 (+0.5%, 원화약세 → 수출기업 우호)" 형식으로 표시. (3) main.py에서 get_exchange_rates()를 호출하여 파이프라인에 연결. 삼성전자 실적의 60%+가 해외 매출이므로 환율 맥락은 투자 판단에 필수. 테스트 먼저 작성.

### Task 3: RSI를 리포트에 반영 + 시장온도 판정에 통합
Files: src/analysis/report.py, tests/test_report.py
Description: Task 1에서 추가한 RSI를 리포트에 표시한다. (1) "RSI(14): 45.2 (중립)" 형식으로 기술적 분석 섹션에 추가. RSI 상태를 분류: 70↑ 과매수🔴, 30↓ 과매도🟢, 그 외 중립🟡. (2) assess_market_temperature()에 RSI를 네 번째 스코어링 요소로 추가: 과매수 시 -1 (상승 과열), 과매도 시 +1 (반등 가능성). 테스트 먼저 작성.
