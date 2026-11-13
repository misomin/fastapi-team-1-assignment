"""Exercise deployment failure boundaries without SSH, systemd, Docker or a DB."""

import io
import fcntl
import json
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
import subprocess
import tarfile
from urllib.error import URLError

import pytest

from deploy import check_database, verify_health


REPO = Path(__file__).resolve().parents[2]
SHA = "a" * 40
SOURCE_HASH = "b" * 64


@pytest.fixture
def deployment(tmp_path):
    root = tmp_path / "remote"
    (root / "shared").mkdir(parents=True)
    (root / "shared" / "production.env").write_text("# mock settings\n")
    previous = root / "previous"
    previous.mkdir()
    (root / "current").symlink_to(previous)
    tools = tmp_path / "bin"
    tools.mkdir()
    uv = tools / "uv"
    uv.write_text('''#!/usr/bin/env bash
set -eu
printf 'uv %s\\n' "$*" >> "$TEST_LOG"
case "$FAIL_STAGE:$*" in
  sync:sync* | database:*deploy.check_database* | migration:*alembic* | health:*deploy.verify_health*) exit 1 ;;
esac
''')
    uv.chmod(0o700)
    sudo = tools / "sudo"
    sudo.write_text('''#!/usr/bin/env bash
set -eu
printf 'sudo %s\\n' "$*" >> "$TEST_LOG"
if [[ "$*" == *'docker ps '* ]]; then echo fastapi-assignment-3; fi
''')
    sudo.chmod(0o700)
    archive = tmp_path / "release.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(REPO / "deploy/wapang.service", arcname="deploy/wapang.service")
    log = tmp_path / "commands.log"

    def run(*, fail="", number=10, sha=SHA):
        env = {**os.environ, "PATH": f"{tools}:{os.environ['PATH']}",
               "WAPANG_ROOT": str(root), "UV_BIN": str(uv),
               "TEST_LOG": str(log), "FAIL_STAGE": fail}
        result = subprocess.run(
            ["bash", str(REPO / "deploy/deploy.sh"), str(archive), sha,
             SOURCE_HASH, str(number)], env=env, capture_output=True, text=True,
            timeout=10,
        )
        return result, log.read_text() if log.exists() else ""

    return run, root, previous


@pytest.mark.parametrize("stage", ["sync", "database"])
def test_preflight_failure_keeps_existing_service(deployment, stage):
    run, root, previous = deployment
    result, commands = run(fail=stage)
    assert result.returncode != 0
    assert (root / "current").resolve() == previous
    assert "docker stop" not in commands
    assert "docker update" not in commands
    assert "systemctl restart" not in commands
    assert "systemctl stop" not in commands
    assert not (root / "last-deployed").exists()


def test_migration_failure_leaves_service_stopped_and_current_unchanged(deployment):
    run, root, previous = deployment
    result, commands = run(fail="migration")
    assert result.returncode != 0
    assert commands.index("systemctl stop") < commands.index("alembic upgrade head")
    assert commands.index("docker stop") < commands.index("alembic upgrade head")
    assert "systemctl restart" not in commands
    assert (root / "current").resolve() == previous
    assert not (root / "last-deployed").exists()


def test_success_stops_old_services_before_migration_and_restart(deployment):
    run, root, previous = deployment
    result, commands = run()
    assert result.returncode == 0, result.stderr
    steps = ["sync --frozen", "deploy.check_database", "systemctl stop wapang.service",
             "docker update --restart=no fastapi-assignment-3",
             "docker stop fastapi-assignment-3", "alembic upgrade head",
             "systemctl restart wapang.service",
             "deploy.verify_health"]
    positions = [commands.index(step) for step in steps]
    assert positions == sorted(positions)
    assert commands.count("deploy.check_database") == 2
    assert (root / "current").resolve() != previous
    assert (root / "last-deployed").read_text() == f"10 {SHA} {SOURCE_HASH}\n"


def test_health_failure_does_not_record_success(deployment):
    run, root, _ = deployment
    result, commands = run(fail="health")
    assert result.returncode != 0
    assert "systemctl restart" in commands
    assert not (root / "last-deployed").exists()


def test_older_ci_cannot_deploy_after_a_newer_failed_attempt(deployment):
    run, root, previous = deployment
    newer, before = run(fail="migration", number=11)
    assert newer.returncode != 0
    older, after = run(number=10)
    assert older.returncode == 3
    assert "uv " not in after[len(before):]
    assert (root / "current").resolve() == previous


def test_same_ci_run_can_be_retried_but_cannot_change_commit(deployment):
    run, _, _ = deployment
    assert run(fail="migration")[0].returncode != 0
    assert run()[0].returncode == 0
    assert run(sha="c" * 40)[0].returncode != 0


def test_remote_lock_blocks_a_second_deployment(deployment):
    run, root, _ = deployment
    with (root / "deploy.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(run)
            try:
                with pytest.raises(FutureTimeoutError):
                    pending.result(timeout=0.2)
                assert not (root / "last-attempt").exists()
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
            assert pending.result(timeout=5)[0].returncode == 0


def test_health_retries_connection_failure_then_checks_source_hash(monkeypatch):
    replies = iter([URLError("not ready"), {"status": "ok", "hash": SOURCE_HASH}])

    def open_response(*_args, **_kwargs):
        reply = next(replies)
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(json.dumps(reply).encode())

    monkeypatch.setattr(verify_health, "urlopen", open_response)
    monkeypatch.setattr(verify_health.time, "sleep", lambda _: None)
    verify_health.verify("http://example.test/health", SOURCE_HASH)


@pytest.mark.parametrize("payload", [
    {"status": "ok", "hash": "wrong"}, {"status": "error", "hash": SOURCE_HASH}, [],
])
def test_health_rejects_wrong_code_or_status(monkeypatch, payload):
    monkeypatch.setattr(verify_health, "urlopen", lambda *_a, **_k: io.BytesIO(json.dumps(payload).encode()))
    with pytest.raises(RuntimeError, match="expected source hash"):
        verify_health.verify("http://example.test/health", SOURCE_HASH, timeout=0)


def test_production_check_requires_explicit_settings_without_disclosing_values(monkeypatch, capsys):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DB_PASSWORD", "sensitive-test-value")
    monkeypatch.delenv("DB_HOST", raising=False)
    assert check_database.main() == 1
    output = capsys.readouterr().err
    assert "DB_HOST" in output
    assert "sensitive-test-value" not in output
