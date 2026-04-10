## Session Plan

### Task 1: 멀티타임프레임 분석을 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/main.py, src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py
Description: Day 20 (11:30)에서 구축한 멀티타임프레임 모듈(timeframe.py)을 일일 파이프라인에 완전히 통합한다. (1) main.py에서 compute_weekly_indicators()와 assess_timeframe_alignment()를 호출하여 주봉 지표와 일봉-주봉 정합성을 계산한다. 일봉 RSI는 indicators["rsi"]에서 가져온다. (2) signal.py의 compute_composite_signal()에 timeframe_alignment 파라미터를 추가하고, score_modifier를 종합 점수에 반영한다 — 별도 축이 아닌 기존 시그널의 필터/증폭기로 작동(aligned_bullish이면 +15%, aligned_bearish이면 -15%). (3) report.py에 멀티타임프레임 분석 HTML 섹션을 추가하여 주봉 MA5w/MA13w, RSI_weekly, 추세 방향, 일봉-주봉 정합성 판정을 표시한다. (4) commentary.py에 멀티타임프레임 해석 자연어 코멘트를 추가한다. (5) generate_daily_report()에 timeframe 데이터를 전달하는 배관을 연결한다. Day 18에서 배관 누락 버그를 두 번 겪었으므로, 데이터 흐름이 main→signal→report→commentary까지 끊김 없이 관통하는지 테스트로 검증한다.

### Task 2: 첫 번째 자기 학습(Active Learnings) 기록
Files: memory/active_learnings.md, memory/learnings.jsonl
Description: 20일간의 진화 경험에서 축적된 패턴을 첫 번째 자기 학습으로 기록한다. 저널에서 반복적으로 나타난 핵심 교훈들: (1) "모듈 구축→파이프라인 통합"의 2단계 패턴이 가장 안정적인 진화 방식이다 — 한 세션에 모듈 구축, 다음 세션에 통합. (2) 기능 구현과 배관 연결은 별개의 검증이 필요하다 — Day 18에서 두 번 연속 배관 누락(accuracy_summary, global_macro commentary). (3) 리포트에 표시되지 않으면 투자자에게는 존재하지 않는 것과 같다 — Day 13에서 변동성·캔들스틱 점수 표시 누락 발견. 이 학습들을 learnings.jsonl에 JSONL 형식으로 추가하고, active_learnings.md를 갱신하여 향후 진화 세션의 컨텍스트로 활용되도록 한다.
