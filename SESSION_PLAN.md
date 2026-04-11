## Session Plan

Day 21 (2026-04-11 11:30) — 가격 시나리오 분석: 점수를 행동으로 바꾸기

### 자기 평가 요약

현재 11축 분석 체계(기술·수급·환율·상대강도·펀더멘털·뉴스·컨센서스·반도체·변동성·캔들스틱·글로벌매크로)와 멀티타임프레임 필터, 수렴 분석, 추세 전환 감지, 적응형 가중치까지 갖추고 있다. 843개 테스트 모두 통과.

**핵심 갭**: "매수우세 +35점"이라는 결론은 투자자에게 "그래서 어떻게 하라는 건데?"라는 질문을 남긴다. 지지/저항, ATR, 시그널 방향을 종합하여 구체적인 가격 시나리오(상승/중립/하락)와 핵심 트리거를 제시해야 한다. watchpoints 모듈에 scenario_levels, daily_range, risk_opportunity_factors가 이미 있지만 분리된 팩트 나열 — 이를 통합 시나리오 내러티브로 엮는 것이 목표.

### Task 1: 가격 시나리오 분석 모듈 구축

Files: tests/test_scenario.py (신규), src/analysis/scenario.py (신규)

Description:
지지/저항선, ATR, 종합 시그널 방향, 멀티타임프레임 정합성을 결합하여 3가지 시나리오를 생성하는 모듈.

`build_price_scenarios(current_price, support_resistance, volatility, composite_signal, timeframe_alignment, convergence)` 함수:

- **상승 시나리오**: 시그널 매수우세일 때 — 목표가(nearest_resistance 또는 ATR 기반), 도달 조건(트리거)
- **하락 시나리오**: 시그널 매도우세일 때 — 하한선(nearest_support 또는 ATR 기반), 경계 조건
- **기본 시나리오**: 중립일 때 — 예상 박스권(ATR 기반 일일 변동 범위)
- 각 시나리오에 확신도(conviction) 부여: 시그널 강도 + 타임프레임 정합성 + 수렴 수준으로 산출
- `dominant_scenario` 판정: 종합 시그널 점수 기반
- `risk_reward_comment`: 상승 여력 vs 하방 리스크 비율 문자열

반환 형식:
```python
{
  "scenarios": [
    {"label": "상승", "target": 58000, "trigger": "저항선 56,500 돌파 시",
     "conviction": "높음"},
    {"label": "기본", "range": [55500, 56500], "trigger": "현 수급 흐름 유지",
     "conviction": "보통"},
    {"label": "하락", "target": 54000, "trigger": "지지선 55,000 이탈 시",
     "conviction": "낮음"},
  ],
  "dominant_scenario": "상승",
  "key_level": 56000,
  "risk_reward_comment": "상승 여력 +3.6% vs 하방 리스크 -1.8%"
}
```

테스트 우선: 시그널 강도별(강매수/매수/중립/매도/강매도), 데이터 부족 시, ATR 없을 때, 지지/저항 없을 때 등 엣지 케이스 포함. 최소 10개 테스트.

### Task 2: 시나리오 분석을 리포트·코멘터리·파이프라인에 통합

Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py

Description:
Task 1에서 구축한 시나리오 모듈을 일일 파이프라인에 연결한다. 확립된 2단계 패턴(모듈 구축 → 파이프라인 통합)을 따른다.

1. **main.py**: watchpoints 계산 직후에 build_price_scenarios() 호출 추가. composite_signal, support_resistance, volatility, timeframe_alignment, convergence를 전달. 결과를 generate_daily_report()와 generate_commentary()에 scenario 파라미터로 전달.
2. **report.py**: `_build_scenario_section(scenario)` 함수 추가. 종합 판정 바로 아래에 배치. 시나리오 3개를 HTML로 렌더링(상승=🟢, 기본=🟡, 하락=🔴). 핵심 가격대·확신도·리스크/리워드 비율 표시.
3. **commentary.py**: `_build_scenario_sentence(scenario)` 함수 추가. "단기 상승 시나리오 우세 — 56,500원 돌파 시 58,000원대 진입 가능" 같은 1문장 생성.
4. **테스트**: 기존 report/commentary/main 테스트에 시나리오 관련 케이스 추가.
5. **배관 검증(Day 18 교훈)**: main.py에서 build_price_scenarios → generate_daily_report/generate_commentary까지 데이터 흐름 end-to-end 확인.
