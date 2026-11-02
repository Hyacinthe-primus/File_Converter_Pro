"""Concurrency and cleanup tests for PowerPoint COM temporary workspaces."""

import sys
import threading
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from converter.converters import AdvancedConverterEngine
from converter.mixins import office_com


def _install_fake_comtypes(monkeypatch):
    comtypes = types.ModuleType("comtypes")
    comtypes.__path__ = []
    client = types.ModuleType("comtypes.client")
    comtypes.client = client
    monkeypatch.setitem(sys.modules, "comtypes", comtypes)
    monkeypatch.setitem(sys.modules, "comtypes.client", client)


def _source_files(tmp_path):
    first = tmp_path / "deck-one.pptx"
    second = tmp_path / "deck-two.pptx"
    first.write_bytes(b"first source")
    second.write_bytes(b"second source")
    return first, second


def test_concurrent_pptx_conversions_use_isolated_workspaces(tmp_path, monkeypatch):
    _install_fake_comtypes(monkeypatch)
    first, second = _source_files(tmp_path)
    first_out = tmp_path / "first.pdf"
    second_out = tmp_path / "second.pdf"
    barrier = threading.Barrier(2)
    captured = []
    lock = threading.Lock()

    def fake_run(command, **kwargs):
        env = kwargs["env"]
        workspace_file = Path(env["FCP_DST"])
        with lock:
            captured.append(workspace_file)
        barrier.wait(timeout=5)
        workspace_file.write_bytes(f"PDF:{Path(env['FCP_SRC']).name}".encode())
        return types.SimpleNamespace(stderr=b"")

    monkeypatch.setattr(office_com.subprocess, "run", fake_run)
    engine = AdvancedConverterEngine()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(engine._pptx_to_pdf_com, str(first), str(first_out)),
            pool.submit(engine._odp_to_pdf_com, str(second), str(second_out)),
        ]
        results = [future.result(timeout=10) for future in futures]

    assert results == [True, True]
    assert len(captured) == 2
    assert captured[0].name == captured[1].name == "pptx_com_out.pdf"
    assert captured[0].parent != captured[1].parent
    assert first_out.read_bytes() == b"PDF:deck-one.pptx"
    assert second_out.read_bytes() == b"PDF:deck-two.pptx"
    assert not captured[0].parent.exists()
    assert not captured[1].parent.exists()


def test_one_conversion_cleanup_does_not_delete_other_workspace(tmp_path, monkeypatch):
    _install_fake_comtypes(monkeypatch)
    first, second = _source_files(tmp_path)
    first_out = tmp_path / "first.pdf"
    second_out = tmp_path / "second.pdf"
    second_ready = threading.Event()
    first_finished = threading.Event()
    captured = {}
    lock = threading.Lock()

    def fake_run(command, **kwargs):
        env = kwargs["env"]
        workspace_file = Path(env["FCP_DST"])
        with lock:
            captured[Path(env["FCP_SRC"]).name] = workspace_file
        workspace_file.write_bytes(f"PDF:{Path(env['FCP_SRC']).name}".encode())
        if Path(env["FCP_SRC"]).name == "deck-two.pptx":
            (workspace_file.parent / "keep.txt").write_text("keep", encoding="utf-8")
            second_ready.set()
            assert first_finished.wait(timeout=5)
            assert (workspace_file.parent / "keep.txt").exists()
        return types.SimpleNamespace(stderr=b"")

    monkeypatch.setattr(office_com.subprocess, "run", fake_run)
    engine = AdvancedConverterEngine()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(engine._pptx_to_pdf_com, str(first), str(first_out))
        second_future = pool.submit(engine._pptx_to_pdf_com, str(second), str(second_out))
        assert second_ready.wait(timeout=5)
        assert first_future.result(timeout=10) is True
        first_finished.set()
        assert second_future.result(timeout=10) is True

    assert first_out.exists()
    assert second_out.exists()
    assert not captured["deck-one.pptx"].parent.exists()
    assert not captured["deck-two.pptx"].parent.exists()


def test_exception_in_one_conversion_does_not_affect_another(tmp_path, monkeypatch):
    _install_fake_comtypes(monkeypatch)
    first, second = _source_files(tmp_path)
    first_out = tmp_path / "first.pdf"
    second_out = tmp_path / "second.pdf"
    barrier = threading.Barrier(2)
    captured = []
    lock = threading.Lock()

    def fake_run(command, **kwargs):
        env = kwargs["env"]
        workspace_file = Path(env["FCP_DST"])
        with lock:
            captured.append(workspace_file)
        barrier.wait(timeout=5)
        if Path(env["FCP_SRC"]).name == "deck-one.pptx":
            raise RuntimeError("simulated PowerPoint failure")
        workspace_file.write_bytes(b"PDF:second")
        return types.SimpleNamespace(stderr=b"")

    monkeypatch.setattr(office_com.subprocess, "run", fake_run)
    engine = AdvancedConverterEngine()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(engine._pptx_to_pdf_com, str(first), str(first_out)),
            pool.submit(engine._pptx_to_pdf_com, str(second), str(second_out)),
        ]
        results = [future.result(timeout=10) for future in futures]

    assert results == [False, True]
    assert not first_out.exists()
    assert second_out.read_bytes() == b"PDF:second"
    assert all(not path.parent.exists() for path in captured)


def test_failed_conversion_cleans_its_workspace(tmp_path, monkeypatch):
    _install_fake_comtypes(monkeypatch)
    source, _ = _source_files(tmp_path)
    output = tmp_path / "failed.pdf"
    captured = []

    def fake_run(command, **kwargs):
        captured.append(Path(kwargs["env"]["FCP_DST"]))
        raise RuntimeError("simulated PowerPoint failure")

    monkeypatch.setattr(office_com.subprocess, "run", fake_run)
    engine = AdvancedConverterEngine()

    assert engine._pptx_to_pdf_com(str(source), str(output)) is False
    assert captured
    assert not captured[0].parent.exists()
    assert not output.exists()
