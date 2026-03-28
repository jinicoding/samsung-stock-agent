## Session Plan

### Task 1: 기본적 분석 모듈 구축 — PER/PBR/배당수익률/EPS/BPS 수집 및 밸류에이션 분석
Files: src/data/fundamentals.py, src/analysis/fundamentals.py, tests/test_fundamentals.py, tests/test_fundamentals_analysis.py
Description: Naver Finance(finance.naver.com/item/main.naver?code=005930)에서 PER, 추정PER, PBR, 배당수익률, EPS, BPS를 스크래핑하는 데이터 수집 모듈(`src/data/fundamentals.py`)과, 이를 해석하는 분석 모듈(`src/analysis/fundamentals.py`)을 구축한다. 분석 모듈은 밸류에이션 판정(저평가/적정/고평가)을 PER·PBR 각각에 대해 수행하고, trailing PER vs 추정PER 비교로 실적 개선/악화 전망을 도출하며, 배당수익률 매력도를 판정한다. 기존 supply_demand.py의 Naver 파싱 패턴을 참조하되, per_table 영역의 em 태그를 파싱한다. 테스트를 먼저 작성하고 구현한다.

### Task 2: 기본적 분석을 리포트·코멘터리·종합시그널 파이프라인에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/analysis/signal.py, src/main.py, tests/test_report.py, tests/test_commentary.py, tests/test_signal.py
Description: Task 1에서 구축한 기본적 분석 결과를 일일 파이프라인 끝단까지 통합한다. (1) report.py에 밸류에이션 섹션(PER/PBR/배당/밸류에이션 판정)을 추가한다. (2) commentary.py에 PER 고평가/저평가 시 자연어 코멘트를 생성한다. (3) signal.py에 밸류에이션 축을 선택적으로 반영한다(극단적 저평가/고평가 시 보너스/패널티). (4) main.py에서 fundamentals 데이터 수집→분석→리포트 전달 흐름을 추가한다. 이로써 투자자가 "지금 삼성전자가 비싼가 싼가?"를 기술적 분석과 함께 판단할 수 있게 된다.
