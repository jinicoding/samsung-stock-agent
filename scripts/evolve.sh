#!/bin/bash
# scripts/evolve.sh — One evolution cycle for SSANAI (싸나이) agent.
# Adapted from yoyo-evolve. Run locally via cron or manually.
# Uses Claude Max subscription via claude CLI (no API key needed).
#
# Usage:
#   ./scripts/evolve.sh
#
# Environment:
#   MODEL              — LLM model (default: claude-opus-4-6)
#   TIMEOUT            — Planning phase time budget in seconds (default: 1200)

set -euo pipefail

MODEL="${MODEL:-claude-opus-4-6}"
TIMEOUT="${TIMEOUT:-1200}"
BIRTH_DATE="2026-03-21"
DATE=$(date +%Y-%m-%d)
SESSION_TIME=$(date +%H:%M)

# Compute calendar day
if date -j &>/dev/null; then
    DAY=$(( ($(date +%s) - $(date -j -f "%Y-%m-%d" "$BIRTH_DATE" +%s)) / 86400 ))
else
    DAY=$(( ($(date +%s) - $(date -d "$BIRTH_DATE" +%s)) / 86400 ))
fi
echo "$DAY" > DAY_COUNT

echo "=== Day $DAY ($DATE $SESSION_TIME) ==="
echo "Model: $MODEL"
echo "Plan timeout: ${TIMEOUT}s | Impl timeout: 900s/task"
echo ""

# Ensure directories exist
mkdir -p memory

# ── Step 0: Load identity context ──
if [ -f scripts/context.sh ]; then
    AGENT_REPO="." source scripts/context.sh
else
    echo "WARNING: scripts/context.sh not found" >&2
    AGENT_CONTEXT=""
fi

# ── Step 1: Verify starting state ──
echo "→ Checking tests..."
if ! pytest tests/ -q 2>&1; then
    echo "  FATAL: Tests fail. Cannot evolve."
    exit 1
fi
echo "  Tests OK."
echo ""

# ── Step 2: Timeout command detection ──
TIMEOUT_CMD="timeout"
if ! command -v timeout &>/dev/null; then
    if command -v gtimeout &>/dev/null; then
        TIMEOUT_CMD="gtimeout"
    else
        TIMEOUT_CMD=""
    fi
fi

SESSION_START_SHA=$(git rev-parse HEAD)
COMPLETED_TASKS=""
TOTAL_TASKS=0
echo "→ Starting evolution session..."
echo ""

# ── Phase A: Planning session ──
echo "  Phase A: Planning..."
PLAN_PROMPT=$(mktemp)
cat > "$PLAN_PROMPT" <<'PLANEOF'
You are SSANAI (싸나이), a self-evolving AI stock analysis agent for Samsung Electronics (삼성전자). Today is Day DAYNUM (DATESTR TIMESTR).

CONTEXTBLOCK

Now read these files:
1. All .py files under src/ (your current source code — this is YOU)
2. JOURNAL.md (your recent history — last 10 entries)
3. tests/ (your test suite)

=== PHASE 1: Self-Assessment ===

Read your own source code carefully. Then evaluate:
- What analysis capabilities do you have now?
- What's the most important capability you're missing?
- Are there bugs, errors, or data quality issues?
- Is your Telegram report as useful as it could be?

=== PHASE 2: Research ===

You have internet access via bash (curl).
Think strategically: what stock analysis techniques would make you better?
Consider: technical indicators, fundamental analysis, news sentiment,
supply-demand patterns, cross-market correlations.

=== PHASE 3: Write SESSION_PLAN.md ===

You MUST produce a file called SESSION_PLAN.md with your plan.

Priority:
0. Fix test failures (if any — this overrides everything)
1. Community issues (COMMUNITY ISSUES section above) — address user requests
2. Analysis capability gaps — what do investors need that you can't do yet?
3. Self-discovered bugs or data quality issues
4. Report quality improvements
5. New data sources or indicators

IMPORTANT: If you address a community issue, include "Fixes #N" (to fully resolve)
or "Partially-fixes #N" (if only part of the request is addressed) in the task title.
Example: "### Task 1: 볼린저 밴드 분석 추가 (Fixes #12)"

Write SESSION_PLAN.md with EXACTLY this format:

## Session Plan

