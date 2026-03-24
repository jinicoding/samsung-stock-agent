## Session Plan

### Task 1: 종합 투자 시그널 모듈 구축 — 모든 분석을 하나의 판정으로
Files: src/analysis/signal.py (신규), tests/test_signal.py (신규)
Description: 기술적 분석(시장온도), 수급 판정, 환율 추세를 하나로 종합하는 `compute_composite_signal()` 함수를 만든다. 각 축에 가중치를 부여하고(기술적 40%, 수급 40%, 환율 20%), -100~+100 점수와 5단계 판정(강력매수신호/매수우세/중립/매도우세/강력매도신호)을 반환한다. 이것이 리포트 최상단에 "오늘의 핵심 판단"으로 표시될 기반이다. 테스트를 먼저 작성한다.

### Task 2: 일일 리포트에 자연어 인사이트 섹션 추가
Files: src/analysis/insight.py (신규), src/analysis/report.py, tests/test_insight.py (신규), tests/test_report.py
Description: 숫자 나열을 넘어 "왜 이 숫자가 중요한지" 맥락을 설명하는 `generate_insight()` 함수를 만든다. 규칙 기반으로 핵심 변화를 감지하고 자연어 문장을 생성한다: (1) 종합 시그널의 근거 요약 ("외국인 5일 연속 순매수와 정배열이 맞물리며 매수우세 판정"), (2) 주요 변화 감지 ("RSI가 과매도 진입", "MACD 골든크로스 발생", "환율 급등으로 수출주 우호적"), (3) 주의 사항 ("볼린저 밴드 상단 돌파로 과열 주의"). 리포트 상단에 종합 시그널 + 인사이트 문단을 배치하고, main.py 파이프라인에 연결한다. 테스트를 먼저 작성한다.
