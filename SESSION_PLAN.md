## Session Plan

### Task 1: 멀티타임프레임 분석 모듈 구축 — 주봉 추세 맥락 추가
Files: src/analysis/timeframe.py, tests/test_timeframe.py
Description: 일봉 OHLCV 데이터를 주봉으로 리샘플링하여 주간 추세(MA5w/MA13w, RSI_weekly, 주봉 추세방향)를 산출하는 모듈을 구축한다. 현재 시스템은 일봉 데이터만 분석하여 "나무만 보고 숲을 못 보는" 한계가 있다. 주봉 추세가 상승인데 일봉이 과매도이면 매수 기회, 주봉도 하락이면 추가 하락 경계 — 이런 멀티타임프레임 맥락을 제공해야 실전 투자자에게 유용하다. 일봉 데이터(최소 60일)를 주봉으로 변환하고, 주봉 MA(5주/13주)·RSI(14주)·추세방향을 계산하여 일봉 시그널과의 정합성(alignment)을 판정한다. 테스트를 먼저 작성하고 구현한다.

### Task 2: 멀티타임프레임 분석을 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py
Description: Task 1에서 구축한 멀티타임프레임 분석을 파이프라인 전체에 통합한다. (1) signal.py: 주봉-일봉 정합성(alignment)에 따라 종합 시그널의 확신도를 조절 — aligned이면 시그널 강화(+15%), conflicting이면 약화(-15%). 별도 축이 아닌 기존 시그널의 필터/증폭기로 작동. (2) report.py: 주봉 추세 섹션 HTML 추가 (주봉 MA 위치, RSI, 추세방향, 일봉과의 정합성). (3) commentary.py: 멀티타임프레임 맥락 자연어 해설 추가. (4) main.py: 파이프라인에서 timeframe 분석 호출 및 결과 전달. 모든 변경에 대해 테스트 추가.
