## Session Plan

Day 10에서 signal.py에 반도체 업황 축(semiconductor_momentum)을 통합했으나,
리포트·코멘터리·파이프라인에는 아직 연결되지 않았다.
이번 세션에서 반도체 통합을 완성하여 7축 분석 체계를 파이프라인 끝단까지 관통시킨다.

### Task 1: 반도체 업황을 리포트·코멘터리에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, tests/test_report.py, tests/test_commentary.py
Description:
- report.py에 `_build_semiconductor_section()` 함수 추가
  - 삼성전자 vs SK하이닉스 상대성과 (alpha_5d, alpha_20d, relative_trend)
  - SOX 지수 추세 (trend, change_pct, current)
  - 반도체 모멘텀 스코어
  - HTML 포맷으로 렌더링
- generate_daily_report()에 semiconductor 파라미터 추가 (rel_perf, sox_trend, semiconductor_momentum)
- commentary.py에 `_build_semiconductor_sentence()` 함수 추가
  - 반도체 업황에 따른 자연어 코멘트 (예: "반도체 업황이 호조세로, SOX 지수 상승과 SK하이닉스 대비 초과수익이 긍정적이다")
- generate_commentary()에 semiconductor 관련 파라미터 추가
- 테스트: semiconductor 섹션 렌더링 검증, None 처리, 코멘터리 문장 생성 검증

### Task 2: 반도체 업황을 일일 파이프라인에 통합
Files: src/main.py, tests/test_main.py
Description:
- main.py에 반도체 데이터 수집 단계 추가:
  - SK하이닉스 OHLCV 수집 (fetch_skhynix_ohlcv 또는 KIS API 직접 호출)
  - SOX 지수 수집 (fetch_sox_closes)
  - compute_relative_performance() 호출
  - compute_sox_trend() 호출
  - compute_semiconductor_momentum() 호출
- compute_composite_signal() 호출 시 semiconductor_momentum 전달
- generate_daily_report() 호출 시 반도체 데이터 전달
- generate_commentary() 호출 시 반도체 데이터 전달
- try/except로 감싸서 반도체 수집 실패 시 None 폴백
- test_main.py에 반도체 관련 mock/fixture 추가
