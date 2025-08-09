import subprocess
import os
import tempfile
import json
from typing import Tuple, Optional
from src.config import GITHUB_TOKEN, REPO_OWNER

def _run(cmd, check=True, capture_output=True, text=True, cwd=None):
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=text, cwd=cwd)

def current_branch(dry_run: bool=False) -> str:
    if dry_run:
        return
    r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return r.stdout.strip()

def create_branch(branch_name: str, dry_run: bool=False) -> None:
    if dry_run:
        return 
    _run(["git", "fetch", "origin"])
    _run(["git", "checkout", "-b", branch_name])

def checkout_branch(branch_name: str, dry_run: bool=False) -> None:
    if dry_run:
        return
    _run(["git", "checkout", branch_name])

def stage_patch(patch_text: str, dry_run: bool=False) -> Tuple[bool, str]:
    """
    Apply a unified patch to the working tree and stage changes.
    Returns (success, message). If failure, returns git-apply stderr.
    """
    
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".patch") as tmp:
        tmp.write(patch_text)
        tmp.flush()
        tmp_path = tmp.name

    if dry_run:
      return True, "Dry run: patch validated but not applied."

    try:
        # try to apply and index (stage) the changes
        res = _run(["git", "apply", "--index", tmp_path], check=False)
        if res.returncode != 0:
            # capture stderr (res.stderr)
            return False, res.stderr
        return True, "Patch applied and indexed."
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

def commit_index(message: str, author_name: Optional[str]=None, author_email: Optional[str]=None, dry_run: bool=False) -> str:
    if dry_run:
        return True, "Dry run: patch validated but not applied."
    env = os.environ.copy()
    if author_name:
        env["GIT_AUTHOR_NAME"] = author_name
        env["GIT_COMMITTER_NAME"] = author_name
    if author_email:
        env["GIT_AUTHOR_EMAIL"] = author_email
        env["GIT_COMMITTER_EMAIL"] = author_email

    _run(["git", "commit", "-m", message], cwd=None, check=True)
    sha = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    return sha

def push_branch(branch_name: str, remote: str = "origin", dry_run: bool=False) -> Tuple[bool, str]:
    if dry_run:
        return True, f"Dry run: would have pushed branch {branch_name} to {remote}."
    res = _run(["git", "push", "--set-upstream", remote, branch_name], check=False)
    if res.returncode != 0:
        return False, res.stderr
    return True, "Pushed."

def create_pull_request(repo_name: str, branch_name: str, title: str, body: str, base: str = "main", dry_run: bool=False) -> dict:
    """
    Use GitHub REST API to create a PR. Requires GITHUB_TOKEN in config.
    Returns the JSON response as dict.
    """
    if dry_run:
        return {
            "html_url": f"https://github.com/{REPO_OWNER}/{repo_name}/pull/fake",
            "title": title,
            "body": body,
            "dry_run": True
        }
    import requests
    url = f"https://api.github.com/repos/{REPO_OWNER}/{repo_name}/pulls"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    payload = {"title": title, "head": branch_name, "base": base, "body": body}
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()
