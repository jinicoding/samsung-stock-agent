## Session Plan

### Task 1: 다축 수렴 분석(Multi-Axis Convergence Analysis) 모듈 구축
Files: src/analysis/convergence.py (신규), tests/test_convergence.py (신규)
Description: 현재 9축 종합 시그널은 각 축의 점수를 가중평균하여 하나의 점수로 합산할 뿐, "몇 개의 축이 같은 방향을 가리키는가"를 감지하지 못한다. 다축 수렴 분석 모듈을 구축하여: (1) 각 축의 개별 점수(technical_score, supply_score, exchange_score, fundamental_score, news_score, consensus_score, semiconductor_score, volatility_score, candlestick_score)를 입력받아 방향(bullish/bearish/neutral)을 분류하고(임계값: ±15), (2) 동일 방향 축의 개수로 수렴도(strong: 7+축, moderate: 5-6축, weak: 3-4축, mixed: 2-축 동의)를 판정하며, (3) 수렴하는 축 이름 목록과 충돌하는 축 이름 목록, conviction 레벨(0-100)을 반환한다. 이를 통해 투자자가 "현재 시그널이 얼마나 신뢰할 만한가"를 한눈에 파악할 수 있게 된다. 테스트를 먼저 작성한다.

### Task 2: 다축 수렴 분석을 리포트·코멘터리·파이프라인에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Task 1에서 구축한 convergence 모듈을 일일 파이프라인에 통합한다. (1) main.py에서 compute_composite_signal() 반환값의 개별 축 점수들을 analyze_convergence()에 전달하여 수렴도를 계산하고, (2) report.py의 종합 시그널 섹션 바로 아래에 수렴도 등급·수렴 축 목록·conviction을 HTML로 표시하며("🎯 시그널 수렴도: Strong — 9축 중 7축 강세 합의"), (3) commentary.py에서 수렴도에 따른 자연어 해설을 생성한다("기술·수급·펀더멘털 등 7개 축이 동시에 강세를 가리키고 있어 시그널 확신도가 높습니다" / "기술적 분석과 수급이 상충하는 혼조세로 관망이 필요합니다"). generate_daily_report() 함수 시그니처에 convergence 파라미터를 추가하고, 기존 테스트를 확장한다.
