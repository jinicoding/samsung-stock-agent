"""Tests for scripts/issue_manager.py.

All gh CLI calls are mocked via _run_gh to avoid real GitHub API hits.
"""

import json
from unittest.mock import patch

import pytest

# Add scripts/ to path for import
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.issue_manager import (
    truncate,
    priority_score,
    cmd_check,
    cmd_list,
    cmd_list_all,
    cmd_comment,
    cmd_create,
    cmd_transition,
    format_issues_for_prompt,
    parse_issue_refs,
)

MOCK_GH = "scripts.issue_manager._run_gh"


# ── truncate ────────────────────────────────────────────────────────

class TestTruncate:
    def test_short_text(self):
        assert truncate("hello", 500) == "hello"

    def test_exact_limit(self):
        text = "a" * 500
        assert truncate(text, 500) == text

    def test_over_limit(self):
        text = "a" * 501
        result = truncate(text, 500)
        assert len(result) == 503  # 500 + "..."
        assert result.endswith("...")

    def test_empty_string(self):
        assert truncate("", 500) == ""

    def test_none_like(self):
        assert truncate("", 10) == ""

    def test_whitespace_strip(self):
        assert truncate("  hello  ", 500) == "hello"

    def test_unicode_emoji(self):
        text = "🔥" * 300
        result = truncate(text, 500)
        assert len(result) <= 503


# ── priority_score ──────────────────────────────────────────────────

class TestPriorityScore:
    def test_basic_score(self):
        issue = {
            "reactions": {"THUMBS_UP": 3, "total": 5},
            "comments": [{"body": "a"}, {"body": "b"}],
        }
        # 3*2 + 5 + 2 = 13
        assert priority_score(issue) == 13

    def test_zero_engagement(self):
        issue = {"reactions": {"THUMBS_UP": 0, "total": 0}, "comments": []}
        assert priority_score(issue) == 0

    def test_missing_fields(self):
        assert priority_score({}) == 0

    def test_comments_as_int(self):
        issue = {"reactions": {"THUMBS_UP": 1, "total": 1}, "comments": 5}
        # 1*2 + 1 + 5 = 8
        assert priority_score(issue) == 8

    def test_reactions_as_list(self):
        issue = {
            "reactions": [
                {"content": "THUMBS_UP"},
                {"content": "THUMBS_UP"},
                {"content": "HEART"},
            ],
            "comments": [],
        }
        # thumbs=2, total=3 → 2*2 + 3 + 0 = 7
        assert priority_score(issue) == 7


# ── cmd_check ───────────────────────────────────────────────────────

class TestCmdCheck:
    @patch(MOCK_GH, return_value=("Logged in", "", 0))
    def test_available(self, mock):
        assert cmd_check() == 0

    @patch(MOCK_GH, return_value=("", "not logged in", 1))
    def test_not_authenticated(self, mock):
        assert cmd_check() == 1

    @patch(MOCK_GH, return_value=("", "gh CLI not installed", 127))
    def test_not_installed(self, mock):
        assert cmd_check() == 1


# ── cmd_list ────────────────────────────────────────────────────────

SAMPLE_ISSUES = [
    {
        "number": 1,
        "title": "볼린저 밴드 추가",
        "body": "볼린저 밴드 지표를 추가해주세요",
        "reactions": {"THUMBS_UP": 5, "total": 7},
        "comments": [{"body": "좋아요"}, {"body": "+1"}],
        "createdAt": "2026-03-20T10:00:00Z",
        "labels": [{"name": "agent-input"}],
    },
    {
        "number": 2,
        "title": "RSI 추가",
        "body": "RSI 지표 추가 요청",
        "reactions": {"THUMBS_UP": 1, "total": 1},
        "comments": [],
        "createdAt": "2026-03-21T10:00:00Z",
        "labels": [{"name": "agent-input"}],
    },
]


class TestCmdList:
    @patch(MOCK_GH, return_value=(json.dumps(SAMPLE_ISSUES), "", 0))
    def test_returns_sorted(self, mock):
        result = cmd_list(label="agent-input", limit=10, sort="priority")
        assert len(result) == 2
        assert result[0]["number"] == 1  # higher priority
        assert "body_truncated" in result[0]

    @patch(MOCK_GH, return_value=("", "network error", 1))
    def test_gh_failure_returns_empty(self, mock):
        result = cmd_list()
        assert result == []

    @patch(MOCK_GH, return_value=("not json", "", 0))
    def test_malformed_json(self, mock):
        result = cmd_list()
        assert result == []

    @patch(MOCK_GH, return_value=("[]", "", 0))
    def test_empty_issues(self, mock):
        result = cmd_list()
        assert result == []

    @patch(MOCK_GH, return_value=("", "", 0))
    def test_empty_stdout(self, mock):
        result = cmd_list()
        assert result == []

    @patch(MOCK_GH, return_value=(json.dumps(SAMPLE_ISSUES), "", 0))
    def test_limit(self, mock):
        result = cmd_list(limit=1)
        assert len(result) == 1

    @patch(MOCK_GH, return_value=(json.dumps(SAMPLE_ISSUES), "", 0))
    def test_truncates_body(self, mock):
        result = cmd_list()
        for issue in result:
            assert len(issue["body_truncated"]) <= 503  # 500 + "..."


