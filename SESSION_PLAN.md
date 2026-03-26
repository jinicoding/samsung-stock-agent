## Session Plan

### Task 1: 규칙 기반 자연어 마켓 코멘터리 모듈 구축 — 숫자 뒤의 이야기
Files: src/analysis/commentary.py, tests/test_commentary.py, src/analysis/report.py, src/main.py
Description: 분석 결과를 자연어 한국어 코멘터리로 변환하는 모듈을 구축한다. 종합 시그널, 기술적 지표(RSI·MACD·볼린저·이평선 배열), 수급 동향(외국인/기관 연속매매), 환율 추세, 지지/저항선을 조합하여 2~3문장의 자연어 해석을 생성한다. 예: "외국인 5일 연속 순매수와 MACD 골든크로스가 겹치면서 매수 우세 흐름입니다. 다만 RSI 65로 과매수 영역에 접근 중이므로 단기 조정 가능성에 유의하세요." 규칙 기반 템플릿(LLM 호출 없이)으로 구현하여 안정성 확보. 핵심 함수: generate_commentary(indicators, supply_demand, exchange_rate, composite_signal, support_resistance) → str. 생성된 코멘터리를 리포트 최상단(종합 판정 바로 아래)에 배치하고, main.py 파이프라인에 연결한다. 테스트를 먼저 작성한다.

### Task 2: 시그널 정확도를 일일 리포트에 통합 — 자기 검증의 투명성
Files: src/analysis/report.py, src/main.py, tests/test_report.py
Description: Day 4에서 만든 accuracy.py의 결과를 일일 리포트와 파이프라인에 연결한다. (1) main.py에서 evaluate_signals()를 호출하여 정확도 통계를 구한다. (2) report.py에 _build_accuracy_section(summary) 함수를 추가하여 "📊 시그널 적중률" 섹션을 렌더링한다 — 1일/3일/5일 적중률, 평균 수익률, 평가 시그널 수를 표시. 데이터가 아직 없거나 부족하면(evaluated_signals < 5) "데이터 축적 중" 메시지를 표시한다. (3) generate_daily_report()에 accuracy_summary 파라미터를 추가하고 리포트 하단에 배치. 테스트를 먼저 작성한다.
