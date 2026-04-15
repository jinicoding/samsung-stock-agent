## Session Plan

Day 25 (2026-04-15 15:30) — 시장 체제(Market Regime) 파이프라인 통합 + 체제 기반 시그널 조정

### 자기 평가 요약

958개 테스트 전부 통과, 버그 없음. 커뮤니티 이슈 없음. Day 25 11:30에 시장 체제 인식 모듈(`market_regime.py`)을 구축했으나 파이프라인에 미통합 상태. `main.py`에서 호출하지 않고, `report.py`에 표시되지 않으며, `commentary.py`에 반영되지 않는다. 2단계 확장 패턴의 2단계(파이프라인 통합)가 필요한 상태. 체제 인식이 단순 표시를 넘어 실제 시그널 해석에 영향을 미치도록 확장하면, "지금 어떤 장인가"에 따라 같은 RSI 70이라도 추세장에서는 정상, 횡보장에서는 과매수로 달리 해석할 수 있어 분석 품질이 한 단계 올라간다.

### Task 1: 시장 체제(Market Regime) 리포트·코멘터리·파이프라인 통합
Files: src/main.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description: Day 25 11:30에 구축한 `market_regime.py` 모듈을 일일 파이프라인에 완전 통합한다.

1. **main.py**: 기술적 지표 계산(3단계) 직후에 `compute_market_regime()` 호출
   - `from src.analysis.market_regime import compute_market_regime`
   - try/except로 감싸고 실패 시 None 처리 (기존 패턴과 동일)
   - 결과를 `generate_daily_report()`와 `generate_commentary()`에 `market_regime=` 파라미터로 전달

2. **report.py**: 시장 체제 섹션 HTML 렌더링 추가
   - `generate_daily_report()`에 `market_regime: dict | None = None` 파라미터 추가
   - 종합 판정 섹션 뒤에 시장 체제 섹션 배치
   - 체제 한글명(추세상승/추세하락/횡보/돌파/붕괴), 국면(매집/마크업/분배/마크다운), 확신도, 지속 일수를 표시
   - `interpretation_hints`의 핵심 내용(RSI 기준, 지지/저항 신뢰도)을 해석 가이드로 표시

3. **commentary.py**: 체제 맥락을 코멘터리에 프레이밍으로 반영
   - `generate_commentary()`에 `market_regime: dict | None = None` 파라미터 추가
   - 체제별 맥락 문장: "상승 추세장(확신도 N%)에서", "횡보 국면이 N일째 지속되는 가운데" 등
   - 기존 코멘터리의 해석을 보강하는 프레이밍 역할

4. **테스트**: 리포트·코멘터리·파이프라인 통합 테스트 추가
   - 체제 정보가 리포트 HTML에 표시되는지
   - 코멘터리에 체제 맥락이 반영되는지
   - `market_regime=None`일 때 안전 처리되는지

### Task 2: 시장 체제 기반 시그널 해석 조정 (Regime-Aware Signal Contextualization)
Files: src/analysis/signal.py, tests/test_signal.py
Description: `market_regime.py`의 `interpretation_hints`를 활용하여 종합 시그널의 기술적 분석 점수를 체제에 맞게 조정한다.

1. **signal.py**: `compute_composite_signal()`에 `market_regime: dict | None = None` 파라미터 추가
   - `market_regime`이 제공되면 `interpretation_hints`를 읽어 기술적 점수를 조정:
     - 추세장: RSI 과매수/과매도 임계값 80/20 적용 → RSI 기반 감점/가점 완화 (기존 70/30보다 ±15% 범위 축소)
     - 횡보장: RSI 기준 유지(70/30), 지지/저항 기반 점수의 가중치 +10%
     - 돌파장: 거래량 확인 없는 돌파 시그널의 점수를 -20% 감쇄
   - `market_regime=None`일 때 기존 동작 100% 유지 (기본값으로 조정 없음)
   - 조정 결과를 시그널 dict에 `regime_adjustment` 키로 추가하여 투명성 확보

2. **main.py**: `compute_composite_signal()` 호출 시 `market_regime` 전달
   - Task 1에서 이미 변수를 확보하므로 배관만 연결

3. **테스트**: 체제별 시그널 조정 테스트
   - trending_up 체제에서 RSI 75일 때 과매수 감점이 적용되지 않는지
   - range_bound 체제에서 RSI 75일 때 과매수 감점이 정상 적용되는지
   - breakout 체제에서 거래량 미확인 시 감쇄가 작동하는지
   - `market_regime=None`일 때 기존 테스트 전부 통과하는지
