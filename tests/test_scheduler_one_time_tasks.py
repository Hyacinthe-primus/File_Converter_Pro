"""One-time scheduled task deactivation regressions."""

import types
from pathlib import Path

import fitz

from tasks import scheduler


def _make_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "converted")
    document.save(str(path))
    document.close()


def _task(tmp_path: Path, trigger_type: str = "date") -> tuple[dict, Path]:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "source.txt").write_text("source", encoding="utf-8")
    toml_path = tmp_path / "automation.toml"
    toml_path.write_text(
        "\n".join(
            [
                "[scheduled_tasks.once]",
                "enabled = true",
                f'path = "{input_dir.as_posix()}"',
                f'output_dir = "{output_dir.as_posix()}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return (
        {
            "name": "once",
            "path": str(input_dir),
            "output_dir": str(output_dir),
            "rules": {"txt": [{"kind": "convert", "fmt": "pdf"}]},
            "recursive": False,
            "trigger": {"type": trigger_type},
            "toml_file": toml_path,
            "ocr": False,
        },
        toml_path,
    )


def test_successful_one_time_task_is_disabled(monkeypatch, tmp_path):
    task, toml_path = _task(tmp_path)

    def convert(_conversion_type, _source, output_dir, **_kwargs):
        _make_pdf(Path(output_dir) / "source.pdf")

    monkeypatch.setattr(scheduler, "_run_conversion", convert)

    scheduler._run_task(task)

    assert "enabled = false" in toml_path.read_text(encoding="utf-8")


def test_failed_one_time_task_remains_enabled(monkeypatch, tmp_path, caplog):
    task, toml_path = _task(tmp_path)
    monkeypatch.setattr(
        scheduler,
        "_run_conversion",
        lambda *_args, **_kwargs: types.SimpleNamespace(
            success=False, error="temporary conversion failure"
        ),
    )

    scheduler._run_task(task)

    assert "enabled = true" in toml_path.read_text(encoding="utf-8")
    assert "temporary conversion failure" in caplog.text
    assert "keeping it enabled for retry" in caplog.text


def test_temporary_failure_does_not_consume_one_time_task(monkeypatch, tmp_path):
    task, toml_path = _task(tmp_path)
    attempts = []

    def convert(_conversion_type, _source, output_dir, **_kwargs):
        attempts.append(True)
        if len(attempts) == 1:
            return types.SimpleNamespace(success=False, error="try again")
        _make_pdf(Path(output_dir) / "source.pdf")
        return True

    monkeypatch.setattr(scheduler, "_run_conversion", convert)

    scheduler._run_task(task)
    assert "enabled = true" in toml_path.read_text(encoding="utf-8")

    scheduler._run_task(task)
    assert "enabled = false" in toml_path.read_text(encoding="utf-8")
    assert len(attempts) == 2


def test_boolean_failure_result_keeps_one_time_task_enabled(monkeypatch, tmp_path):
    task, toml_path = _task(tmp_path)
    monkeypatch.setattr(scheduler, "_run_conversion", lambda *_args, **_kwargs: False)

    scheduler._run_task(task)

    assert "enabled = true" in toml_path.read_text(encoding="utf-8")


def test_exception_failure_keeps_one_time_task_enabled(monkeypatch, tmp_path):
    task, toml_path = _task(tmp_path)

    def fail(*_args, **_kwargs):
        raise RuntimeError("conversion exploded")

    monkeypatch.setattr(scheduler, "_run_conversion", fail)

    scheduler._run_task(task)

    assert "enabled = true" in toml_path.read_text(encoding="utf-8")


def test_recurring_task_is_never_auto_disabled(monkeypatch, tmp_path):
    task, toml_path = _task(tmp_path, trigger_type="interval")
    calls = []

    def convert(_conversion_type, _source, _output_dir, **_kwargs):
        return types.SimpleNamespace(success=False, error="recurring failure")

    monkeypatch.setattr(scheduler, "_run_conversion", convert)
    monkeypatch.setattr(
        scheduler,
        "_disable_date_task_in_toml",
        lambda *args: calls.append(args),
    )

    scheduler._run_task(task)

    assert calls == []
    assert "enabled = true" in toml_path.read_text(encoding="utf-8")
