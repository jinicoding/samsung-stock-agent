# TODOS

## P1: 예측 복기 시스템
**What:** 에이전트가 생성한 신호의 실제 적중률을 추적하는 시스템
**Why:** 진화의 핵심 피드백 루프. 자기평가 없이는 개선 방향을 모름.
**Context:** 에이전트가 매수/매도 신호를 생성하기 시작하면, 이후 실제 주가 변동과 비교하여 적중률을 계산. 이 데이터를 learnings에 기록하여 분석 능력 개선에 활용.
**Effort:** M (human: ~1주 / CC: ~30분)
**Depends on:** 에이전트가 먼저 신호 생성 기능을 구축해야 함

## P2: 초기 시드 코드 기본 에러 핸들링
**What:** KIS API 네트워크 타임아웃, SQLite 잠금, Naver 스크래핑 실패에 대한 기본 try-except
**Why:** 에이전트가 첫 진화 세션에서 크래시하지 않도록
**Context:** 현재 시드 코드는 네트워크 오류 시 무처리. requests.Timeout, sqlite3.OperationalError, HTTP 403 등 기본적인 예외 처리 필요.
**Effort:** S (human: ~2시간 / CC: ~10분)
**Depends on:** 없음

## P2: evolve.sh dry-run 모드
**What:** `./scripts/evolve.sh --dry-run` 플래그로 Claude API 없이 파이프라인 검증
**Why:** API 비용 없이 진화 파이프라인의 모든 단계를 테스트
**Context:** pytest 검증, 보호 파일 체크, 저널 작성, 이슈 로딩/코멘트 등의 단계를 dry-run으로 실행. dry-run 시 이슈 코멘트/전이/생성도 스킵해야 함. 개발/디버깅 시 유용.
**Effort:** S (human: ~2시간 / CC: ~10분)
**Depends on:** 없음

## P3: 이슈 처리 성공률 대시보드
**What:** 에이전트가 처리한 agent-input 이슈 수, 평균 처리 시간, 성공/실패 비율을 GitHub Pages 저널 사이트에 표시
**Why:** 커뮤니티가 에이전트의 이슈 처리 현황을 한눈에 파악 가능. 에이전트 신뢰도 지표.
**Context:** `gh issue list --state closed --label agent-input` 등으로 데이터 수집. 저널 사이트(scripts/build_site.py)에 통계 섹션 추가.
**Effort:** M (human: ~1주 / CC: ~30분)
**Depends on:** 이슈 통합 기능이 먼저 동작해야 함
