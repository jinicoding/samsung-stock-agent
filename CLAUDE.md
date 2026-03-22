# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A self-evolving AI stock analysis agent for Samsung Electronics (삼성전자). The agent evolves its own Python source code to become a better stock analyst. A cron job (`scripts/evolve.sh`) runs the agent periodically using a 3-phase pipeline (plan → implement → verify), which reads its own source, picks improvements, implements them, and commits — if tests pass.

Adapted from [yoyo-evolve](https://github.com/yologdev/yoyo-evolve), with the domain shifted from coding agent to stock analysis.

## Build & Test Commands

```bash
pytest tests/                    # Run all tests
pytest tests/ -v                 # Verbose output
pytest tests/test_database.py    # Run specific test file
pytest -k test_name              # Run matching tests
```

To trigger a full evolution cycle (uses Claude Max subscription):
```bash
./scripts/evolve.sh
```

## Environment Variables

```bash
# Evolution uses Claude Max subscription — no API key needed.
# Just ensure claude CLI is logged in: claude login
export KIS_APP_KEY="..."         # Korea Investment Securities API
export KIS_APP_SECRET="..."      # KIS API secret
export TELEGRAM_BOT_TOKEN="..."  # Telegram bot token
export GH_TOKEN="..."            # GitHub token (optional, for issue integration)
```

For local cron setup:
```bash
crontab -e
# Add: 0 */8 * * * cd /path/to/samsungelc-agent && ./scripts/evolve.sh >> /tmp/evolve.log 2>&1
```

See `.env.example` for the full list.

## Architecture

**Python source** (`src/`):
- `src/data/` — Data collection layer (agent evolves this)
  - `kis_api.py` — KIS OpenAPI client with OAuth token caching
  - `stock_price.py` — Samsung Electronics OHLCV data (005930.KS)
  - `supply_demand.py` — Foreign/institutional trading + ownership (KIS + Naver)
  - `exchange_rate_fetcher.py` — USD/KRW daily OHLC
  - `database.py` — SQLite CRUD for 4 tables (daily_prices, foreign_trading, exchange_rate, foreign_ownership)
  - `config.py` — Environment variables and paths
- `src/analysis/` — Analysis layer (agent builds this through evolution)
- `src/delivery/` — Report delivery
  - `telegram_bot.py` — HTML message broadcast to subscribers
  - `subscribers.py` — Subscriber list loader
- `src/main.py` — Daily orchestration entry point

**Issue system** (`scripts/issue_manager.py`):
- GitHub Issues를 에이전트-커뮤니티 소통 채널로 사용
- 라벨: `agent-input` (사용자 요청), `agent-self` (에이전트 할일), `bug`, `in-progress`
- `scripts/context.sh`가 이슈를 로드하여 `$AGENT_CONTEXT`에 포함
- 진화 세션 후 처리한 이슈에 코멘트 + 상태 전이 자동화
- 디자인 문서: `docs/designs/github-issues-integration.md`

**Evolution loop** (`scripts/evolve.sh`):
1. Verifies tests pass (`pytest tests/`)
2. Loads context including community issues (`scripts/context.sh`)
3. **Phase A** (Planning): Claude CLI reads source + journal + issues, writes `SESSION_PLAN.md`
4. **Phase B** (Implementation): Claude CLI executes each task (15 min each), with pytest verification gate
5. Processes issue references (`Fixes #N` / `Partially-fixes #N`) — comments + transitions
6. Verifies tests, reverts on failure → writes journal entry (+ agent-self issues) → pushes

**Skills** (`skills/`): Three domain-specific skills guide the agent's evolution:
- `self-assess` — evaluate analysis capabilities, find gaps
- `evolve` — safely modify source, test, revert on failure
- `communicate` — write journal entries, reflect on learnings

**Memory system** (`memory/`):
- `memory/learnings.jsonl` — append-only self-reflection archive (JSONL)
- `memory/active_learnings.md` — synthesized prompt context (regenerated periodically)
- Archives appended via `python3` with `json.dumps()` (never `echo`). Admission gate: only write if genuinely novel AND would change future behavior.
- Context loaded by `scripts/context.sh` → `$AGENT_CONTEXT`

**State files**:
- `IDENTITY.md` — mission and rules (DO NOT MODIFY)
- `PERSONALITY.md` — voice and values (DO NOT MODIFY)
- `JOURNAL.md` — evolution log (append at top, never delete)
- `DAY_COUNT` — integer tracking current evolution day (birth: 2026-03-21)
- `SESSION_PLAN.md` — ephemeral, written by planning agent (gitignored)

## Safety Rules

Enforced by `evolve` skill and `evolve.sh`:
- Never modify `IDENTITY.md`, `PERSONALITY.md`, `scripts/evolve.sh`, `scripts/context.sh`, or `.github/workflows/`
- Every code change must pass `pytest tests/`
- If tests fail after changes, revert with `git checkout -- src/ tests/`
- Never delete existing tests
- Write tests before adding features
- Stay within Samsung Electronics stock analysis domain
