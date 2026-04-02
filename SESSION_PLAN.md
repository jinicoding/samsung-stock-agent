## Session Plan

Day 11에서 변동성 분석 모듈(volatility.py)을 구축했지만 파이프라인에 통합하지 않았다.
8번째 분석축이 허공에 떠 있는 상태다. 이번 세션의 최우선은 이 연결을 완성하는 것이다.

그 다음, IDENTITY.md의 핵심 차별화인 "LLM으로 데이터를 해석하여 자연어 인사이트를 생성"을
실현한다. 현재 commentary.py는 규칙 기반 템플릿이라 숫자 나열의 한계가 있다.
Claude CLI를 활용하여 "왜 이 숫자가 중요한지" 맥락을 설명하는 AI 인사이트를 생성한다.

### Task 1: 변동성 분석을 종합 시그널·리포트·코멘터리·파이프라인에 통합
Files: src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description:
- Day 11에서 구축한 변동성 분석 모듈(src/analysis/volatility.py)을 파이프라인 전체에 통합한다. 테스트를 먼저 작성한다.
  1. main.py — compute_volatility(prices) 호출 추가, 결과를 리포트/코멘터리에 전달
  2. signal.py — _score_volatility() 함수 추가. 변동성 체제(고변동성=-30, 저변동성=+20, 보통=0)와 밴드폭 수축(+15) 반영. 8번째 축으로 가중치 5% 부여, 기존 축 비례 축소
  3. report.py — "변동성 분석" HTML 섹션 추가: ATR, ATR%, HV20(연율화), 변동성 체제, 밴드폭 수축 여부
  4. commentary.py — 변동성 기반 자연어 문장 추가:
     - 고변동성: 리스크 경고
     - 저변동성+수축: 돌파 대비 언급
     - 보통: 별도 언급 없음
  5. 각 모듈에 대한 테스트 추가 (테스트 먼저 작성)

### Task 2: LLM 기반 종합 인사이트 생성기 구축
Files: src/analysis/llm_insight.py (신규), tests/test_llm_insight.py (신규), src/main.py, src/analysis/report.py
Description:
- 규칙 기반 commentary.py의 한계를 넘어, Claude CLI를 활용한 LLM 기반 인사이트 생성기를 구축한다.
  1. src/analysis/llm_insight.py 생성 — 모든 분석 결과(8축 + 변동성)를 구조화된 프롬프트로 조합하여 `claude` CLI에 전달, 2-3문장의 투자 인사이트를 생성
  2. 프롬프트 설계: 분석 데이터를 JSON 직렬화 → 시스템 프롬프트에 "삼성전자 애널리스트, 매수/매도 추천 금지, 분석 근거 설명" 지침
  3. CLI 실패 시 기존 commentary.py 결과로 폴백 — 안정성 확보
  4. 리포트에 "AI 인사이트" 섹션으로 기존 코멘터리 아래에 추가
  5. 테스트: CLI 호출을 모킹하여 정상/실패/타임아웃 시나리오 검증
