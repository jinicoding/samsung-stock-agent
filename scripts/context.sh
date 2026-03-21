#!/bin/bash
# scripts/context.sh — Build agent's identity context for prompts.
# Source this file, then use $AGENT_CONTEXT in any prompt.
#
# Usage:
#   AGENT_REPO="/path/to/samsungelc-agent" source scripts/context.sh
#   echo "$AGENT_CONTEXT"

_AGENT_REPO="${AGENT_REPO:-.}"

_IDENTITY=""
if [ -f "$_AGENT_REPO/IDENTITY.md" ]; then
    _IDENTITY=$(cat "$_AGENT_REPO/IDENTITY.md") || {
        echo "WARNING: Failed to read IDENTITY.md" >&2
        _IDENTITY=""
    }
else
    echo "WARNING: IDENTITY.md not found at $_AGENT_REPO/IDENTITY.md" >&2
fi

_PERSONALITY=""
if [ -f "$_AGENT_REPO/PERSONALITY.md" ]; then
    _PERSONALITY=$(cat "$_AGENT_REPO/PERSONALITY.md") || {
        echo "WARNING: Failed to read PERSONALITY.md" >&2
        _PERSONALITY=""
    }
else
    echo "WARNING: PERSONALITY.md not found at $_AGENT_REPO/PERSONALITY.md" >&2
fi

# Active learnings — no warning if missing
_LEARNINGS=""
if [ -f "$_AGENT_REPO/memory/active_learnings.md" ]; then
    _LEARNINGS=$(cat "$_AGENT_REPO/memory/active_learnings.md") || _LEARNINGS=""
fi

AGENT_CONTEXT="=== WHO YOU ARE ===

${_IDENTITY:-Read IDENTITY.md for your rules and constitution.}

=== YOUR VOICE ===

${_PERSONALITY:-Read PERSONALITY.md for your voice and values.}

=== SELF-WISDOM ===

${_LEARNINGS:-No learnings yet. This is your first session.}"
