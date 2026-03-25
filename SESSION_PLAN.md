## Session Plan

### Task 1: 시그널 정확도 추적 모듈 구축 — "내 시그널이 맞았는가?"
Files: src/analysis/accuracy.py, tests/test_accuracy.py
Description: signal_history 테이블에 축적된 과거 시그널을 실제 주가 변동과 대조하여 정확도를 계산하는 분석 모듈을 구축한다. 핵심 기능: (1) 시그널 발생 후 N일(1/3/5일) 수익률 계산, (2) 시그널 방향(매수/매도)과 실제 주가 방향 일치 여부 판정, (3) 전체 적중률·평균 수익률 통계 반환. get_signal_history()와 get_prices()에서 데이터를 가져와 날짜 매칭으로 forward return을 계산한다. 데이터가 충분히 쌓이면 자동으로 리포트에 포함할 수 있도록 dict 형태로 반환. 테스트를 먼저 작성한다.

### Task 2: 규칙 기반 자연어 마켓 코멘터리 — 숫자 뒤의 이야기
Files: src/analysis/commentary.py, tests/test_commentary.py, src/analysis/report.py, src/main.py
Description: 분석 결과를 자연어 한국어 코멘터리로 변환하는 모듈을 구축한다. 종합 시그널, 기술적 지표, 수급 동향, 지지/저항을 조합하여 "오늘 삼성전자는 외국인 5일 연속 순매수와 MACD 골든크로스가 겹치면서 매수 우세 흐름입니다. 다만 RSI 65로 과매수 영역에 접근 중이므로 단기 조정 가능성에 유의하세요." 같은 자연어 해석을 생성한다. 규칙 기반 템플릿(LLM 호출 없이)으로 구현하여 안정성 확보. 생성된 코멘터리를 리포트 최상단에 배치하고, main.py 파이프라인에 연결한다. 테스트를 먼저 작성한다.
