## Session Plan

Day 11 이전 세션에서 반도체 업황 모듈(data/semiconductor.py, analysis/semiconductor.py)을 구축하고
signal.py·report.py·commentary.py에 통합했으나, main.py 파이프라인에 데이터 수집·분석 호출이 누락되어
반도체 축이 실질적으로 동작하지 않는 상태다. 이번 세션에서 파이프라인 연결을 완성하고
실제 시장 데이터로 7축 전체 파이프라인을 검증한다.

### Task 1: 반도체 업황을 일일 파이프라인(main.py)에 연결
Files: src/main.py, tests/test_main.py
Description:
- main.py에 반도체 데이터 수집·분석 단계를 추가한다:
  1. from src.data.semiconductor import fetch_skhynix_ohlcv, fetch_sox_index
  2. from src.analysis.semiconductor import compute_relative_performance, compute_sox_trend, compute_semiconductor_momentum
  3. 기존 KOSPI/RS 분석 블록(3.6) 뒤에 반도체 수집 블록 추가:
     - fetch_skhynix_ohlcv()로 SK하이닉스 OHLCV 수집
     - fetch_sox_index()로 SOX 일별 종가 수집
     - samsung_closes와 hynix_closes 길이를 맞춰 compute_relative_performance() 호출
     - SOX 종가로 compute_sox_trend() 호출
     - compute_semiconductor_momentum(rel_perf, sox_trend) 호출
  4. compute_composite_signal() 호출 시 semiconductor_momentum=semi_momentum 전달
  5. generate_daily_report() 호출 시 rel_perf=rel_perf, sox_trend=sox_trend, semiconductor_momentum=semi_momentum 전달
  6. try/except로 감싸서 실패 시 rel_perf=None, sox_trend=None, semi_momentum=None으로 폴백
- test_main.py에 semiconductor 모듈 호출 검증 테스트를 추가한다

### Task 2: 전체 7축 파이프라인 dry-run 검증
Files: (실행 검증 위주, 필요시 src/data/*.py 또는 src/analysis/*.py 수정)
Description:
- Task 1 완료 후 python3 -m src.main --dry-run 으로 실제 시장 데이터 기반 파이프라인을 실행한다
- 7축(기술·수급·환율·상대강도·펀더멘털·뉴스·컨센서스+반도체) 데이터 수집·분석·리포트 생성이
  모두 정상 동작하는지 확인한다
- 데이터 수집 실패, 파싱 에러, HTML 렌더링 깨짐 등 문제가 발견되면 즉시 수정한다
- Day 6 저널 이후 반복 언급된 "실제 시장 데이터 dry-run 검증"을 완료한다
