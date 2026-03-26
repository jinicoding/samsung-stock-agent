## Session Plan

### Task 1: 시그널 정확도 추적을 일일 파이프라인·리포트에 통합 — "내 시그널을 얼마나 믿어야 하는가"
Files: src/main.py, src/analysis/report.py, tests/test_main.py, tests/test_report.py
Description: accuracy.py 모듈은 이미 있지만 main.py에서 호출하지 않고, 리포트에도 표시되지 않는다. 투자자가 시그널의 신뢰도를 판단하려면 "최근 N일 적중률"과 "평균 수익률"이 리포트에 보여야 한다. (1) main.py에서 evaluate_signals()를 호출하여 정확도 통계를 산출하고, (2) report.py에 정확도 섹션(_build_accuracy_section)을 추가하여 1/3/5일 적중률, 평균 수익률, 총 평가 시그널 수를 표시한다. 데이터가 아직 부족하면(evaluated_signals < 5) "데이터 축적 중" 메시지를 표시. (3) generate_daily_report()의 시그니처에 accuracy_summary dict를 추가하고, 리포트 하단 지지/저항선 아래에 정확도 섹션을 배치한다. 테스트를 먼저 작성하고 구현한다.

### Task 2: VWAP(거래량 가중 평균 가격) 지표 구축 — 기관 벤치마크 도입
Files: src/analysis/technical.py, src/analysis/report.py, src/analysis/signal.py, tests/test_technical.py, tests/test_report.py
Description: VWAP는 기관 투자자들이 매매 실행 품질을 평가하는 핵심 벤치마크다. 현재가가 VWAP 위면 매수세 우위, 아래면 매도세 우위로 해석한다. (1) technical.py의 compute_technical_indicators()에 N일 VWAP 계산을 추가한다. typical_price = (H+L+C)/3, VWAP = Σ(typical_price × volume) / Σ(volume)으로 20일 누적 계산. price_vs_vwap_pct(현재가 대비 VWAP 괴리율)도 함께 반환한다. (2) report.py에 VWAP 정보를 거래량 섹션에 통합하여 VWAP 값, 현재가와의 괴리율, 매수/매도 우위 판정을 표시한다. (3) signal.py의 _score_technical()에 VWAP 괴리율을 추가 스코어링 요소로 반영한다. 테스트 먼저 작성 후 구현.
