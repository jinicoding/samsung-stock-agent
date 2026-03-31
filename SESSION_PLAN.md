## Session Plan

### Task 1: 반도체 업황 지표를 종합 시그널(signal.py)에 통합
Files: src/analysis/signal.py, tests/test_signal.py
Description: Day 10 오전에 구축한 `src/analysis/semiconductor.py`의 `compute_semiconductor_momentum()` 결과를 종합 시그널 모듈에 반영한다. `compute_composite_signal()`에 `semiconductor_momentum` 파라미터(int | None)를 추가하고, 가중치 체계에 반도체 업황 축(10%)을 신설한다. 컨센서스 통합 때와 동일한 패턴(기존 축 비례 축소)으로 100%를 유지한다. `_score_semiconductor()` 함수를 추가하여 모멘텀 스코어(-100~+100)를 그대로 시그널 점수로 변환한다. 테스트: semiconductor가 None일 때 기존 동작 유지, 양수/음수 모멘텀 반영 검증, result dict에 semiconductor_score 키 포함 확인.

### Task 2: 반도체 업황 지표를 리포트(report.py) 및 코멘터리(commentary.py)에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, tests/test_report.py, tests/test_commentary.py
Description: report.py에 `_build_semiconductor_section(rel_perf, sox_trend, momentum)` 함수를 추가하여 삼성전자 vs SK하이닉스 alpha(5d/20d), 상대추세, SOX 추세·변동률, 종합 모멘텀 스코어를 HTML로 렌더링한다. `generate_daily_report()`에 `semiconductor_rel_perf`, `semiconductor_sox`, `semiconductor_momentum` 파라미터를 추가하고, 펀더멘털과 뉴스 사이에 배치한다. commentary.py에 `_build_semiconductor_sentence(momentum, rel_perf, sox_trend)` 함수를 추가하여 모멘텀 +30 이상이면 업황 긍정 문장, -30 이하이면 부정 문장을 생성한다. `generate_commentary()`에도 동일 파라미터를 추가한다. 테스트로 섹션 렌더링과 문장 생성을 검증한다.

### Task 3: 반도체 업황 지표를 일일 파이프라인(main.py)에 통합
Files: src/main.py, tests/test_main.py
Description: main.py에 반도체 데이터 수집 단계를 추가한다. (1) `fetch_skhynix_ohlcv()`로 SK하이닉스 OHLCV 수집, (2) `fetch_sox_index()`로 SOX 지수 수집, (3) 삼성전자·SK하이닉스 종가로 `compute_relative_performance()` 호출, (4) SOX 종가로 `compute_sox_trend()` 호출, (5) `compute_semiconductor_momentum()`으로 모멘텀 산출. 결과를 `compute_composite_signal()`의 `semiconductor_momentum`과 `generate_daily_report()`의 반도체 관련 파라미터에 전달한다. try-except로 감싸서 실패 시 None으로 폴백, 기존 파이프라인은 영향받지 않도록 한다.
