import os
import tempfile
import pytest
from src.tools.file_tools import read_file, make_unified_diff, apply_file_patch

@pytest.fixture
def temp_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "testfile.txt")
        yield tmpdir, file_path

def test_read_file_existing(temp_file):
    tmpdir, path = temp_file
    content = "hello world\nsecond line"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    assert read_file(path) == content

def test_read_file_missing(temp_file):
    tmpdir, path = temp_file
    # no file created
    assert read_file(path) == ""

def test_make_unified_diff_new_file(temp_file):
    tmpdir, path = temp_file
    new_content = "line 1\nline 2\n"
    diff = make_unified_diff(path, new_content, repo_root=tmpdir)
    assert diff.startswith(f"--- a/{os.path.basename(path)}")
    assert diff.endswith(f"+line 2\n")
    assert "+line 1\n" in diff

def test_make_unified_diff_existing_file(temp_file):
    tmpdir, path = temp_file
    old_content = "line 1\nline 2\n"
    new_content = "line 1\nline 3\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(old_content)
    diff = make_unified_diff(os.path.relpath(path, tmpdir), new_content, repo_root=tmpdir)
    assert "-line 2\n" in diff
    assert "+line 3\n" in diff

@pytest.mark.skip(reason="Requires git repo and git_utils mocks")
def test_apply_file_patch_dry_run(temp_file):
    tmpdir, path = temp_file
    new_content = "new file content\n"
    branch_name = "test/branch"
    commit_message = "Test commit"
    # Dry run should not actually commit or push anything
    result = apply_file_patch(
        os.path.relpath(path, tmpdir), new_content,
        branch_name, commit_message,
        dry_run=True
    )
    assert result["dry_run"] is True
    assert "patch" in result and result["patch"] is not None
    # Because dry run, applied should be True if patch generated
    assert result["applied"] or result["error"] == "No changes detected."