### Task 1: [title] (Fixes #N or Partially-fixes #N if applicable)
Files: [files to modify]
Description: [what to do — specific enough for a focused implementation agent]

### Task 2: [title]
Files: [files to modify]
Description: [what to do]

After writing SESSION_PLAN.md, commit it:
git add SESSION_PLAN.md && git commit -m "Day DAYNUM (TIMESTR): session plan"

Then STOP. Do not implement anything. Your job is planning only.
PLANEOF

# Substitute variables into prompt
sed -i "s/DAYNUM/$DAY/g; s/DATESTR/$DATE/g; s/TIMESTR/$SESSION_TIME/g" "$PLAN_PROMPT"
# Replace context block (use python to handle multiline safely)
python3 -c "
import sys
prompt = open('$PLAN_PROMPT').read()
context = '''$AGENT_CONTEXT'''
prompt = prompt.replace('CONTEXTBLOCK', context)
open('$PLAN_PROMPT', 'w').write(prompt)
" 2>/dev/null || true

PLAN_EXIT=0
${TIMEOUT_CMD:+$TIMEOUT_CMD "$TIMEOUT"} claude -p "$(cat "$PLAN_PROMPT")" \
    --model "$MODEL" \
    2>&1 || PLAN_EXIT=$?
rm -f "$PLAN_PROMPT"

if [ "$PLAN_EXIT" -eq 124 ]; then
    echo "  WARNING: Planning agent TIMED OUT after ${TIMEOUT}s."
fi

# Fallback if no plan produced
if [ ! -f SESSION_PLAN.md ]; then
    echo "  Planning agent did not produce SESSION_PLAN.md — falling back."
    cat > SESSION_PLAN.md <<FALLBACK
## Session Plan

### Task 1: Self-improvement
Files: src/
Description: Read your own source code, identify the most impactful improvement you can make, implement it, and commit.
FALLBACK
    git add SESSION_PLAN.md && git commit -m "Day $DAY ($SESSION_TIME): fallback session plan" || true
fi

echo "  Planning complete."
echo ""

# ── Phase B: Implementation loop ──
echo "  Phase B: Implementation..."
IMPL_TIMEOUT=900
TASK_NUM=0
while IFS= read -r task_line; do
    TASK_NUM=$((TASK_NUM + 1))
    TOTAL_TASKS=$TASK_NUM
    task_title="${task_line#*: }"
    echo "  → Task $TASK_NUM: $task_title"

    PRE_TASK_SHA=$(git rev-parse HEAD)

    # Extract task block
    TASK_DESC=$(awk "/^### Task $TASK_NUM:/{found=1} found{if(/^### / && !/^### Task $TASK_NUM:/)exit; print}" SESSION_PLAN.md)

    if [ -z "$TASK_DESC" ]; then
        echo "    WARNING: Could not extract Task $TASK_NUM. Skipping."
        continue
    fi

    TASK_PROMPT=$(mktemp)
    cat > "$TASK_PROMPT" <<TEOF
You are SSANAI (싸나이), a self-evolving AI stock analysis agent for Samsung Electronics. Day $DAY ($DATE $SESSION_TIME).

$AGENT_CONTEXT

Your ONLY job: implement this single task and commit.

$TASK_DESC

Rules:
- Write a test first if possible
- Use edit_file for surgical changes, not full file rewrites
- Run: pytest tests/ -q after changes
- If tests fail, read the error and fix it. Keep trying until it passes.
- Only if you've tried 3+ times and are stuck, revert with: git checkout -- src/ tests/
- After tests pass, commit: git add -A && git commit -m "Day $DAY ($SESSION_TIME): $task_title (Task $TASK_NUM)"
- Do NOT work on anything else.
TEOF

    TASK_EXIT=0
    ${TIMEOUT_CMD:+$TIMEOUT_CMD "$IMPL_TIMEOUT"} claude -p "$(cat "$TASK_PROMPT")" \
        --model "$MODEL" \
        2>&1 || TASK_EXIT=$?
    rm -f "$TASK_PROMPT"

    # ── Per-task verification gate ──
    TASK_OK=true

    # Check 1: Protected files
    PROTECTED_CHANGES=$(git diff --name-only "$PRE_TASK_SHA"..HEAD -- \
        IDENTITY.md PERSONALITY.md \
        scripts/evolve.sh scripts/context.sh \
        .github/workflows/ 2>/dev/null || true)

    if [ -n "$PROTECTED_CHANGES" ]; then
        echo "    BLOCKED: Modified protected files: $PROTECTED_CHANGES"
        TASK_OK=false
    fi

    # Check 2: Tests
    if [ "$TASK_OK" = true ]; then
        if ! pytest tests/ -q 2>&1; then
            echo "    BLOCKED: Tests fail after Task $TASK_NUM"
            TASK_OK=false
        fi
    fi

    # Revert if failed
    if [ "$TASK_OK" = false ]; then
        echo "    Reverting Task $TASK_NUM..."
        git reset --hard "$PRE_TASK_SHA" 2>/dev/null || true
        git clean -fd 2>/dev/null || true
    else
        COMPLETED_TASKS="$COMPLETED_TASKS $TASK_NUM"
        echo "    Task $TASK_NUM: verified OK"
    fi

