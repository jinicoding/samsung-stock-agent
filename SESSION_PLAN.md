## Session Plan

Day 26 (2026-04-16 11:30) — 시장 체제 적응형 시그널 + 축-가격 상관관계 동태 분석

### 자기 평가 요약

971개 테스트 전부 통과, 버그 없음. 커뮤니티 이슈 없음. Day 25에서 시장 체제 인식 모듈을 구축·통합하여 리포트·코멘터리에 체제 정보가 표시되지만, 핵심 Gap이 남아 있다: (1) 시장 체제가 시그널 해석에 실제로 영향을 미치지 않음 — `signal.py`에 market_regime이 연결되지 않아 추세장과 횡보장에서 동일한 RSI 해석이 적용됨. (2) 10축이 독립적으로 점수를 산출하지만, 삼성전자와 각 외부 변수 간 상관관계의 시간적 변화를 추적하지 않아 "지금 어떤 변수에 가장 민감한가"라는 질문에 답할 수 없음.

### Task 1: 시장 체제 적응형 시그널 스코어링 — 체제별 기술적 해석 조정

Files: src/analysis/signal.py, src/main.py, tests/test_signal.py
Description: Day 25에서 구축한 market_regime 모듈의 `interpretation_hints`를 `signal.py`의 `compute_composite_signal()`에 연결하여, 시장 체제에 따라 기술적 지표 해석을 조정한다.

1. `compute_composite_signal()`에 `market_regime: dict | None = None` 파라미터 추가
2. `_score_technical()`에 체제 정보를 전달하여 RSI 임계값을 체제별로 조정:
   - 추세장(trending_up/down): RSI 80/20 (기존 70/30보다 완화 → 추세 추종 유리)
   - 횡보장(range_bound): RSI 70/30 (기존 유지 → 평균 회귀 전략)
   - 돌파장(breakout/breakdown): RSI 80/20 + 볼린저 돌파 가중치 상향
3. 체제 확신도(confidence)가 50 미만이면 조정을 적용하지 않음 (불확실한 체제에서는 기본 해석 유지)
4. `main.py`에서 market_regime 결과를 `compute_composite_signal()`에 전달하도록 배관 연결
5. 테스트: 동일 지표 데이터에 체제만 다를 때 점수가 달라지는 것을 검증, `market_regime=None`일 때 기존 동작 100% 유지

이 변경으로 "같은 RSI 30이지만 추세 하락장에서는 조심, 횡보장에서는 매수 기회"라는 맥락 인식이 시그널에 반영된다.

### Task 2: 축-가격 상관관계 동태 분석 모듈 — 민감도 변화 추적

Files: src/analysis/correlation_dynamics.py (신규), tests/test_correlation_dynamics.py (신규)
Description: 삼성전자 주가 변동과 각 외부 축(환율, SOX, NASDAQ, VIX) 간의 롤링 상관계수를 추적하여, "지금 삼성전자는 어떤 변수에 가장 민감한가"를 정량화하는 모듈을 구축한다.

1. `signal_history` + `daily_prices` 테이블에서 최근 60일 데이터 조회
2. 20일 롤링 상관계수를 축별로 계산 (Pearson correlation: 주가 일일수익률 vs 축별 점수 변화)
3. 상관계수의 최근 변화(강화/약화/전환)를 감지
4. 결과: `{"correlations": {"exchange": {"current": 0.72, "prev": 0.45, "change": "강화"}, ...}, "primary_driver": "exchange", "primary_correlation": 0.72}`
5. "삼성전자는 현재 환율 변동에 가장 민감하게 반응 중 (상관 0.72, 20일 전 0.45에서 급등)" 같은 인사이트의 데이터 기반
6. 테스트: 합성 데이터로 상관계수 계산 정확성, 변화 감지 로직, 엣지 케이스(데이터 부족, 상수 시계열) 검증

리포트·코멘터리·파이프라인 통합은 다음 세션(15:30)에서 2단계 패턴으로 진행. 이 세션은 모듈 구축에 집중.
