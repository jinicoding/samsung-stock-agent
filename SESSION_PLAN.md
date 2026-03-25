## Session Plan

### Task 1: 지지/저항선 분석 모듈 구축
Files: src/analysis/support_resistance.py, tests/test_support_resistance.py
Description: 최근 N일 가격 데이터에서 핵심 지지선·저항선을 자동 도출하는 모듈을 만든다. 세 가지 방법을 결합한다: (1) 피봇 포인트(전일 고가/저가/종가 기반 클래식 피봇 — PP, S1, S2, R1, R2), (2) 최근 20일 스윙 고점·저점(local extrema) 기반 수평 지지/저항, (3) 주요 이동평균선(MA20, MA60)을 동적 지지/저항으로 포함. 반환값은 `{"pivot": {...}, "swing_levels": [...], "ma_levels": {...}, "nearest_support": float, "nearest_resistance": float}` 형태로, 현재가 기준 가장 가까운 지지선과 저항선을 바로 꺼낼 수 있게 한다. 테스트를 먼저 작성한다.

### Task 2: 지지/저항선을 리포트·파이프라인에 통합
Files: src/analysis/report.py, src/main.py, tests/test_report.py, tests/test_main.py
Description: Task 1에서 만든 지지/저항선 분석을 일일 리포트 HTML에 반영하고, main.py 파이프라인에 연결한다. 리포트에 "📍 주요 가격대" 섹션을 추가하여 nearest_support, nearest_resistance, 피봇 포인트, 현재가의 밴드 내 위치(%)를 표시한다. 투자자가 "지금 가격이 어디쯤에 있는지"를 한눈에 볼 수 있는 시각적 게이지를 포함한다. generate_daily_report()에 support_resistance 파라미터를 추가하고, main.py에서 분석 결과를 전달한다. 기존 테스트를 깨지 않으면서 새 섹션 테스트를 추가한다.
