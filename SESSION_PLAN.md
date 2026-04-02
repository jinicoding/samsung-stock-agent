## Session Plan

9축 종합 시그널 시스템이 완성된 상태에서, 핵심 결함을 발견했다:
모든 분석 축이 시장 국면(추세/횡보/고변동)을 구분하지 않고 동일 가중치로 합산된다.
RSI·스토캐스틱은 횡보장에서 유효하고, MA·MACD는 추세장에서 유효한데,
이 구분 없이 합산하면 whipsaw 노이즈가 발생한다.

추세 강도의 표준 지표인 ADX(Average Directional Index)를 먼저 구현하고,
이를 기반으로 시장 레짐 탐지 → 시그널 가중치 동적 조정 체계를 구축한다.

### Task 1: ADX(Average Directional Index) 추세 강도 지표 구현
Files: tests/test_technical.py, src/analysis/technical.py
Description:
- 기술적 분석 모듈에 ADX(14) 지표를 추가한다. TDD: 테스트 먼저 작성.
  1. Wilder smoothing 방식으로 True Range, +DM, -DM, +DI, -DI, DX, ADX를 계산
  2. compute_technical_indicators 결과에 adx, plus_di, minus_di 키 추가
  3. 테스트: 상승 추세 데이터에서 ADX > 25 & +DI > -DI, 횡보 데이터에서 ADX < 20,
     하락 추세에서 -DI > +DI, 데이터 부족 시 None 반환

### Task 2: 시장 레짐 탐지 모듈 구축 및 시그널·리포트·코멘터리 통합
Files: src/analysis/market_regime.py, tests/test_market_regime.py, src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description:
- 새로운 market_regime 모듈을 만들어 현재 시장 상태를 4가지로 분류한다. TDD: 테스트 먼저 작성.
  1. 분류 기준: ADX(추세 강도) + MA 배열(정배열/역배열) + 변동성 레짐(ATR percentile)
     - ADX≥25 + 정배열 → trending_up(상승추세)
     - ADX≥25 + 역배열 → trending_down(하락추세)
     - ADX<20 + 저변동 → ranging(횡보)
     - 고변동성(HV 80th percentile 이상) → volatile(고변동)
  2. signal.py: 레짐별 가중치 미세 조정 (추세장: 기술적↑ 수급↑, 횡보장: 지지저항↑, 고변동: 변동성↑)
  3. report.py: 시장 레짐 섹션 추가 — "현재 시장 국면: 상승추세 (ADX 32)" 형태
  4. commentary.py: 레짐에 따른 자연어 해설 — "추세가 강한 시장에서 기술적 지표의 신뢰도가 높습니다"
  5. main.py: 파이프라인에 market_regime 분석 호출 추가, 결과를 signal/report/commentary에 전달
