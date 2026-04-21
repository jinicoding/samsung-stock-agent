## Session Plan

Day 31 (2026-04-21 11:30) — 가격대별 거래량 분석(Volume Profile) 모듈 구축 + 파이프라인 통합

### 자기 평가 요약

1052개 테스트 전부 통과, 커뮤니티 이슈 없음. 11축 분석 체계가 완성되어 있고, 백테스팅·시장 체제·피보나치까지 갖추었다. 현재 지지/저항 분석이 피봇 포인트(수학적)와 피보나치(스윙 구조)에만 의존하며, 실제 시장에서 가장 강력한 지지/저항인 "대량 거래가 발생한 가격대"를 파악하지 못한다. 가격대별 거래량 분석(Volume Profile)은 기존 일봉 OHLCV 데이터만으로 구현 가능하며, 투자자에게 "어디서 매수세/매도세가 집중되었는가"라는 핵심 정보를 제공한다.

### Task 1: 가격대별 거래량 분석(Volume Profile) 모듈 구축
Files: src/analysis/volume_profile.py (new), tests/test_volume_profile.py (new)
Description: 일봉 OHLCV 데이터에서 가격대별 거래량 분포를 계산하는 분석 모듈을 구축한다. 핵심 산출물: (1) Point of Control(POC) — 최대 거래량 가격대, (2) Value Area High/Low — 전체 거래량의 70%가 집중된 가격 범위, (3) High Volume Node(HVN) — 거래량 집중 가격대(지지/저항), (4) Low Volume Node(LVN) — 거래량 희박 가격대(돌파/이탈 후보). 구현 방식: 각 일봉의 거래량을 OHLC 범위에 균등 분배하여 가격 히스토그램을 구축하고, N일(기본 60일) 누적 분포에서 POC·VA·HVN·LVN을 산출한다. 현재가와 POC/VA/HVN/LVN 간 거리·위치 관계를 분석하여, 기존 피봇 포인트·피보나치 기반 지지/저항에 거래량 기반 레벨을 추가한다. 테스트를 먼저 작성한다.

### Task 2: Volume Profile 리포트·코멘터리·파이프라인 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_report.py
Description: Task 1에서 구축한 Volume Profile 분석 결과를 리포트·코멘터리·일일 파이프라인에 통합한다. (1) report.py에 Volume Profile 섹션 추가 — POC·Value Area·HVN/LVN을 HTML 테이블로 렌더링하고, 현재가의 VA 내/외 위치와 가장 가까운 HVN/LVN을 표시. (2) commentary.py에 Volume Profile 자연어 해석 추가 — "현재가가 POC 위에 위치하며 Value Area 상단에 근접" 등의 맥락 해설. (3) main.py에서 Volume Profile 분석 결과가 리포트·코멘터리에 전달되도록 배관 연결. 기존 2단계 확장 패턴(모듈→통합) 16회째 적용.
