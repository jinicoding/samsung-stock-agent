## Session Plan

### Task 1: OBV 다이버전스를 종합 시그널·리포트·코멘터리에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py
Description: Day 5에서 구축한 OBV(On-Balance Volume) 다이버전스 감지가 technical.py의 compute_technical_indicators()에서 계산되지만, signal.py의 종합 점수에 반영되지 않고 report.py에도 표시되지 않는다. (1) signal.py의 _score_technical()에 OBV 다이버전스 반영 — bearish divergence(가격↑+OBV↓)일 때 감점, bullish divergence(가격↓+OBV↑)일 때 가점. (2) report.py에 OBV 다이버전스 경고 섹션 추가 — "⚠️ 가격-거래량 괴리: 가격은 상승 중이나 거래량 동반되지 않음" 등. (3) commentary.py에 OBV 다이버전스 관련 자연어 문장 추가. 테스트를 먼저 작성하고 구현한다.

### Task 2: 다중 지표 수렴 감지 모듈 구축 — "고확신 시그널" 판정
Files: src/analysis/confluence.py (신규), src/analysis/report.py, src/analysis/commentary.py, tests/test_confluence.py (신규), tests/test_report.py
Description: 현재 RSI·MACD·BB·OBV·수급이 각각 독립적으로 점수를 계산하지만, 여러 지표가 같은 방향을 동시에 가리킬 때("수렴") 이를 감지하여 시그널의 확신도를 높이는 모듈을 구축한다. (1) 각 지표의 방향성(매수/매도/중립)을 추출하여 수렴도(0~100%)를 계산 — 예: 5개 지표 중 4개 매수 방향이면 80% 수렴. (2) 수렴 임계값(70% 이상)에서 "고확신 매수 시그널" / "고확신 매도 시그널" 판정. (3) 리포트에 수렴 상태 섹션 추가 — "🎯 4/5 지표 매수 방향 수렴 (고확신)". (4) commentary.py에 수렴 판정 기반 코멘터리 추가. 투자자에게 "여러 지표가 동시에 같은 신호를 보내고 있다"는 메타 분석 정보를 제공하여 리포트의 판단력을 한 단계 높인다. 테스트를 먼저 작성하고 구현한다.
