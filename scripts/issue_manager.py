#!/usr/bin/env python3
"""GitHub Issues manager for SSANAI agent.

Provides CLI subcommands to read, comment, create, and transition issues.
All GitHub API calls go through _run_gh() for centralized error handling
and easy test mocking.

Usage:
    python3 scripts/issue_manager.py check
    python3 scripts/issue_manager.py list --label agent-input --limit 10 --sort priority
    python3 scripts/issue_manager.py comment --issue 12 --body "구현 완료"
    python3 scripts/issue_manager.py create --title "TODO" --body "내용" --label agent-self
    python3 scripts/issue_manager.py transition --issue 12 --action start|complete|skip
"""

import argparse
import json
import re
import subprocess
import sys
from typing import Any  # noqa: F401


# ── gh CLI wrapper ──────────────────────────────────────────────────

def _run_gh(args: list[str], timeout: int = 30) -> tuple[str, str, int]:
    """Run a gh CLI command. Returns (stdout, stderr, returncode).

    All gh interactions go through this function so tests can mock it
    in a single place.
    """
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return "", "gh CLI not installed", 127
    except subprocess.TimeoutExpired:
        return "", f"gh command timed out after {timeout}s", 124


# ── Utilities ───────────────────────────────────────────────────────

def truncate(text: str, max_len: int = 500) -> str:
    """Truncate text to max_len characters."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def priority_score(issue: dict) -> float:
    """Score an issue by community engagement.

    reactions (thumbs up weight x2) + total comments.
    Higher = more community demand.
    """
    reactions = issue.get("reactions", {})
    # thumbsUp (👍) counts double
    thumbs_up = 0
    if isinstance(reactions, dict):
        thumbs_up = reactions.get("THUMBS_UP", 0)
        total_reactions = reactions.get("total", 0)
    elif isinstance(reactions, list):
        # gh sometimes returns reactions as list
        total_reactions = len(reactions)
        thumbs_up = sum(1 for r in reactions if r.get("content") == "THUMBS_UP")
    else:
        total_reactions = 0

    comments_count = issue.get("comments", [])
    if isinstance(comments_count, list):
        comments_count = len(comments_count)
    elif not isinstance(comments_count, int):
        comments_count = 0

    return thumbs_up * 2 + total_reactions + comments_count


# ── Subcommands ─────────────────────────────────────────────────────

def cmd_check() -> int:
    """Check if gh CLI is available and authenticated. Exit 0=OK, 1=fail."""
    stdout, stderr, rc = _run_gh(["auth", "status"])
    if rc == 0:
        print("→ gh CLI: available and authenticated")
        return 0
    else:
        print(f"WARNING: gh not available — {stderr.strip()}", file=sys.stderr)
        return 1


def cmd_list(label: str = "agent-input", limit: int = 10,
             sort: str = "priority") -> list[dict]:
    """List open issues by label, sorted by priority. Returns list of dicts."""
    fields = "number,title,body,reactions,comments,createdAt,labels"
    stdout, stderr, rc = _run_gh([
        "issue", "list",
        "--label", label,
        "--state", "open",
        "--limit", "50",  # fetch more, then sort and trim
        "--json", fields,
    ])

    if rc != 0:
        print(f"WARNING: gh issue list failed — {stderr.strip()}", file=sys.stderr)
        return []

    try:
        issues = json.loads(stdout) if stdout.strip() else []
    except json.JSONDecodeError as e:
        print(f"WARNING: malformed JSON from gh — {e}", file=sys.stderr)
        return []

    # Truncate bodies
    for issue in issues:
        issue["body_truncated"] = truncate(issue.get("body", ""), 500)

    # Sort
    if sort == "priority":
        issues.sort(key=priority_score, reverse=True)
    else:
        # default: newest first (already from gh)
        pass

    return issues[:limit]


def cmd_list_all(limit: int = 10) -> list[dict]:
    """List open issues across agent-input, agent-self, and bug labels."""
    all_issues: list[dict] = []
    for label in ["agent-input", "agent-self", "bug"]:
        all_issues.extend(cmd_list(label=label, limit=50, sort="created"))

    # Deduplicate by issue number
    seen: set[int] = set()
    unique: list[dict] = []
    for issue in all_issues:
        num = issue.get("number", 0)
        if num not in seen:
            seen.add(num)
            unique.append(issue)

    # Sort by priority
    unique.sort(key=priority_score, reverse=True)
    return unique[:limit]


def cmd_comment(issue_number: int, body: str, dedup: bool = True) -> bool:
    """Post a comment on an issue. Returns True on success.

    If dedup=True, checks for existing comments with the same first line
    to avoid duplicates.
    """
    if dedup:
        first_line = body.split("\n")[0][:80]
        stdout, stderr, rc = _run_gh([
            "issue", "view", str(issue_number),
            "--json", "comments",
        ])
        if rc == 0:
            try:
                data = json.loads(stdout)
                comments = data.get("comments", [])
                for c in comments:
                    if first_line in c.get("body", ""):
                        print(f"→ Issue #{issue_number}: comment already exists, skipping")
                        return True
            except (json.JSONDecodeError, KeyError):
                pass  # proceed to comment anyway

    _, stderr, rc = _run_gh([
        "issue", "comment", str(issue_number),
        "--body", body,
    ])

    if rc == 0:
        print(f"→ Issue #{issue_number}: commented")
        return True
    else:
        print(f"WARNING: comment on #{issue_number} failed — {stderr.strip()}",
              file=sys.stderr)
        return False


def cmd_create(title: str, body: str, label: str = "agent-self",
               max_per_session: int = 3) -> int | None:
    """Create a new issue. Returns issue number or None on failure.

    Checks for duplicate titles to prevent spam.
    """
    # Check for duplicates
    stdout, stderr, rc = _run_gh([
        "issue", "list",
        "--label", label,
        "--state", "open",
        "--search", title,
        "--json", "number,title",
        "--limit", "5",
    ])
    if rc == 0 and stdout.strip():
        try:
            existing = json.loads(stdout)
            for iss in existing:
                if iss.get("title", "").strip() == title.strip():
                    print(f"→ Issue create: duplicate title '{title}', skipping")
                    return None
        except json.JSONDecodeError:
            pass

    stdout, stderr, rc = _run_gh([
        "issue", "create",
        "--title", title,
        "--body", body,
        "--label", label,
    ])

    if rc == 0:
        # gh issue create prints the URL; extract issue number
        match = re.search(r"/issues/(\d+)", stdout)
        num = int(match.group(1)) if match else None
        print(f"→ Issue created: #{num} — {title}")
        return num
    else:
        print(f"WARNING: issue create failed — {stderr.strip()}", file=sys.stderr)
        return None


def cmd_transition(issue_number: int, action: str) -> bool:
    """Transition an issue's state.

    Actions:
        start    — add 'in-progress' label
        complete — remove 'in-progress', close issue, comment
        skip     — remove 'in-progress' label (partial fix, keep open)
    """
    if action == "start":
        _, stderr, rc = _run_gh([
            "issue", "edit", str(issue_number),
            "--add-label", "in-progress",
        ])
        if rc == 0:
            print(f"→ Issue #{issue_number}: → in-progress")
        else:
            print(f"WARNING: label add failed on #{issue_number} — {stderr.strip()}",
                  file=sys.stderr)
        return rc == 0

    elif action == "complete":
        # Remove in-progress label
        _run_gh([
            "issue", "edit", str(issue_number),
            "--remove-label", "in-progress",
        ])
        # Close the issue
        _, stderr, rc = _run_gh([
            "issue", "close", str(issue_number),
        ])
        if rc == 0:
            print(f"→ Issue #{issue_number}: closed")
        else:
            print(f"WARNING: close failed on #{issue_number} — {stderr.strip()}",
                  file=sys.stderr)
        return rc == 0

    elif action == "skip":
        # Remove in-progress, keep open
        _, stderr, rc = _run_gh([
            "issue", "edit", str(issue_number),
            "--remove-label", "in-progress",
        ])
        if rc == 0:
            print(f"→ Issue #{issue_number}: in-progress removed (partial fix)")
        return rc == 0

    else:
        print(f"WARNING: unknown transition action '{action}'", file=sys.stderr)
        return False


# ── Format for prompt injection ─────────────────────────────────────

def format_issues_for_prompt(issues: list[dict]) -> str:
    """Format issue list for injection into agent prompt."""
    if not issues:
        return "현재 커뮤니티 요청이 없습니다."

    lines = []
    for i, issue in enumerate(issues, 1):
        num = issue.get("number", "?")
        title = issue.get("title", "untitled")
        body = issue.get("body_truncated", "")

        reactions = issue.get("reactions", {})
        if isinstance(reactions, dict):
            thumbs = reactions.get("THUMBS_UP", 0)
        else:
            thumbs = 0

        comments = issue.get("comments", [])
        comment_count = len(comments) if isinstance(comments, list) else comments

        labels = issue.get("labels", [])
        label_names = [l.get("name", "") for l in labels if isinstance(l, dict)]
        label_str = ", ".join(label_names) if label_names else ""

        lines.append(
            f"[Priority {i}] #{num}: {title} "
            f"(👍 {thumbs}, 💬 {comment_count}) [{label_str}]"
        )
        if body:
            # Indent body, limit to 3 lines
            body_lines = body.split("\n")[:3]
            for bl in body_lines:
                lines.append(f"  > {bl}")
        lines.append("")

    return "\n".join(lines)


# ── Parse Fixes/Partially-fixes from SESSION_PLAN ──────────────────

def parse_issue_refs(text: str) -> tuple[list[int], list[int]]:
    """Parse 'Fixes #N' and 'Partially-fixes #N' from text.

    Returns (fixes_list, partial_list).
    """
    partials = [int(m) for m in re.findall(
        r"[Pp]artially-[Ff]ixes\s+#(\d+)", text
    )]
    partial_set = set(partials)

    # All "Fixes #N" matches (case-insensitive)
    all_fixes = [int(m) for m in re.findall(r"[Ff]ixes\s+#(\d+)", text)]

    # Remove those that are part of "Partially-fixes"
    fixes = [n for n in all_fixes if n not in partial_set]

    return fixes, partials


# ── CLI entry point ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SSANAI Issue Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check
    subparsers.add_parser("check", help="Check gh CLI availability")

    # list
    p_list = subparsers.add_parser("list", help="List open issues")
    p_list.add_argument("--label", default="agent-input")
    p_list.add_argument("--limit", type=int, default=10)
    p_list.add_argument("--sort", default="priority", choices=["priority", "created"])
    p_list.add_argument("--all-labels", action="store_true",
                        help="List across all agent labels")

    # comment
    p_comment = subparsers.add_parser("comment", help="Comment on an issue")
    p_comment.add_argument("--issue", type=int, required=True)
    p_comment.add_argument("--body", required=True)
    p_comment.add_argument("--no-dedup", action="store_true")

    # create
    p_create = subparsers.add_parser("create", help="Create a new issue")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--body", required=True)
    p_create.add_argument("--label", default="agent-self")

    # transition
    p_trans = subparsers.add_parser("transition", help="Transition issue state")
    p_trans.add_argument("--issue", type=int, required=True)
    p_trans.add_argument("--action", required=True,
                         choices=["start", "complete", "skip"])

    # format (for context.sh)
    p_format = subparsers.add_parser("format",
                                     help="List + format issues for prompt")
    p_format.add_argument("--limit", type=int, default=10)

    # parse-refs (for evolve.sh)
    p_parse = subparsers.add_parser("parse-refs",
                                    help="Parse Fixes/Partially-fixes from stdin")

    args = parser.parse_args()

    if args.command == "check":
        sys.exit(cmd_check())

    elif args.command == "list":
        if args.all_labels:
            issues = cmd_list_all(limit=args.limit)
        else:
            issues = cmd_list(label=args.label, limit=args.limit, sort=args.sort)
        print(json.dumps(issues, ensure_ascii=False, indent=2))

    elif args.command == "comment":
        ok = cmd_comment(args.issue, args.body, dedup=not args.no_dedup)
        sys.exit(0 if ok else 1)

    elif args.command == "create":
        num = cmd_create(args.title, args.body, label=args.label)
        if num:
            print(num)
        sys.exit(0 if num else 1)

    elif args.command == "transition":
        ok = cmd_transition(args.issue, args.action)
        sys.exit(0 if ok else 1)

    elif args.command == "format":
        issues = cmd_list_all(limit=args.limit)
        print(format_issues_for_prompt(issues))

    elif args.command == "parse-refs":
        text = sys.stdin.read()
        fixes, partials = parse_issue_refs(text)
        print(json.dumps({"fixes": fixes, "partials": partials}))


if __name__ == "__main__":
    main()
