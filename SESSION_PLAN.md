## Session Plan

### Task 1: 상대강도(RS) 분석을 일일 파이프라인(main.py)에 통합
Files: src/main.py, tests/test_main.py
Description: kospi_index.py와 relative_strength.py 모듈이 존재하지만 main.py에서 전혀 사용되지 않는다. KOSPI 지수 데이터를 수집하고, compute_relative_strength()를 호출하여 RS 결과를 compute_composite_signal()과 generate_daily_report()에 전달하도록 main.py를 수정한다. 기존 테스트가 깨지지 않도록 방어적으로 구현하고(KOSPI 수집 실패 시 RS=None으로 폴백), test_main.py에 RS 통합 테스트를 추가한다.

### Task 2: KIS API 기반 기본적 분석(PER/PBR/시가총액/배당수익률) 모듈 구축
Files: src/data/fundamental.py (신규), src/analysis/fundamental.py (신규), tests/test_fundamental.py (신규)
Description: 삼성전자 투자 분석에서 가장 큰 공백은 펀더멘탈(가치평가) 지표다. KIS API의 주식현재가 시세 엔드포인트(/uapi/domestic-stock/v1/quotations/inquire-price)에서 PER, PBR, 시가총액, 배당수익률을 조회하는 데이터 수집 모듈과, 이를 해석하는 분석 모듈을 구축한다. 분석 모듈은 PER/PBR의 과대/적정/저평가 판정, 시가총액 변동 추세를 포함한다. 테스트를 먼저 작성하고 구현한다. 이번 세션에서는 데이터 수집 + 분석까지만 구현하고, 리포트·시그널 통합은 다음 세션으로 넘긴다.
