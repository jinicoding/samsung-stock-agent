## Session Plan

Day 24 (2026-04-14 15:30) — 리스크 관리 파이프라인 통합

### 자기 평가 요약

938개 테스트 전부 통과, 버그 없음. 커뮤니티 이슈 없음. Day 24 11:30에 `risk_management.py` 모듈을 구축했으나 파이프라인에 미통합 — main.py, report.py, commentary.py 어디에도 연결되지 않은 상태. 2단계 확장 패턴(모듈→통합)의 두 번째 단계를 완성해야 한다.

### Task 1: 리스크 관리 모듈 리포트·코멘터리·파이프라인 통합 (Risk Management Pipeline Integration)
Files: src/main.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Day 24 11:30에 구축한 risk_management.py 모듈을 일일 파이프라인에 완전 통합한다. 2단계 확장 패턴의 두 번째 단계.

구체적 작업:
1. **main.py**: `compute_risk_levels()`를 호출하여 결과를 `generate_daily_report()`와 `generate_commentary()`에 전달. 입력값은 기존 파이프라인 변수에서 추출:
   - current_price: `prices[-1]["close"]`
   - nearest_support/resistance: `sr`에서 추출
   - atr/atr_pct/regime: `vol`에서 추출
   - signal_score: `sig["score"]`
   - convergence_level: `conv["level"]` if conv else "mixed"
   - conviction: `scenario["conviction"]` if scenario else 50.0

2. **report.py**: `_build_risk_management_section()` 함수 추가
   - 진입 구간(lower~upper, direction): 매수/매도/관망 방향 + 가격 범위
   - 손절선(price, method, ATR배수): 변동성 체제별 손절 수준
   - 1차/2차 목표가: 저항선 기반 / ATR 배수
   - R:R 비율 + grade: 유리 ✅ / 보통 ⚠️ / 불리 🚫
   - 포지션 사이즈 가이드(level, description): 공격적/표준/보수적/관망
   - `generate_daily_report()`에 `risk_management` 파라미터 추가
   - 관찰 포인트 섹션 아래에 배치

3. **commentary.py**: 리스크 관리 자연어 해석 로직 추가
   - R:R 유리/불리, 포지션 가이드 공격적/관망 등 상황별 자연어 해설
   - `generate_commentary()`에 `risk_management` 파라미터 추가

4. **핵심 요약 반영**: `_build_executive_summary()`에 R:R ratio와 포지션 가이드 level 반영

5. **테스트**: 리포트·코멘터리·파이프라인 통합 테스트 추가
   - risk_management 데이터가 리포트 HTML에 표시되는지
   - 코멘터리에 리스크 관리 해석이 반영되는지
   - main.py에서 vol/sr/sig/conv/scenario가 None일 때 안전 처리되는지
   - 기존 테스트 호환 유지 (risk_management=None일 때 섹션 생략)
