import os
import difflib
from typing import Tuple
import subprocess
from src.tools import git_utils

def read_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def make_unified_diff(path: str, new_content: str, repo_root: str = ".") -> str:
    """
    Return a unified diff for path between current repo content (or empty if new) and new_content.
    The result is a text patch suitable for 'git apply'.
    """
    old_content = ""
    abs_path = os.path.join(repo_root, path)
    if os.path.exists(abs_path):
        with open(abs_path, "r", encoding="utf-8") as f:
            old_content = f.read()

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    # difflib.unified_diff adds file paths; use a/ and b/ to make git happy
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{path}", tofile=f"b/{path}")
    return "".join(diff)

def apply_file_patch(path: str, new_content: str, branch_name: str, commit_message: str, issue_number: int=None, dry_run: bool=False) -> dict:
    """
    Create a branch (if needed), craft a patch, apply it safely, commit, push, and optionally open a PR.
    Returns a dict with status and messages.
    """
    # create branch
    res = {"applied": False, "patch": None, "commit": None, "push": None, "pr": None, "error": None, "dry_run": dry_run}
    try:
        git_utils.create_branch(branch_name, dry_run=dry_run)
        patch_text = make_unified_diff(path, new_content)
        res["patch"] = patch_text

        if not patch_text.strip():
            res["error"] = "No changes detected."
            return res

        ok, msg = git_utils.stage_patch(patch_text, dry_run=dry_run)
        if not ok:
            res["error"] = f"git apply failed: {msg}"
            return res

        commit_sha = git_utils.commit_index(commit_message, dry_run=dry_run)
        res["applied"] = True
        res["commit"] = commit_sha

        okpush, push_msg = git_utils.push_branch(branch_name, dry_run=dry_run)
        res["push"] = push_msg
        if not okpush:
            res["error"] = "Push failed: " + push_msg
            return res

        pr_title = commit_message if issue_number is None else f"[Issue #{issue_number}] {commit_message}"
        pr_body = f"Automated change by agent for issue #{issue_number}" if issue_number else "Automated change by agent"
        pr = git_utils.create_pull_request(branch_name, pr_title, pr_body, dry_run=dry_run)
        res["pr"] = pr
        return res

    except Exception as e:
        res["error"] = str(e)
        return res
