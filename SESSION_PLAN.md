## Session Plan

### Task 1: 펀더멘털 분석을 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Day 7에서 구축한 기본적 분석 모듈(src/data/fundamentals.py, src/analysis/fundamentals.py)이 아직 파이프라인에 연결되지 않았다. 다음을 수행한다:
1) main.py에서 fetch_fundamentals() → analyze_fundamentals() 호출 추가, 결과를 시그널·리포트에 전달
2) signal.py의 compute_composite_signal()에 fundamentals 파라미터 추가, 5축 가중치 재배분 (기술 30%, 수급 30%, 환율 15%, 상대강도 10%, 펀더멘털 15%)
3) report.py에 펀더멘털 섹션 추가 (PER/PBR 밸류에이션, 배당수익률, 실적 전망)
4) commentary.py에 펀더멘털 기반 자연어 문장 추가 (저평가/고평가 언급)
5) 각 모듈의 기존 테스트 업데이트 + 새 테스트 추가

### Task 2: 전체 파이프라인 dry-run 검증 스크립트 구축
Files: scripts/dry_run_test.sh, tests/test_pipeline_integration.py
Description: 저널에서 매 세션 "실제 시장 데이터로 전체 파이프라인 dry-run 검증이 필요"라고 반복 언급했으나 한 번도 수행되지 않았다. mock 없이 실제 API를 호출하여 전체 파이프라인이 end-to-end로 동작하는지 검증하는 통합 테스트를 만든다:
1) scripts/dry_run_test.sh — `python3 -m src.main --dry-run`을 실행하고 출력에 핵심 섹션(종합 판정, 기술적, 수급, 환율, 펀더멘털)이 모두 포함되는지 grep으로 확인
2) tests/test_pipeline_integration.py — 실제 DB 데이터(또는 fixture)로 main() 흐름을 end-to-end 테스트하되, 텔레그램 발송만 mock하는 통합 테스트
