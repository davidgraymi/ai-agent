import os
import subprocess
import pytest
from unittest.mock import patch, MagicMock
import src.tools.git_utils as git_utils

# Helper to mock subprocess.run
def mock_subprocess_run(returncode=0, stdout="", stderr="", check=True):
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    if check and returncode != 0:
        # Simulate subprocess.CalledProcessError
        def raise_err(*args, **kwargs):
            raise subprocess.CalledProcessError(returncode, args[0], output=stdout, stderr=stderr)
        mock.side_effect = raise_err
    return mock

def test_current_branch_normal():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = mock_subprocess_run(stdout="feature-branch\n")
        branch = git_utils.current_branch()
        assert branch == "feature-branch"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True, capture_output=True, text=True, cwd=None
        )

def test_current_branch_dry_run():
    result = git_utils.current_branch(dry_run=True)
    assert result is None

def test_create_branch_calls_git_commands():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = mock_subprocess_run()
        git_utils.create_branch("test-branch")
        calls = [call.args[0] for call in mock_run.call_args_list]
        assert ["git", "fetch", "origin"] in calls
        assert ["git", "checkout", "-b", "test-branch"] in calls

def test_create_branch_dry_run():
    with patch("subprocess.run") as mock_run:
        git_utils.create_branch("test-branch", dry_run=True)
        mock_run.assert_not_called()

def test_checkout_branch_calls_git_checkout():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = mock_subprocess_run()
        git_utils.checkout_branch("main")
        mock_run.assert_called_once_with(
            ["git", "checkout", "main"], check=True, capture_output=True, text=True, cwd=None
        )

def test_checkout_branch_dry_run():
    with patch("subprocess.run") as mock_run:
        git_utils.checkout_branch("main", dry_run=True)
        mock_run.assert_not_called()

def test_stage_patch_success(tmp_path):
    patch_text = "some patch content"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = mock_subprocess_run(returncode=0)
        ok, msg = git_utils.stage_patch(patch_text)
        assert ok is True
        assert "Patch applied" in msg
        # The temp patch file should be deleted (tested indirectly)

def test_stage_patch_failure(tmp_path):
    patch_text = "bad patch content"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = mock_subprocess_run(returncode=1, stderr="patch failed", check=False)
        ok, msg = git_utils.stage_patch(patch_text)
        assert not ok
        assert "patch failed" in msg

def test_stage_patch_dry_run():
    ok, msg = git_utils.stage_patch("anything", dry_run=True)
    assert ok
    assert "Dry run" in msg

def test_commit_index_returns_sha():
    with patch("subprocess.run") as mock_run:
        # First call is commit, second call is rev-parse HEAD
        mock_run.side_effect = [
            mock_subprocess_run(),
            mock_subprocess_run(stdout="abcdef1234567890\n"),
        ]
        sha = git_utils.commit_index("commit message")
        assert sha == "abcdef1234567890"

def test_commit_index_dry_run():
    result = git_utils.commit_index("commit message", dry_run=True)
    assert isinstance(result, tuple)
    assert "Dry run" in result[1]

def test_push_branch_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = mock_subprocess_run(returncode=0)
        ok, msg = git_utils.push_branch("feature-branch")
        assert ok
        assert "Pushed" in msg

def test_push_branch_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = mock_subprocess_run(returncode=1, stderr="push error", check=False)
        ok, msg = git_utils.push_branch("feature-branch")
        assert not ok
        assert "push error" in msg

def test_push_branch_dry_run():
    ok, msg = git_utils.push_branch("feature-branch", dry_run=True)
    assert ok
    assert "Dry run" in msg

def test_create_pull_request_dry_run():
    pr = git_utils.create_pull_request("branch-name", "title", "body", dry_run=True)
    assert isinstance(pr, dict)
    assert pr.get("dry_run") is True
    assert pr["title"] == "title"
    assert "https://github.com/" in pr["html_url"]

@pytest.mark.skipif("requests" not in globals(), reason="requests not installed")
def test_create_pull_request_real(monkeypatch):
    # We patch requests.post to simulate a GitHub API response
    import requests
    class DummyResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {"html_url": "http://fakepr.url", "title": "pr title"}

    def fake_post(url, headers, json):
        assert "Authorization" in headers
        assert json["title"] == "Test PR"
        return DummyResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    pr = git_utils.create_pull_request("branch", "Test PR", "PR body")
    assert pr["html_url"] == "http://fakepr.url"
    assert pr["title"] == "pr title"
