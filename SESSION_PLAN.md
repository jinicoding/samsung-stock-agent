## Session Plan

Day 26 (2026-04-16 15:30) — 배관 버그 수정 + 체제 적응 투명화

### 자기 평가 요약

980개 테스트 전부 통과, 커뮤니티 이슈 없음. Day 26 11:30에서 시장 체제가 기술적 점수의 RSI 임계값을 조정하는 적응형 스코어링을 구현했으나, 두 가지 핵심 Gap이 남아 있다: (1) 상대강도(rs_score)가 수렴 분석에서 누락된 배관 버그 — 11축 중 유일하게 빠져 있어 수렴도 산출이 부정확. (2) 체제 적응형 조정이 투자자에게 불투명 — 점수가 왜 달라졌는지 리포트·코멘터리에 표시되지 않아, Day 26 저널에서 명시한 "체제별 조정의 리포트 통합" 과제가 미완.

### Task 1: 상대강도(rs_score) 수렴 분석 누락 버그 수정

Files: src/main.py, tests/test_convergence_pipeline.py (신규 또는 기존 테스트에 추가)
Description: `main.py:256-261`에서 수렴 분석용 `conv_scores`를 구성할 때 for 루프에 `"rs_score"`가 빠져 있어, 상대강도 축이 수렴 분석에서 제외되는 배관 버그다. `rs_score`를 포함하도록 수정하고, RS 데이터가 있을 때 수렴 분석에 포함되는지 검증하는 테스트를 작성한다.

### Task 2: 체제별 시그널 조정의 리포트·코멘터리 투명화 — 투자자에게 "왜 점수가 조정되었는가" 설명

Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py
Description: Day 26 11:30에서 시장 체제가 기술적 점수를 조정하지만, 투자자는 이를 알 수 없다.

1. `signal.py`의 `_score_technical()`이 체제 조정 전/후 점수를 추적하여, `compute_composite_signal()`이 `regime_adjustment` 필드를 반환하도록 수정. 이 필드에 조정 전 기술적 점수, 적용된 체제, 조정된 RSI 임계값을 포함.
2. `report.py`의 시장 체제 섹션(`_build_market_regime_section`)에 "📊 체제 적응 조정" 서브섹션 추가 — 기술적 점수가 체제에 의해 어떻게 조정되었는지 (예: "RSI 기준 70/30 → 80/20 적용, 기술적 점수 +12.3 → +18.7") HTML 표시.
3. `commentary.py`에 체제 조정 관련 자연어 해설 추가 (예: "현재 추세장에서 RSI 과매수/과매도 기준이 완화되어 기술적 판정이 조정되었습니다").
4. 테스트: 체제 조정 정보가 시그널·리포트·코멘터리에 정확히 반영되는지 검증. 체제 미제공 시 `regime_adjustment`가 없는 것도 검증.
