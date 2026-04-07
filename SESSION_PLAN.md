## Session Plan

### Task 1: 글로벌 매크로 분석 모듈 구축 (NASDAQ 추세 + VIX 리스크 해석)
Files: src/analysis/global_macro.py, tests/test_global_macro_analysis.py
Description: Day 17 이전 세션에서 구축한 데이터 수집 모듈(src/data/global_macro.py)의 NASDAQ/VIX 데이터를 해석하는 분석 모듈을 구축한다. (1) NASDAQ 추세 분석: 5/20일 이동평균, 추세 방향(상승/하락/보합), 모멘텀 강도 산출. (2) VIX 리스크 레벨: VIX 수준별 시장 심리 판정(20 미만=안정, 20~30=경계, 30 이상=공포). VIX 추세(상승=리스크 확대, 하락=리스크 완화). (3) 글로벌 매크로 종합 스코어(-100~+100): NASDAQ 상승+VIX 안정=긍정, NASDAQ 하락+VIX 급등=부정. 테스트를 먼저 작성하고 구현한다.

### Task 2: 글로벌 매크로를 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Task 1에서 구축한 글로벌 매크로 분석을 전체 파이프라인에 통합한다. (1) signal.py: _score_global_macro() 함수 추가, compute_composite_signal()에 global_macro 파라미터 추가, 10번째 축으로 가중치 할당(7%). (2) report.py: 글로벌 매크로 HTML 섹션 추가 — NASDAQ 추세, VIX 레벨, 매크로 스코어 시각화. (3) commentary.py: 매크로 환경에 따른 자연어 해설 생성 ("미국 시장 강세+변동성 안정으로 글로벌 투자심리 우호적" 등). (4) main.py: fetch_nasdaq_index(), fetch_vix_index() 호출 → analyze_global_macro() → 시그널·리포트·코멘터리에 전달. 모듈 구축(Task 1)→파이프라인 통합(Task 2)의 2단계 패턴을 따른다.
