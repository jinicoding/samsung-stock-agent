## Session Plan

### Task 1: 글로벌 매크로 데이터 수집 모듈 구축 (NASDAQ + VIX)
Files: src/data/global_macro.py, tests/test_global_macro.py
Description: Naver Finance 해외지수 페이지에서 NASDAQ Composite과 VIX(CBOE 변동성 지수) 일별 데이터를 수집하는 모듈을 구축한다. 기존 `src/data/semiconductor.py`의 `fetch_sox_index()` 패턴을 참고하여 동일한 Naver Finance 크롤링 방식으로 구현한다. `fetch_nasdaq_index(days=60) -> list[dict]` (날짜 오름차순, date/close 키)와 `fetch_vix_index(days=60) -> list[dict]` 두 함수를 구현한다. 삼성전자는 NASDAQ 기술주 심리와 글로벌 공포지수(VIX)에 강한 연동성을 보이므로, 이 데이터가 있어야 "글로벌 리스크 환경이 삼성전자에 미치는 영향"을 해석할 수 있다. 테스트를 먼저 작성한다 (Naver HTML 응답 mock 기반).

### Task 2: 글로벌 매크로 분석 모듈 구축 및 종합 시그널 통합
Files: src/analysis/global_macro.py, tests/test_global_macro_analysis.py, src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py
Description: NASDAQ/VIX 데이터를 분석하는 모듈을 구축하고, 종합 시그널·리포트·코멘터리·파이프라인에 통합한다. `analyze_global_macro(nasdaq_data, vix_data, samsung_prices) -> dict`는 다음을 산출한다: (1) NASDAQ 추세(상승/하락/횡보) 및 5일 수익률, (2) VIX 수준(공포/보통/낙관) — 20 이상 공포, 15 미만 낙관, (3) 삼성전자-NASDAQ 20일 상관계수, (4) 글로벌 매크로 스코어(-100~+100). signal.py에 10번째 축(global_macro, 가중치 8%)을 추가하고, report.py에 글로벌 매크로 HTML 섹션, commentary.py에 자연어 문장을 추가한다. main.py에서 NASDAQ/VIX 수집→분석→시그널 전달 흐름을 연결한다. 기존 "모듈 구축→파이프라인 통합" 2단계 패턴을 한 Task 내에서 완료한다.
