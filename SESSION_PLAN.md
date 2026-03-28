## Session Plan

### Task 1: 시그널 추이 분석 — 최근 N일 종합 시그널 변화 추적 및 리포트 통합
Files: src/analysis/signal_trend.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal_trend.py
Description: signal_history 테이블에 매일 저장되는 종합 시그널 데이터를 활용하여, 최근 5일간 시그널 점수·등급의 변화 추이를 분석하는 모듈을 구축한다. (1) `analyze_signal_trend(db_module, days=5)` 함수를 만들어 최근 N일 시그널 히스토리를 조회하고, 점수 변화 방향(개선/악화/횡보), 연속 동일 등급 일수, 점수 변동폭을 계산한다. (2) 리포트에 "📈 시그널 추이" 섹션을 추가하여 최근 5일 점수를 미니 차트(텍스트 기반 스파크라인)로 시각화하고, 추세 방향을 표시한다. (3) 코멘터리에 "시그널이 3일 연속 개선 중" 또는 "매도 신호가 약화되는 추세" 같은 추세 기반 문장을 추가한다. 투자자가 "어제보다 나아지고 있는가?"를 즉시 파악할 수 있게 한다. 테스트를 먼저 작성한다.

### Task 2: 52주 고저·심리적 가격대 분석 모듈 구축
Files: src/analysis/price_context.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_price_context.py
Description: 현재 주가의 역사적 맥락을 제공하는 모듈을 구축한다. (1) `analyze_price_context(prices)` 함수를 만들어 52주(약 250거래일, 보유 데이터 범위 내) 고가·저가를 산출하고, 현재가의 52주 범위 내 백분위 위치(0%=52주 최저, 100%=52주 최고)를 계산한다. (2) 심리적 가격대(1000원 단위 라운드넘버) 중 현재가 근처(±3%) 수준을 식별한다. (3) 52주 고가/저가 근접 여부(5% 이내)를 감지하여 투자자에게 알린다. (4) 리포트에 "📍 가격 위치" 섹션으로 52주 범위 바, 심리적 가격대 근접 여부를 표시한다. (5) 코멘터리에 "52주 최저가 근접" 등의 맥락 문장을 추가한다. 테스트를 먼저 작성한다.
