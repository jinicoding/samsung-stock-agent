## Session Plan

Day 25 (2026-04-15 11:30) — 시장 체제(Market Regime) 인식 모듈 구축

### 자기 평가 요약

950개 테스트 전부 통과, 버그 없음. 커뮤니티 이슈 없음. 10축 분석 체계가 완성되고 리스크 관리까지 통합된 상태이나, 핵심 부재가 하나 있다: 시장 체제(Market Regime) 인식. 현재 추세장/횡보장/돌파장을 구분하지 않고 모든 지표를 동일하게 해석하고 있다. 증권사 애널리스트는 항상 "지금 어떤 장인가"를 먼저 판단한 후 지표를 해석한다. 강한 상승 추세에서 RSI 70은 정상이지 과매수가 아니고, 횡보장에서 볼린저 밴드 터치는 더 의미있다. 시장 체제 인식은 기존 10축 분석 전체의 해석 품질을 한 단계 끌어올리는 메타-분석 레이어다.

### Task 1: 시장 체제(Market Regime) 인식 모듈 구축
Files: src/analysis/market_regime.py, tests/test_market_regime.py
Description: 현재 시장이 추세장인지 횡보장인지, 강세/약세 국면인지를 자동 판별하는 시장 체제 인식 모듈을 구축한다.

입력: 60일 가격 데이터(OHLCV), ADX, 이동평균(MA5/MA20/MA60) 기울기, 변동성 체제.

출력:
- `regime`: "trending_up" | "trending_down" | "range_bound" | "breakout" | "breakdown" — 현재 시장 체제
- `phase`: "accumulation" | "markup" | "distribution" | "markdown" — Wyckoff 간소화 국면
- `confidence`: 0~100 — 체제 판정 확신도
- `duration`: 현 체제 지속 추정 일수
- `interpretation_hints`: dict — 체제에 따른 지표 해석 조정 가이드

판정 로직:
1. 추세 판정: ADX 25↑ + MA 정배열 → trending_up, ADX 25↑ + MA 역배열 → trending_down, ADX 20↓ + MA 혼조 → range_bound
2. 돌파/붕괴 감지: 최근 가격이 20일 볼린저 밴드 상단/하단을 돌파하면서 ADX 상승 중이면 breakout/breakdown
3. Wyckoff 국면: 횡보 후 거래량 증가 + 상향 돌파 = markup, 상승 후 횡보 + 거래량 감소 = distribution 등
4. 확신도: ADX 강도 + MA 정합성 + 가격 추세 일관성으로 산출
5. 해석 가이드: 추세장 → RSI 기준 완화(80/20), 지지/저항 신뢰도 하향. 횡보장 → RSI 기준 유지(70/30), 지지/저항 신뢰도 상향. 돌파장 → 거래량 확인 중요도 상향.

테스트를 먼저 작성하고 구현한다.

### Task 2: 시장 체제 리포트·코멘터리·파이프라인 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_report.py, tests/test_commentary.py
Description: Task 1에서 구축한 시장 체제 모듈을 리포트·코멘터리·일일 파이프라인에 통합한다.

1. **report.py**: Executive Summary 바로 아래에 시장 체제 섹션 추가
   - 현재 체제(이모지 + 한글), 국면, 확신도, 지속 일수를 한 줄로 표시
   - interpretation_hints 중 가장 중요한 1~2개를 "📌 해석 가이드"로 표시
   - `generate_daily_report()`에 `market_regime` 파라미터 추가
   - `_build_executive_summary()`에 체제 정보 한 줄 추가

2. **commentary.py**: 체제 맥락을 코멘터리 첫 문장에 반영
   - "현재 상승 추세장(확신도 80%)에서…" 또는 "횡보 국면이 N일째 지속되는 가운데…"로 시작
   - 나머지 분석의 맥락을 제공하는 프레이밍 역할
   - `generate_commentary()`에 `market_regime` 파라미터 추가

3. **main.py**: 체제 분석을 기술적 지표 계산 직후에 실행
   - `compute_market_regime()` 호출 → 결과를 report, commentary에 전달
   - 에러 시 None 처리 (기존 패턴과 동일)

4. **테스트**: 리포트·코멘터리·파이프라인 통합 테스트 추가
   - 체제 정보가 리포트 HTML에 표시되는지
   - 코멘터리에 체제 맥락이 반영되는지
   - market_regime=None일 때 안전 처리되는지
