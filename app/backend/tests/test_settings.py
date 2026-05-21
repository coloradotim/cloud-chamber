import json
from pathlib import Path

from cloud_chamber.settings import (
    CLOUD_CHAMBER_CM1_ROOT,
    CLOUD_CHAMBER_RUNTIME_HOME,
    DEFAULT_RUNTIME_HOME,
    discover_cm1,
    load_settings,
)


def test_settings_default_to_cloud_chamber_runtime_home() -> None:
    settings = load_settings(environ={}, probe_paths=())

    assert settings.runtime_home == DEFAULT_RUNTIME_HOME.expanduser()
    assert settings.cache_dir == DEFAULT_RUNTIME_HOME.expanduser() / "cache"
    assert settings.log_dir == DEFAULT_RUNTIME_HOME.expanduser() / "logs"
    assert settings.cm1_root is None
    assert settings.cm1_run_dir is None


def test_settings_load_saved_config_from_runtime_home(tmp_path: Path) -> None:
    runtime_home = tmp_path / "CloudChamber"
    cm1_root = tmp_path / "cm1"
    cm1_run_dir = cm1_root / "run"
    runtime_home.mkdir()
    (runtime_home / "settings.json").write_text(
        json.dumps(
            {
                "cm1_root": str(cm1_root),
                "cm1_run_dir": str(cm1_run_dir),
                "cache_dir": str(tmp_path / "cache"),
                "log_dir": str(tmp_path / "logs"),
            }
        )
    )

    settings = load_settings(home=runtime_home, environ={}, probe_paths=())

    assert settings.runtime_home == runtime_home
    assert settings.cm1_root == cm1_root
    assert settings.cm1_run_dir == cm1_run_dir
    assert settings.cache_dir == tmp_path / "cache"
    assert settings.log_dir == tmp_path / "logs"


def test_environment_override_wins_over_saved_cm1_root(tmp_path: Path) -> None:
    runtime_home = tmp_path / "CloudChamber"
    runtime_home.mkdir()
    saved_root = tmp_path / "saved-cm1"
    env_root = tmp_path / "env-cm1"
    (runtime_home / "settings.json").write_text(json.dumps({"cm1_root": str(saved_root)}))

    settings = load_settings(
        home=runtime_home,
        environ={CLOUD_CHAMBER_CM1_ROOT: str(env_root)},
        probe_paths=(),
    )

    assert settings.cm1_root == env_root
    assert settings.cm1_run_dir == env_root / "run"


def test_runtime_home_environment_override() -> None:
    runtime_home = Path("/tmp/cloud-chamber-test-home")

    settings = load_settings(
        environ={CLOUD_CHAMBER_RUNTIME_HOME: str(runtime_home)},
        probe_paths=(),
    )

    assert settings.runtime_home == runtime_home


def test_probe_paths_are_defaults_not_requirements(tmp_path: Path) -> None:
    cm1_root = tmp_path / "cm1r21.1"
    (cm1_root / "run").mkdir(parents=True)

    settings = load_settings(environ={}, probe_paths=(cm1_root,))

    assert settings.cm1_root == cm1_root
    assert settings.cm1_run_dir == cm1_root / "run"


def test_cm1_discovery_reports_missing_paths_without_launching(tmp_path: Path) -> None:
    settings = load_settings(home=tmp_path / "CloudChamber", environ={}, probe_paths=())

    status = discover_cm1(settings)

    assert not status.ready
    assert "Set CLOUD_CHAMBER_CM1_ROOT" in status.message
    assert "CM1 root path" in status.missing
    assert "CM1 run directory" in status.missing


def test_cm1_discovery_reports_ready_when_run_dir_has_executable(tmp_path: Path) -> None:
    cm1_root = tmp_path / "cm1"
    cm1_run_dir = cm1_root / "run"
    cm1_run_dir.mkdir(parents=True)
    (cm1_run_dir / "cm1.exe").write_text("")
    settings = load_settings(
        home=tmp_path / "CloudChamber",
        environ={CLOUD_CHAMBER_CM1_ROOT: str(cm1_root)},
        probe_paths=(),
    )

    status = discover_cm1(settings)

    assert status.ready
    assert status.cm1_root == cm1_root
    assert status.cm1_run_dir == cm1_run_dir
    assert status.missing == ()
