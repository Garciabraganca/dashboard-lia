from build_info import get_build_stamp


def test_get_build_stamp_from_env(monkeypatch):
    get_build_stamp.cache_clear()
    monkeypatch.setenv("LIA_BUILD_STAMP", "build-from-env")
    stamp = get_build_stamp()
    assert stamp == "build-from-env"


def test_get_build_stamp_includes_commit_branch(monkeypatch):
    get_build_stamp.cache_clear()
    monkeypatch.delenv("LIA_BUILD_STAMP", raising=False)

    def fake_run_git_command(args):
        key = tuple(args)
        mapping = {
            ("rev-parse", "--short", "HEAD"): "abc1234",
            ("log", "-1", "--format=%cd", "--date=iso-strict"): "2026-02-15T19:00:00+00:00",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
        }
        return mapping.get(key)

    monkeypatch.setattr("build_info._run_git_command", fake_run_git_command)
    stamp = get_build_stamp()

    assert "commit=abc1234" in stamp
    assert "branch=main" in stamp
    assert "commit_date=2026-02-15T19:00:00+00:00" in stamp
    assert "app_started_utc=" in stamp
