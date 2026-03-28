## Session Plan

### Task 1: 추세 전환 감지 모듈 구축 — 시그널 컨버전스(convergence) 엔진
Files: src/analysis/trend_reversal.py, tests/test_trend_reversal.py
Description: 기존 기술적 지표(RSI, MACD, 스토캐스틱, 볼린저밴드, OBV, MA괴리율)와 지지/저항선을 5개 카테고리(모멘텀/추세/변동성/거래량/구조)로 분류하여, 각 카테고리별 강세/약세 반전 신호를 감지하고 가중 점수(0~100)로 합산하는 모듈. 핵심은 단일 지표가 아닌 "몇 개 카테고리에서 동시에 신호가 나오는가"로 컨버전스 등급(strong/moderate/weak/none)을 판정하는 것. detect_reversal_signals(tech_indicators, support_resistance) → dict 형태. 테스트를 먼저 작성한다: 강한 강세 반전(4+카테고리), 중간 약세 반전(3카테고리), 혼합 신호, 신호 없음, 데이터 부족 등 최소 10개 케이스.

### Task 2: 추세 전환 감지를 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py
Description: Task 1에서 만든 추세 전환 감지 결과를 파이프라인 끝단까지 연결한다. (1) signal.py: 컨버전스 등급이 strong/moderate일 때 종합 시그널 점수에 보너스/패널티 반영. (2) report.py: "⚡ 추세 전환 감지" 섹션을 종합 시그널 바로 아래에 추가 — 방향(강세/약세), 등급, 감지된 신호 목록을 표시. strong일 때만 별도 강조. (3) commentary.py: strong 컨버전스 시 "다수 지표가 동시에 [강세/약세] 전환을 시사하고 있어 주목할 필요가 있습니다" 같은 자연어 문장 추가. (4) main.py: analyze_support_resistance 결과와 tech indicators를 detect_reversal_signals에 전달. 기존 테스트가 깨지지 않도록 하위 호환성 유지.