done < <(grep '^### Task ' SESSION_PLAN.md | head -5)

echo ""

# ── Step 5: Post-implementation verification ──
echo "→ Final verification..."
if ! pytest tests/ -q 2>&1; then
    echo "  Tests fail after implementation. Reverting to session start."
    git reset --hard "$SESSION_START_SHA" 2>/dev/null || true
    git commit -m "Day $DAY ($SESSION_TIME): revert session (tests fail)" --allow-empty || true
fi
echo ""

# ── Step 5.5: Process issue references from SESSION_PLAN ──
echo "→ Processing issue references..."
if python3 scripts/issue_manager.py check >/dev/null 2>&1 && [ -f SESSION_PLAN.md ]; then
    ISSUE_REFS=$(cat SESSION_PLAN.md | python3 scripts/issue_manager.py parse-refs 2>/dev/null || echo '{"fixes":[],"partials":[]}')
    FIXES=$(echo "$ISSUE_REFS" | python3 -c "import sys,json; print(' '.join(str(x) for x in json.load(sys.stdin).get('fixes',[])))" 2>/dev/null || true)
    PARTIALS=$(echo "$ISSUE_REFS" | python3 -c "import sys,json; print(' '.join(str(x) for x in json.load(sys.stdin).get('partials',[])))" 2>/dev/null || true)

    SESSION_END_SHA=$(git rev-parse --short HEAD)
    COMMITS_SUMMARY=$(git log --oneline "$SESSION_START_SHA".."$SESSION_END_SHA" 2>/dev/null | head -5 || echo "no commits")

    for ISSUE_NUM in $FIXES; do
        COMMENT_BODY="🤖 **싸나이 Day $DAY ($SESSION_TIME)** — 이 이슈를 처리했습니다.

