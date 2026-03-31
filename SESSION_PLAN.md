## Session Plan

### Task 1: 반도체 업황 지표를 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Day 10 10:15 세션에서 구축한 반도체 업황 모듈(src/data/semiconductor.py, src/analysis/semiconductor.py)을 전체 파이프라인에 통합한다. 구체적으로:

1. **signal.py**: `_score_semiconductor()` 함수 추가. `compute_semiconductor_momentum()`의 반환값(모멘텀 스코어 -100~+100)을 그대로 활용. `compute_composite_signal()`에 `semiconductor` 선택 인자 추가하고, 기존 가중치에 반도체 축 10%를 기존 축 비례 축소로 확보 (컨센서스 통합 시와 동일한 패턴).

2. **report.py**: 반도체 업황 HTML 섹션 추가. 삼성전자 vs SK하이닉스 상대성과(5일/20일 alpha), SOX 지수 추세(추세·변동률·MA20), 종합 모멘텀 스코어를 표시. 기존 섹션 순서에서 펀더멘털과 뉴스 사이에 배치.

3. **commentary.py**: `_build_semiconductor_sentence()` 함수 추가. 반도체 섹터 모멘텀이 강세(+30 이상)/약세(-30 이하)일 때 자연어 코멘터리 생성. `generate_commentary()`에 `semiconductor` 인자 추가.

4. **main.py**: SK하이닉스 OHLCV + SOX 지수 데이터 수집 단계 추가. `compute_relative_performance()`, `compute_sox_trend()`, `compute_semiconductor_momentum()` 호출. 결과를 `compute_composite_signal()`, `generate_daily_report()`, 코멘터리에 전달.

5. **테스트**: 각 모듈의 통합 테스트 추가. signal.py의 반도체 가중치 반영, report.py의 반도체 섹션 렌더링, commentary.py의 반도체 문장 생성을 검증.

이전 세션들의 패턴(모듈 구축 → 파이프라인 통합)을 따르며, 기존 컨센서스 통합(Day 8 15:30)과 동일한 방식으로 진행한다.
