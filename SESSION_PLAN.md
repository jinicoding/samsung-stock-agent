## Session Plan

8축 종합 분석 체계가 완성된 상태에서, 가장 기본적인 기술적 분석 역량이 빠져 있다:
캔들스틱 패턴 인식. 이동평균·모멘텀·거래량·변동성은 있지만, 가격 자체의 형태(도지, 해머, 인걸핑 등)를
읽는 능력이 없다. 투자자가 차트를 볼 때 가장 먼저 보는 것이 캔들 패턴인 만큼,
이 역량을 우선적으로 구축한다.

### Task 1: 캔들스틱 패턴 인식 모듈 구축
Files: tests/test_candlestick.py, src/analysis/candlestick.py
Description:
- OHLCV 데이터에서 핵심 캔들스틱 패턴을 감지하는 분석 모듈을 구축한다. 테스트를 먼저 작성한다.
  1. 단일 캔들 패턴 (최근 1봉): 도지(Doji), 해머(Hammer), 행잉맨(Hanging Man), 마루보즈(Marubozu)
  2. 복합 캔들 패턴 (최근 2~3봉): 강세/약세 인걸핑(Engulfing), 모닝스타(Morning Star), 이브닝스타(Evening Star)
  3. 감지된 패턴 리스트와 종합 패턴 시그널(bullish/bearish/neutral)을 구조화된 딕셔너리로 반환
  4. 각 패턴에 중요도(신뢰도) 가중치를 부여하여 종합 점수(-100~+100) 산출

### Task 2: 캔들스틱 패턴을 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description:
- Task 1에서 구축한 캔들스틱 패턴 인식 결과를 기존 파이프라인 전체에 통합한다.
  1. signal.py — _score_candlestick() 함수 추가, 기술적 분석 점수에 보너스/페널티로 반영 (직접적 축 추가 대신, 기술적 축 내에서 가산)
  2. report.py — "캔들 패턴" HTML 섹션 추가: 감지된 패턴명, 방향(강세/약세), 신뢰도
  3. commentary.py — 주요 패턴 발생 시 자연어 해설 생성 ("강세 인걸핑 패턴이 나타나 단기 반등 가능성을 시사합니다")
  4. main.py — 캔들스틱 분석 호출 추가, 결과를 시그널·리포트·코멘터리에 전달
  5. 각 모듈에 대한 테스트 추가 (테스트 먼저 작성)
