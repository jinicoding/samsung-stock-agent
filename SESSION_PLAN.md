## Session Plan

Day 11까지 7축 종합 시그널 체계를 완성했다. 방향 판단은 충실하지만,
투자자가 포지션을 잡기 위해 필요한 "리스크 수준"을 알려주지 못한다.
OHLCV 데이터가 있는데 close만 활용하는 것은 낭비다.
이번 세션에서 변동성 분석 모듈을 구축하여 "방향 + 리스크"라는
완성된 분석 프레임을 만든다.

### Task 1: 변동성 분석 모듈 구축 (ATR + 역사적 변동성 + 변동성 체제)
Files: tests/test_volatility.py, src/analysis/volatility.py
Description:
- OHLCV 데이터를 활용한 변동성 분석 모듈을 구축한다. 테스트를 먼저 작성한다.
  1. ATR(14) — True Range(당일고가-저가, 당일고가-전일종가, 전일종가-당일저가 중 최대)의 14일 이동평균으로 일일 예상 변동폭 산출
  2. 역사적 변동성(HV20) — 20일 로그수익률 표준편차를 연율화 (× sqrt(252))
  3. 변동성 백분위 — 현재 ATR이 최근 60일 ATR 분포에서 몇 번째 백분위인지 (0~100)
  4. 변동성 체제 판정 — 백분위 80% 이상: 고변동성, 20% 이하: 저변동성, 그 외: 보통
  5. 볼린저 밴드폭 수축 감지 — bandwidth가 60일 최저 근처(하위 20%)이면 "에너지 축적" 시그널
- 반환값: {"atr": float, "atr_pct": float (ATR/종가%), "hv20": float, "volatility_percentile": float, "volatility_regime": str, "bandwidth_squeeze": bool}

### Task 2: 변동성 분석을 리포트·코멘터리·파이프라인에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description:
- Task 1의 변동성 분석 결과를 파이프라인 전체에 통합한다.
  1. main.py — compute_volatility() 호출을 파이프라인에 삽입, 결과를 report/commentary에 전달
  2. report.py — "변동성 분석" HTML 섹션 추가: ATR 기반 일일 예상 변동폭(±원), 변동성 백분위(%), 변동성 체제, 밴드폭 수축 여부
  3. commentary.py — 변동성 체제에 따른 자연어 코멘터리:
     - 고변동성: "변동성 확대 구간으로 리스크 관리 강화가 필요합니다"
     - 저변동성+수축: "변동성 수축 구간으로 방향성 돌파에 대비할 필요가 있습니다"
     - 보통: 별도 언급 없음
  4. 기존 테스트에 변동성 관련 케이스를 추가하여 전체 통과 확인
- 변동성은 시그널 점수 자체에 가중치로 반영하지 않고, "맥락 정보"로만 표시한다.
  (방향 시그널에 리스크 경고를 병기하는 형태. 가중치 변경은 다음 세션에서 평가 후 결정.)
