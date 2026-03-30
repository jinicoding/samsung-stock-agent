## Session Plan

### Task 1: 주간 추이 요약을 리포트·코멘터리·파이프라인에 통합
Files: src/main.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_report.py, tests/test_commentary.py
Description: Day 9 (13:30)에서 구축한 weekly_summary 모듈이 아직 파이프라인에 연결되지 않았다. main.py에서 최근 5거래일 데이터를 조회하여 summarize_weekly()를 호출하고, report.py에 _build_weekly_summary_section() HTML 섹션을 추가하며, commentary.py에 _build_weekly_sentence()로 주간 흐름 요약 자연어 문장을 생성한다. generate_daily_report()와 generate_commentary()에 weekly_summary 파라미터를 추가하고, 기존 테스트를 확장하여 주간 요약 섹션 렌더링과 코멘터리 생성을 검증한다. 이로써 투자자가 '오늘의 스냅샷'과 함께 '이번 주 전체 흐름'을 한 리포트에서 확인할 수 있게 된다.

### Task 2: 반도체 업황(DRAM/NAND 현물가) 데이터 수집 모듈 구축
Files: src/data/semi_market.py, tests/test_semi_market.py
Description: 삼성전자 실적의 핵심 드라이버인 반도체 메모리 시장 데이터를 수집하는 모듈을 구축한다. 공개 소스(TrendForce, DRAMeXchange 등)에서 DDR5/NAND 현물가 추이를 스크래핑하여 가격 변동률, 추세(상승/하락/보합), 전주 대비 변화를 구조화된 딕셔너리로 반환한다. 테스트를 먼저 작성하여 파싱 로직과 추세 판정을 검증한다. 기존 6축(기술·수급·환율·펀더멘털·뉴스·컨센서스)에 '산업 업황'이라는 7번째 축의 데이터 기반을 마련하여, "왜 삼성전자 주가가 움직이는가"의 근본 원인인 메모리 사이클을 분석에 반영할 수 있게 한다.
