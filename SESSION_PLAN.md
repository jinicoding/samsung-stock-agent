## Session Plan

### Task 1: OBV(On-Balance Volume) + 가격-거래량 다이버전스 감지 모듈 구축
Files: src/analysis/technical.py, tests/test_technical.py
Description: 거래량 분석을 고도화한다. 현재는 5일 평균 대비 거래량 비율만 있어 "거래량이 많다/적다"만 알 수 있고, "거래량이 가격 추세를 확인하는가?"를 판단할 수 없다. OBV(On-Balance Volume)를 구현하여 누적 거래량 흐름을 추적하고, 가격-OBV 다이버전스(가격은 오르는데 OBV는 하락 = 약세 다이버전스, 반대 = 강세 다이버전스)를 감지하는 함수를 추가한다. compute_technical_indicators()의 반환값에 obv, obv_ma20, obv_divergence 필드를 추가한다. 테스트를 먼저 작성한다: OBV 계산 정확성, 상승일/하락일 누적, 다이버전스 감지(강세/약세/없음), 데이터 부족 시 None 처리.

### Task 2: OBV 다이버전스를 종합 시그널·코멘터리·리포트에 통합
Files: src/analysis/signal.py, src/analysis/commentary.py, src/analysis/report.py, src/main.py, tests/test_signal.py, tests/test_commentary.py, tests/test_report.py
Description: Task 1에서 구축한 OBV 분석을 파이프라인 끝단까지 연결한다. (1) signal.py의 _score_technical()에 OBV 다이버전스 반영 — 약세 다이버전스면 -30점, 강세 다이버전스면 +30점 가산. (2) commentary.py에 다이버전스 경고 문장 추가 — "거래량이 가격 상승을 뒷받침하지 않아 주의가 필요합니다" / "거래량 흐름이 반등 가능성을 시사합니다". (3) report.py에 OBV 섹션 추가 — OBV 값, 20일 MA, 다이버전스 상태를 HTML로 표시. 테스트를 먼저 작성하여 각 모듈의 OBV 통합을 검증한다.