# ── cmd_comment ─────────────────────────────────────────────────────

class TestCmdComment:
    @patch(MOCK_GH)
    def test_success(self, mock):
        # First call: check existing comments; second call: post comment
        mock.side_effect = [
            (json.dumps({"comments": []}), "", 0),
            ("", "", 0),
        ]
        assert cmd_comment(1, "구현 완료") is True

    @patch(MOCK_GH)
    def test_dedup_skips(self, mock):
        mock.return_value = (
            json.dumps({"comments": [{"body": "구현 완료\n커밋: abc123"}]}),
            "", 0,
        )
        assert cmd_comment(1, "구현 완료") is True
        # Only one call (view), no comment call
        assert mock.call_count == 1

    @patch(MOCK_GH)
    def test_failure(self, mock):
        mock.side_effect = [
            (json.dumps({"comments": []}), "", 0),
            ("", "not found", 1),
        ]
        assert cmd_comment(1, "test") is False

    @patch(MOCK_GH, return_value=("", "", 0))
    def test_no_dedup(self, mock):
        assert cmd_comment(1, "test", dedup=False) is True
        assert mock.call_count == 1  # only the comment call


# ── cmd_create ──────────────────────────────────────────────────────

class TestCmdCreate:
    @patch(MOCK_GH)
    def test_success(self, mock):
        mock.side_effect = [
            ("[]", "", 0),  # duplicate check
            ("https://github.com/owner/repo/issues/42\n", "", 0),  # create
        ]
        assert cmd_create("New feature", "Body text") == 42

    @patch(MOCK_GH)
    def test_duplicate_title(self, mock):
        mock.return_value = (
            json.dumps([{"number": 5, "title": "Existing issue"}]),
            "", 0,
        )
        assert cmd_create("Existing issue", "body") is None

    @patch(MOCK_GH)
    def test_create_failure(self, mock):
        mock.side_effect = [
            ("[]", "", 0),  # no duplicates
            ("", "error", 1),  # create fails
        ]
        assert cmd_create("Title", "Body") is None


# ── cmd_transition ──────────────────────────────────────────────────

class TestCmdTransition:
    @patch(MOCK_GH, return_value=("", "", 0))
    def test_start(self, mock):
        assert cmd_transition(1, "start") is True
        args = mock.call_args[0][0]
        assert "--add-label" in args
        assert "in-progress" in args

    @patch(MOCK_GH, return_value=("", "", 0))
    def test_complete(self, mock):
        assert cmd_transition(1, "complete") is True
        # Should have called twice: remove label + close
        assert mock.call_count == 2

    @patch(MOCK_GH, return_value=("", "", 0))
    def test_skip(self, mock):
        assert cmd_transition(1, "skip") is True
        args = mock.call_args[0][0]
        assert "--remove-label" in args

    def test_unknown_action(self):
        assert cmd_transition(1, "invalid") is False


# ── format_issues_for_prompt ────────────────────────────────────────

class TestFormatIssues:
    def test_empty(self):
        result = format_issues_for_prompt([])
        assert "커뮤니티 요청이 없습니다" in result

    def test_formats_correctly(self):
        issues = [
            {
                "number": 12,
                "title": "볼린저 밴드",
                "body_truncated": "추가해주세요",
                "reactions": {"THUMBS_UP": 3},
                "comments": [{"body": "a"}],
                "labels": [{"name": "agent-input"}],
            }
        ]
        result = format_issues_for_prompt(issues)
        assert "#12" in result
        assert "볼린저 밴드" in result
        assert "Priority 1" in result
        assert "👍 3" in result


# ── parse_issue_refs ────────────────────────────────────────────────

class TestParseIssueRefs:
    def test_fixes(self):
        text = "### Task 1: 볼린저 밴드 (Fixes #12)"
        fixes, partials = parse_issue_refs(text)
        assert 12 in fixes
        assert partials == []

    def test_partially_fixes(self):
        text = "### Task 1: RSI (Partially-fixes #8)"
        fixes, partials = parse_issue_refs(text)
        assert fixes == []
        assert 8 in partials

    def test_both(self):
        text = """### Task 1: 볼린저 밴드 (Fixes #12)
### Task 2: MACD 일부 (Partially-fixes #5)"""
        fixes, partials = parse_issue_refs(text)
        assert 12 in fixes
        assert 5 in partials

    def test_no_refs(self):
        text = "### Task 1: Self improvement\nFiles: src/"
        fixes, partials = parse_issue_refs(text)
        assert fixes == []
        assert partials == []

    def test_multiple_fixes(self):
        text = "Fixes #1, Fixes #2, Fixes #3"
        fixes, partials = parse_issue_refs(text)
        assert fixes == [1, 2, 3]

    def test_case_insensitive(self):
        text = "fixes #10"
        fixes, partials = parse_issue_refs(text)
        assert 10 in fixes
