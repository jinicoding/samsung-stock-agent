# 싸나이 SSANAI

**S**amsung **S**tock **A**nalyst **AI** — 스스로 진화하며 최고의 애널리스트를 목표로 성장하는 AI

> 기능 목록을 미리 정하지 않는다. 에이전트가 목표를 향해 스스로 판단하고 하나씩 구축한다.

## What This Is

삼성전자(005930.KS) 주식을 분석하는 자기진화형 AI 에이전트입니다.

- **목표**: 최고 수준의 AI 애널리스트가 되는 것
- **방법**: 주기적으로 자신의 코드를 읽고, 부족한 점을 찾고, 개선하고, 테스트하고, 커밋합니다
- **핵심**: 단순 숫자 나열이 아닌, LLM이 데이터를 해석하여 "왜 이 숫자가 중요한지" 맥락을 설명

[yoyo-evolve](https://github.com/yologdev/yoyo-evolve)의 자기진화 파이프라인을 기반으로 구축되었습니다.

## How It Works

```
┌──────────────────────────────────────────────────┐
│              Evolution Pipeline                   │
│                                                  │
│  pytest 검증 → Phase A: 계획 → Phase B: 구현     │
│                  (Claude)       (Claude)          │
│                                                  │
│  → 보호파일 체크 → pytest 검증 → 저널 작성 → push │
└──────────────────────────────────────────────────┘
```

1. **자기평가** — 자신의 소스코드를 읽고 부족한 분석 능력을 파악
2. **계획** — 가장 중요한 개선 사항을 SESSION_PLAN.md에 작성
3. **구현** — 테스트를 먼저 작성하고, 코드를 수정하고, pytest 통과 확인
4. **검증** — 보호 파일 수정 여부 체크, 테스트 실패 시 자동 롤백
5. **기록** — JOURNAL.md에 세션 기록, memory/learnings.jsonl에 교훈 저장

## Current State

| 항목 | 상태 |
|------|------|
| 데이터 수집 | ✅ KIS API (주가, 수급, 환율), Naver Finance (외인 지분) |
| 데이터 저장 | ✅ SQLite (4 테이블) |
| 리포트 발송 | ✅ Telegram 다중 구독자 |
| 기술적 분석 | 🔄 에이전트가 진화하며 구축 중 |
| LLM 인사이트 | 🔄 에이전트가 진화하며 구축 중 |
| 뉴스 감정 분석 | 🔄 에이전트가 진화하며 구축 중 |

## Project Structure

```
samsung-stock-agent/
├── src/
│   ├── data/               # 데이터 수집 (KIS API, SQLite)
│   ├── analysis/           # 분석 엔진 (에이전트가 진화하며 구축)
│   └── delivery/           # Telegram 리포트 발송
├── scripts/
│   ├── evolve.sh           # 진화 파이프라인 (보호 파일)
│   └── context.sh          # 아이덴티티 컨텍스트 빌더
├── skills/                 # 진화 스킬 (evolve, self-assess, communicate)
├── memory/                 # 학습 기록 (JSONL 아카이브 + 활성 컨텍스트)
├── tests/                  # pytest 테스트
├── IDENTITY.md             # 에이전트 헌법 (불변)
├── PERSONALITY.md           # 에이전트 보이스 (불변)
└── JOURNAL.md              # 진화 일지
```

## Setup

```bash
# 의존성 설치
pip install -r requirements.txt

# Claude CLI 로그인 (Claude Max 구독 필요)
claude login

# 환경변수 설정
export KIS_APP_KEY="..."         # 한국투자증권 API
export KIS_APP_SECRET="..."
export TELEGRAM_BOT_TOKEN="..."  # Telegram 봇 토큰
```

## Run Evolution

```bash
# 수동 실행 (1회 진화 세션)
./scripts/evolve.sh

# 자동 실행 (cron — 8시간마다)
crontab -e
# 0 */8 * * * cd /path/to/samsung-stock-agent && ./scripts/evolve.sh >> /tmp/evolve.log 2>&1
```

## Journal

에이전트의 진화 과정은 [JOURNAL.md](JOURNAL.md)에서 확인할 수 있습니다.

## Safety

- `IDENTITY.md`, `PERSONALITY.md`, `scripts/`, `.github/workflows/`는 에이전트가 수정할 수 없음
- 모든 코드 변경은 `pytest tests/` 통과 필수
- 테스트 실패 시 자동 롤백
- 투자 자문/추천 금지 — 분석 도구일 뿐, 금융 자문이 아님

## License

MIT
