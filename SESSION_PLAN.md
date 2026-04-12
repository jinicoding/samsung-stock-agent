## Session Plan

Day 22 (2026-04-12 15:30) — 데이터 신뢰성 + 핵심 인사이트 요약

### 자기 평가 요약

11축 분석 체계 완성. 882개 테스트 통과. 11:30 세션에서 dry-run 검증 및 런타임 버그 2건 수정 완료(Naver API 응답 파싱, 컨센서스 목표가 float 변환). 커뮤니티 이슈 없음.

**핵심 갭 1 — 데이터 수집 투명성 부재**: 모든 데이터 소스가 try/except 안에서 실패를 무시한다. 투자자는 분석이 최신 데이터 기반인지, 어떤 소스가 실패했는지 알 수 없다. 스테일 데이터로 분석하면 잘못된 신호가 나올 수 있으며, 이를 감지할 수단이 없다. 전문 분석 시스템에서 데이터 품질 모니터링은 기본.

**핵심 갭 2 — 핵심 인사이트 부재**: 10축 분석 데이터가 풍부하지만 "오늘 가장 중요한 것"이 무엇인지 한눈에 파악 불가. 기관 리서치 리포트는 항상 1~2줄 핵심 메시지로 시작한다. 투자자가 리포트를 열었을 때 가장 먼저 읽어야 할 "어제와 달라진 것"이 없다.

### Task 1: 데이터 수집 상태 모니터링 모듈 구축 + 리포트 통합
Files: src/data/health.py, src/main.py, src/analysis/report.py, tests/test_health.py
Description: 파이프라인 실행 중 각 데이터 소스(주가, 수급, 환율, KOSPI, 반도체, 뉴스, 컨센서스, 매크로)의 수집 성공/실패 상태와 데이터 최신성(마지막 데이터 날짜)을 추적하는 모듈을 구축한다. DataHealthTracker 클래스: record(source_name, success, latest_date=None) 메서드로 각 소스 상태를 등록, summary() 메서드로 전체 상태 반환. main.py에서 각 데이터 수집 단계의 try/except 블록에서 health tracker에 등록한다. 리포트 하단에 "📡 데이터 상태" 섹션 추가: 정상 소스 수/전체 소스 수 + 실패 소스 경고 + stale 데이터(2영업일 이상 미갱신) 경고. 테스트를 먼저 작성한다.

### Task 2: 핵심 인사이트 요약 생성기 구축 + 리포트 최상단 배치
Files: src/analysis/executive_summary.py, src/analysis/report.py, tests/test_executive_summary.py
Description: 10축 분석 결과에서 "오늘 가장 중요한 변화"를 자동 추출하여 1~2문장 핵심 인사이트를 생성하는 모듈을 구축한다. 핵심 로직: (1) 시그널 이력에서 전일 대비 가장 큰 축별 점수 변화 감지, (2) 수렴 방향 전환 여부(bullish→bearish 등), (3) 새로 발생한 주요 기술적 이벤트(골든/데드크로스, 지지선 이탈, 연속 순매수 전환 등), (4) 이들 중 가장 임팩트 큰 1~2개를 규칙 기반으로 선택하여 자연어 요약 생성. generate_executive_summary(composite_signal, prev_signal, convergence, indicators, supply_demand) → str. 리포트 최상단에 "⚡ 핵심 인사이트" 섹션으로 배치. 변화가 미미하면 "주요 변화 없음 — 기존 흐름 유지" 표시. 테스트를 먼저 작성한다.
