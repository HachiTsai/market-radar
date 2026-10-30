import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import committer as c  # noqa: E402


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for cmd in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], check=True)
    return tmp_path


def test_ensure_coauthor_is_idempotent():
    once = c.ensure_coauthor_line("feat(x): y\n")
    assert once.endswith(c.COAUTHOR_LINE + "\n")
    assert c.ensure_coauthor_line(once) == once


def test_header_validation():
    assert c.HEADER_RE.match("feat(skills): add thing")
    assert c.HEADER_RE.match("fix: no scope")
    assert not c.HEADER_RE.match("purge(x): invented type")


def test_infer_type():
    assert c.infer_commit_type(["a.md"], "") == "docs"
    assert c.infer_commit_type(["tests/test_a.py"], "") == "test"
    assert c.infer_commit_type(["a.py"], "+ fix the bug") == "fix"
    assert c.infer_commit_type(["a.py"], "+x = 1") == "chore"


def test_infer_scope():
    assert c.infer_scope(["docs/a.md", "docs/b.md"]) == "docs"
    assert c.infer_scope(["docs/a.md", "src/b.py"]) == "project"
    assert c.infer_scope(["README.md"]) == "project"


def test_find_sensitive():
    assert c.find_sensitive([".env", "a/b/id_rsa", "src/app.py", "credentials/x.txt"]) == [
        ".env", "a/b/id_rsa", "credentials/x.txt"]


def test_path_matches():
    assert c.path_matches("a/b/c.txt", "a/b")
    assert c.path_matches("x.log", "*.log")
    assert not c.path_matches("ab/c", "a")


def test_auto_quick_commits_without_push(repo):
    (repo / "a.txt").write_text("hi")
    assert c.main(["--auto-quick", "--no-push"]) == 0
    log = subprocess.run(["git", "log", "-1", "--format=%B"], capture_output=True, text=True).stdout
    assert log.startswith("feat(project): update project")
    assert c.COAUTHOR_LINE in log
    assert not (repo / ".git" / "COMMIT_MSG_TEMP").exists()


def test_sensitive_file_blocks_commit(repo):
    (repo / ".env").write_text("K=1")
    assert c.main(["--auto-quick", "--no-push"]) == 1
    assert subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True).returncode != 0


def test_bad_header_rejected(repo):
    (repo / "a.txt").write_text("hi")
    msg = repo / "m.txt"
    msg.write_text("whatever: bad\n")
    assert c.main(["--message-file", str(msg), "--no-push"]) == 1


def test_exclude_and_stage_list(repo):
    (repo / "a.txt").write_text("1")
    (repo / "b.txt").write_text("2")
    assert c.main(["--exclude", "b.txt", "--dry-run", "--auto-quick"]) == 0
    assert c.staged_files() == ["a.txt"]
    assert c.run_git_add(paths=["b.txt"])
    assert c.staged_files() == ["b.txt"]


def test_dry_run_does_not_commit(repo):
    (repo / "a.txt").write_text("hi")
    assert c.main(["--auto-quick", "--dry-run"]) == 0
    assert subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True).returncode != 0


def test_missing_deps_blocks_commit_and_flag_allows(repo):
    (repo / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = ["pytest==9.1.1"]\n')
    (repo / "app.py").write_text("import os\nimport some_unrecorded_pkg_xyz\n")
    assert c.main(["--auto-quick", "--no-push"]) == 1
    assert c.main(["--auto-quick", "--no-push", "--allow-missing-deps"]) == 0


def test_manifest_sync_and_local_imports(repo):
    rules_dir = repo / ".claude" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "python-environment.md").write_text(
        '# Rule\n```toml\n[project]\nname = "x"\ndependencies = ["pytest==9.1.1"]\n```\n'
    )
    (repo / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = ["pytest==9.1.1", "httpx==0.28.1"]\n')
    (repo / "helper.py").write_text("X = 1\n")
    (repo / "app.py").write_text("import sys\nimport helper\nimport pytest\n")
    issues = c.find_dependency_issues(["app.py", "helper.py"], repo)
    assert len(issues) == 1
    assert "httpx" in issues[0]
    (rules_dir / "python-environment.md").write_text(
        '# Rule\n```toml\n[project]\nname = "x"\ndependencies = ["pytest==9.1.1", "httpx==0.28.1"]\n```\n'
    )
    assert c.find_dependency_issues(["app.py", "helper.py"], repo) == []


def test_rule_index_sync_between_claude_and_agent_md(repo):
    claude_rules = repo / ".claude" / "rules"
    claude_rules.mkdir(parents=True, exist_ok=True)
    (claude_rules / "gcp-free-tier.md").write_text("# GCP\n")

    agent_rules = repo / ".agent" / "rules"
    agent_rules.mkdir(parents=True, exist_ok=True)
    (agent_rules / "AGENT.md").write_text("# Bridge\n")
    (agent_rules / "extra.md").write_text("# Duplicate\n")
    (repo / "CLAUDE.md").write_text("# Index\n")

    issues = c.find_rule_sync_issues(repo)
    assert len(issues) == 3

    (agent_rules / "extra.md").unlink()
    (agent_rules / "AGENT.md").write_text("# Bridge\n- @[.claude/rules/gcp-free-tier.md]\n")
    (repo / "CLAUDE.md").write_text("# Index\n- @[.claude/rules/gcp-free-tier.md]\n")
    assert c.find_rule_sync_issues(repo) == []