커밋:
\`\`\`
$COMMITS_SUMMARY
\`\`\`

[저널 보기](https://jinicoding.github.io/samsung-stock-agent/)"
        python3 scripts/issue_manager.py transition --issue "$ISSUE_NUM" --action start 2>/dev/null || true
        python3 scripts/issue_manager.py comment --issue "$ISSUE_NUM" --body "$COMMENT_BODY" 2>/dev/null || true
        python3 scripts/issue_manager.py transition --issue "$ISSUE_NUM" --action complete 2>/dev/null || true
    done

    for ISSUE_NUM in $PARTIALS; do
        COMMENT_BODY="🤖 **싸나이 Day $DAY ($SESSION_TIME)** — 이 이슈를 부분적으로 처리했습니다. 추가 작업이 남아있습니다.

커밋:
\`\`\`
$COMMITS_SUMMARY
\`\`\`

[저널 보기](https://jinicoding.github.io/samsung-stock-agent/)"
        python3 scripts/issue_manager.py comment --issue "$ISSUE_NUM" --body "$COMMENT_BODY" 2>/dev/null || true
        python3 scripts/issue_manager.py transition --issue "$ISSUE_NUM" --action skip 2>/dev/null || true
    done

    if [ -n "$FIXES" ] || [ -n "$PARTIALS" ]; then
        echo "  Fixes: ${FIXES:-none} | Partial: ${PARTIALS:-none}"
    else
        echo "  No issue references found in SESSION_PLAN.md"
    fi
else
    echo "  Skipped (gh not available or no SESSION_PLAN.md)"
fi
echo ""

# ── Step 5.6: Create issues for incomplete tasks ──
echo "→ Creating issues for incomplete tasks..."
if python3 scripts/issue_manager.py check >/dev/null 2>&1 && [ -f SESSION_PLAN.md ]; then
    CREATED_ISSUES=0
    for T in $(seq 1 "$TOTAL_TASKS"); do
        if echo "$COMPLETED_TASKS" | grep -qw "$T"; then
            continue
        fi
        # Extract task title and description
        TASK_TITLE=$(awk "/^### Task $T:/{gsub(/^### Task $T: /,\"\"); gsub(/ *\\(.*\\)$/,\"\"); print; exit}" SESSION_PLAN.md)
        TASK_BODY=$(awk "/^### Task $T:/{found=1; next} found{if(/^### / && !/^### Task $T:/)exit; print}" SESSION_PLAN.md | head -10)

        if [ -n "$TASK_TITLE" ]; then
            python3 scripts/issue_manager.py create \
                --title "$TASK_TITLE" \
                --body "Day $DAY 세션에서 미완료된 태스크입니다.

$TASK_BODY" \
                --label agent-self 2>/dev/null && CREATED_ISSUES=$((CREATED_ISSUES + 1)) || true
        fi
    done
    echo "  Created $CREATED_ISSUES issue(s) for incomplete tasks"
else
    echo "  Skipped (gh not available)"
fi
echo ""

# ── Step 6: Journal entry + learnings ──
echo "→ Writing journal entry..."
JOURNAL_PROMPT="You are SSANAI (싸나이). Day $DAY ($DATE $SESSION_TIME).

$AGENT_CONTEXT

Write a journal entry for today's session. Read:
1. git log --oneline $SESSION_START_SHA..HEAD
2. JOURNAL.md (previous entries for style)

INSERT a new entry at the TOP of JOURNAL.md:

## Day $DAY — $SESSION_TIME — [short title]

[2-4 sentences: what you tried, what worked, what's next. Write in Korean.]

If you learned something genuinely novel, append to memory/learnings.jsonl via python3:
python3 -c \"import json; entry={'type':'lesson','day':$DAY,'ts':'$(date -u +%Y-%m-%dT%H:%M:%SZ)','source':'evolution','title':'SHORT','context':'WHAT','takeaway':'INSIGHT'}; open('memory/learnings.jsonl','a').write(json.dumps(entry,ensure_ascii=False)+chr(10))\"

If you identified important follow-up work during this session (max 3 items), create
agent-self issues via:
python3 scripts/issue_manager.py create --title \"TITLE\" --body \"DESCRIPTION\" --label agent-self
Only create issues for genuinely important next steps, not trivial improvements.

Commit: git add -A && git commit -m 'Day $DAY ($SESSION_TIME): journal entry'"

claude -p "$JOURNAL_PROMPT" --model "$MODEL" 2>&1 || true

# Fallback journal if agent skipped — only if there were actual commits
if ! grep -q "## Day $DAY.*$SESSION_TIME" JOURNAL.md 2>/dev/null; then
    COMMITS=$(git log --oneline "$SESSION_START_SHA..HEAD" 2>/dev/null || true)
    if [ -n "$COMMITS" ]; then
        ENTRY="## Day $DAY — $SESSION_TIME — auto-generated

Commits this session:
$COMMITS
"
        # Insert after "# Journal" header line
        if grep -q "^# Journal" JOURNAL.md 2>/dev/null; then
            sed -i "/^# Journal$/a\\
\\
$ENTRY" JOURNAL.md
        else
            EXISTING=$(cat JOURNAL.md 2>/dev/null || echo "# Journal")
            printf '# Journal\n\n%s\n\n%s' "$ENTRY" "$EXISTING" > JOURNAL.md
        fi
        git add JOURNAL.md && git commit -m "Day $DAY ($SESSION_TIME): journal entry (auto)" || true
    else
        echo "  No commits this session — skipping fallback journal."
    fi
fi

echo ""

# ── Step 7: Push ──
echo "→ Pushing changes..."
git push 2>/dev/null || echo "  Push failed or no remote configured."

echo ""
echo "=== Evolution session complete (Day $DAY) ==="
