#!/usr/bin/env python3
"""
issue_processor.py — Fetch open GitHub issues labelled 'claude-task',
resolve each one with the Claude Agent SDK (Read/Edit/Write/Glob/Grep),
then commit changes, push to GitHub, and close the issue.
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

REPO = "ct9915/Uploader4MISP"
LABEL = "claude-task"
REPO_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def _gh(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["gh", *args],
        capture_output=True, text=True, check=check,
    )


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_DIR, capture_output=True, text=True, check=check,
    )


def get_open_issues() -> list[dict]:
    result = _gh(
        "issue", "list",
        "--repo", REPO,
        "--label", LABEL,
        "--state", "open",
        "--json", "number,title,body",
    )
    return json.loads(result.stdout or "[]")


def post_comment(number: int, body: str) -> None:
    _gh("issue", "comment", str(number), "--repo", REPO, "--body", body)


def close_issue(number: int) -> None:
    _gh("issue", "close", str(number), "--repo", REPO)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def has_changes() -> bool:
    status = _git("status", "--porcelain", check=False)
    return bool(status.stdout.strip())


def commit_and_push(issue_number: int, summary: str) -> str | None:
    """Stage all changes, commit, push, and return the commit SHA (or None if nothing to commit)."""
    if not has_changes():
        return None

    _git("add", "-A")

    commit_msg = (
        f"fix: resolve issue #{issue_number} via Claude\n\n"
        f"{summary[:800]}\n\n"
        f"Closes #{issue_number}\n\n"
        f"Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
    )
    _git("commit", "-m", commit_msg)
    _git("push")

    sha = _git("rev-parse", "HEAD")
    return sha.stdout.strip()


# ---------------------------------------------------------------------------
# Claude Agent SDK
# ---------------------------------------------------------------------------

async def resolve_issue(issue: dict) -> str:
    number = issue["number"]
    title = issue["title"]
    body = issue["body"] or "(no description)"

    prompt = f"""\
You are a senior software engineer working on the **Uploader4MISP** repository
located at `{REPO_DIR}`.

Your task is to **fully resolve** the following GitHub issue.

---
**Issue #{number}: {title}**

{body}
---

Instructions:
1. Read the relevant source files to understand the current code.
2. Make all necessary changes (edit existing files or create new ones).
3. Do NOT run git commands — the automation script handles committing and pushing.
4. When finished, briefly summarise what you changed and why.
"""

    result_text = None

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            cwd=str(REPO_DIR),
            allowed_tools=["Read", "Edit", "Write", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=80,
            setting_sources=["project"],   # loads CLAUDE.md for repo context
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    return result_text or "Issue resolved (no summary provided)."


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    issues = get_open_issues()

    if not issues:
        print("No open issues with 'claude-task' label.")
        return

    print(f"Found {len(issues)} issue(s) to process.")

    for issue in issues:
        number = issue["number"]
        title = issue["title"]
        print(f"\n{'='*60}")
        print(f"Processing #{number}: {title}")

        try:
            # Pull latest to avoid conflicts
            _git("pull", "--rebase", "--quiet", check=False)

            summary = await resolve_issue(issue)
            print(f"  Agent summary: {summary[:120]}...")

            commit_sha = commit_and_push(number, summary)

            if commit_sha:
                comment = (
                    f"✅ **已由 Claude 自動解決**\n\n"
                    f"{summary}\n\n"
                    f"**Commit:** https://github.com/{REPO}/commit/{commit_sha}"
                )
                post_comment(number, comment)
                close_issue(number)
                print(f"  ✓ Closed. Commit: {commit_sha[:8]}")
            else:
                comment = (
                    f"⚠️ **Claude 處理完畢，但未偵測到檔案異動。**\n\n"
                    f"{summary}"
                )
                post_comment(number, comment)
                print(f"  ⚠ No file changes detected for #{number}.")

        except Exception as exc:
            msg = f"❌ 處理 issue #{number} 時發生錯誤：\n```\n{exc}\n```"
            print(f"  ✗ Error: {exc}", file=sys.stderr)
            try:
                post_comment(number, msg)
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())
