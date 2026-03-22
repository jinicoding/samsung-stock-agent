#!/bin/bash
# scripts/setup_labels.sh — One-time GitHub label setup for SSANAI agent.
# Usage: ./scripts/setup_labels.sh

set -euo pipefail

REPO="${REPO:-jinicoding/samsung-stock-agent}"

echo "Creating labels for $REPO..."

gh label create "agent-input" \
    --description "사람이 에이전트에게 주는 입력" \
    --color "0E8A16" \
    --repo "$REPO" 2>/dev/null || echo "  agent-input: already exists"

gh label create "agent-self" \
    --description "에이전트가 자기 자신을 위해 등록한 이슈" \
    --color "1D76DB" \
    --repo "$REPO" 2>/dev/null || echo "  agent-self: already exists"

gh label create "bug" \
    --description "버그 리포트" \
    --color "D73A4A" \
    --repo "$REPO" 2>/dev/null || echo "  bug: already exists"

gh label create "in-progress" \
    --description "에이전트가 현재 세션에서 처리 중" \
    --color "FBCA04" \
    --repo "$REPO" 2>/dev/null || echo "  in-progress: already exists"

echo "Done."
