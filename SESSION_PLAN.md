## Session Plan

### Task 1: 반도체 업황 지표 수집 및 분석 모듈 구축
Files: src/data/semiconductor.py, src/analysis/semiconductor.py, tests/test_semiconductor.py, tests/test_semiconductor_analysis.py
Description: 삼성전자의 핵심 사업인 메모리 반도체 업황을 추적하는 데이터 수집 모듈과 분석 모듈을 구축한다. (1) 데이터 수집층(src/data/semiconductor.py): Naver Finance에서 SK하이닉스(000660) 주가를 가져와 메모리 반도체 동반 주가 지표로 활용하고, 필라델피아 반도체 지수(SOX) 추이를 수집한다. (2) 분석층(src/analysis/semiconductor.py): SK하이닉스 대비 삼성전자의 상대 성과, SOX 지수 추세(상승/하락/횡보), 반도체 섹터 모멘텀 스코어(-100~+100)를 산출한다. 테스트를 먼저 작성하고 구현한다. 이 세션에서는 모듈 구축만 하고, 파이프라인 통합은 다음 세션에서 진행한다.

### Task 2: 시장 레짐 분류 모듈 구축
Files: src/analysis/market_regime.py, tests/test_market_regime.py
Description: 현재 시장 환경을 5단계(강세장/상승추세/횡보장/하락추세/약세장)로 분류하는 메타 분석 모듈을 구축한다. 기존 기술적 지표(이동평균 배열, RSI, MACD 추세), 수급 판정, 환율 추세, 상대강도, 시그널 추이 방향 등 이미 계산된 분석 결과들을 입력으로 받아 종합적인 시장 레짐을 판정한다. 레짐별 특성 설명(예: "강세장에서는 눌림목 매수 전략이 유효"), 레짐 전환 감지(이전 레짐 대비 변화), 레짐 지속 기간을 출력한다. 이 레짐 정보는 향후 코멘터리와 리포트에 통합되어, 투자자에게 "지금 어떤 장인가"라는 큰 그림을 제공한다. 테스트를 먼저 작성하고 구현한다.
