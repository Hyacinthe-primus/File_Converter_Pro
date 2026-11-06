import os
import sys
import threading
import types
from pathlib import Path

import fitz
import pytest
from docx import Document
from PIL import Image

import context_menu.window as cm_window


def _make_pdf(path: Path, labels: list[str]) -> str:
    doc = fitz.open()
    for label in labels:
        page = doc.new_page()
        page.insert_text((72, 72), label)
    doc.save(str(path))
    doc.close()
    return str(path)


def _make_docx(path: Path, paragraphs: list[str]) -> str:
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(str(path))
    return str(path)


def _make_image(path: Path, size: tuple[int, int]) -> str:
    Image.new("RGB", size, (120, 30, 30)).save(path)
    return str(path)


def _helper_module():
    try:
        from context_menu import conversion_helpers
    except ImportError:
        return cm_window
    return conversion_helpers


@pytest.mark.parametrize(
    ("order", "expected"),
    [
        ("none", ["file10.txt", "file1.txt", "file2.txt"]),
        ("", ["file10.txt", "file1.txt", "file2.txt"]),
        ("unsupported", ["file10.txt", "file1.txt", "file2.txt"]),
        ("manual", ["file10.txt", "file1.txt", "file2.txt"]),
        ("current", ["file10.txt", "file1.txt", "file2.txt"]),
        ("alphabetical_asc", ["file1.txt", "file10.txt", "file2.txt"]),
        ("alphabetical_desc", ["file2.txt", "file10.txt", "file1.txt"]),
        ("alpha_az", ["file1.txt", "file10.txt", "file2.txt"]),
        ("alpha_za", ["file2.txt", "file10.txt", "file1.txt"]),
        ("numerical_asc", ["file1.txt", "file2.txt", "file10.txt"]),
        ("numerical_desc", ["file10.txt", "file2.txt", "file1.txt"]),
        ("num_asc", ["file1.txt", "file2.txt", "file10.txt"]),
        ("num_desc", ["file10.txt", "file2.txt", "file1.txt"]),
        ("date_asc", ["file10.txt", "file1.txt", "file2.txt"]),
        ("date_desc", ["file2.txt", "file1.txt", "file10.txt"]),
    ],
)
def test_sort_files_all_supported_orders(tmp_path, order, expected):
    inputs = []
    for index, name in enumerate(["file10.txt", "file1.txt", "file2.txt"]):
        path = tmp_path / name
        path.write_text("x")
        timestamp = 1_000_000_000 + index * 100
        os.utime(path, (timestamp, timestamp))
        inputs.append(str(path))

    result = cm_window._sort_files(inputs, order)

    assert [Path(path).name for path in result] == expected


def test_merge_pdfs_preserves_page_count_and_order(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    a_pdf = _make_pdf(tmp_path / "a.pdf", ["A"])
    b_pdf = _make_pdf(tmp_path / "b.pdf", ["B1", "B2"])

    cm_window._merge_pdfs([b_pdf, a_pdf], str(out_dir), "alphabetical_asc")

    outputs = list(out_dir.glob("merged_*.pdf"))
    assert len(outputs) == 1
    with fitz.open(outputs[0]) as merged:
        assert merged.page_count == 3
        assert [page.get_text().strip() for page in merged] == ["A", "B1", "B2"]


def test_merge_docx_preserves_paragraph_order_and_page_break_placement(tmp_path):
    from docx.oxml.ns import qn

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    a_docx = _make_docx(tmp_path / "a.docx", ["A1", "A2"])
    b_docx = _make_docx(tmp_path / "b.docx", ["B1", "B2"])

    cm_window._merge_docx([b_docx, a_docx], str(out_dir), "alphabetical_asc")

    outputs = list(out_dir.glob("merged_*.docx"))
    assert len(outputs) == 1
    merged = Document(str(outputs[0]))
    texts = [paragraph.text for paragraph in merged.paragraphs if paragraph.text]
    assert texts == ["A1", "A2", "B1", "B2"]

    positions = {paragraph.text: index for index, paragraph in enumerate(merged.paragraphs) if paragraph.text}
    break_positions = [
        index
        for index, paragraph in enumerate(merged.paragraphs)
        if any(br.get(qn("w:type")) == "page" for br in paragraph._element.iter(qn("w:br")))
    ]
    assert break_positions
    assert all(positions["A2"] < index < positions["B1"] for index in break_positions)


def test_merge_pdfs_preserves_bookmarks(tmp_path):
    from pypdf import PdfReader

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    a_pdf = tmp_path / "a.pdf"
    b_pdf = tmp_path / "b.pdf"
    for path, label in ((a_pdf, "A"), (b_pdf, "B")):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), label)
        doc.set_toc([[1, label, 1]])
        doc.save(str(path))
        doc.close()

    output = out_dir / "merged.pdf"
    cm_window._merge_pdfs(
        [str(b_pdf), str(a_pdf)],
        str(out_dir),
        "alphabetical_asc",
        dst_path=str(output),
    )

    reader = PdfReader(str(output))
    assert [item.title for item in reader.outline] == ["A", "B"]
    assert [page.extract_text().strip() for page in reader.pages] == ["A", "B"]


def test_merge_pdfs_failure_preserves_existing_output_and_cleans_staging(tmp_path):
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"not a pdf")
    output = tmp_path / "merged.pdf"
    output.write_bytes(b"stale")

    with pytest.raises(RuntimeError, match="PDF merge failed"):
        cm_window._merge_pdfs([str(invalid)], str(tmp_path), "none", dst_path=str(output))

    assert output.read_bytes() == b"stale"
    assert not list(tmp_path.glob("~fcp_merge_*"))


def test_merge_pdfs_same_timestamp_does_not_overwrite_output(monkeypatch, tmp_path):
    src = _make_pdf(tmp_path / "input.pdf", ["A"])
    monkeypatch.setattr(
        "context_menu.conversion_helpers.time.strftime",
        lambda _format: "20240101_120000",
    )

    cm_window._merge_pdfs([src], str(tmp_path), "none")
    cm_window._merge_pdfs([src], str(tmp_path), "none")

    outputs = sorted(tmp_path.glob("merged_*.pdf"))
    assert [path.name for path in outputs] == [
        "merged_20240101_120000.pdf",
        "merged_20240101_120000_1.pdf",
    ]


@pytest.mark.parametrize(
    ("helper", "suffix"),
    [
        (cm_window._merge_pdfs, "pdf"),
        (cm_window._merge_docx, "docx"),
    ],
)
def test_merge_requires_at_least_one_input(tmp_path, helper, suffix):
    with pytest.raises(RuntimeError, match="at least one input file"):
        helper([], str(tmp_path), "none")

    assert not list(tmp_path.glob(f"merged_*.{suffix}"))


def test_merge_images_preserves_page_count_and_order(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    wide = _make_image(tmp_path / "wide.png", (80, 40))
    tall = _make_image(tmp_path / "tall.png", (40, 80))

    cm_window._merge_images_to_pdf([wide, tall], str(out_dir))

    outputs = list(out_dir.glob("merged_images_*.pdf"))
    assert len(outputs) == 1
    with fitz.open(outputs[0]) as merged:
        assert merged.page_count == 2
        assert merged[0].rect.width > merged[0].rect.height
        assert merged[1].rect.width < merged[1].rect.height


def test_merge_images_cancellation_raises_before_output(tmp_path):
    src = _make_image(tmp_path / "image.png", (10, 10))
    cancel_event = threading.Event()
    cancel_event.set()

    with pytest.raises(cm_window._ConversionCancelled):
        cm_window._merge_images_to_pdf([src], str(tmp_path), cancel_event=cancel_event)

    assert not list(tmp_path.glob("merged_images_*.pdf"))


def test_merge_pdfs_cancellation_raises_before_output(tmp_path):
    src = _make_pdf(tmp_path / "input.pdf", ["A"])
    cancel_event = threading.Event()
    cancel_event.set()

    with pytest.raises(cm_window._ConversionCancelled):
        cm_window._merge_pdfs([src], str(tmp_path), "none", cancel_event=cancel_event)

    assert not list(tmp_path.glob("merged_*.pdf"))


def test_merge_docx_cancellation_raises_before_output(tmp_path):
    src = _make_docx(tmp_path / "input.docx", ["A"])
    cancel_event = threading.Event()
    cancel_event.set()

    with pytest.raises(cm_window._ConversionCancelled):
        cm_window._merge_docx([src], str(tmp_path), "none", cancel_event=cancel_event)

    assert not list(tmp_path.glob("merged_*.docx"))


def _install_docx2pdf(monkeypatch, order, succeed, invalid=False):
    module = types.ModuleType("docx2pdf")

    def convert(src, dst):
        order.append("docx2pdf")
        if not succeed:
            raise RuntimeError("docx2pdf failed")
        if invalid:
            Path(dst).write_bytes(b"%PDF")
            return
        _make_pdf(Path(dst), ["docx2pdf"])

    module.convert = convert
    monkeypatch.setitem(sys.modules, "docx2pdf", module)


def _install_com(
    monkeypatch,
    order,
    succeed,
    invalid=False,
    error=None,
    fail_open=False,
    cleanup_calls=None,
):
    client = types.ModuleType("comtypes.client")

    class FakeDocument:
        def SaveAs(self, dst, FileFormat):
            if invalid:
                Path(dst).write_bytes(b"%PDF")
            else:
                _make_pdf(Path(dst), ["com"])

        def Close(self, _save):
            if cleanup_calls is not None:
                cleanup_calls.append("close")

    class FakeDocuments:
        def Open(self, _src):
            if fail_open:
                raise RuntimeError("open failed")
            return FakeDocument()

    class FakeWord:
        def __init__(self):
            self.Visible = False
            self.DisplayAlerts = 0
            self.Documents = FakeDocuments()

        def Quit(self):
            if cleanup_calls is not None:
                cleanup_calls.append("quit")

    def create_object(_name):
        order.append("com")
        if error is not None:
            raise error
        if not succeed:
            raise RuntimeError("com failed")
        return FakeWord()

    client.CreateObject = create_object
    package = types.ModuleType("comtypes")
    package.client = client
    package.__path__ = []
    monkeypatch.setitem(sys.modules, "comtypes", package)
    monkeypatch.setitem(sys.modules, "comtypes.client", client)


def _install_libreoffice(monkeypatch, order, succeed, returncode=0):
    import external_binaries

    if not succeed:
        monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: None)
        return

    monkeypatch.setattr(external_binaries, "resolve_binary", lambda _name: "soffice.exe")

    def run(args, **_kwargs):
        order.append("libreoffice")
        out_dir = Path(args[args.index("--outdir") + 1])
        src = Path(args[-1])
        _make_pdf(out_dir / f"{src.stem}.pdf", ["libreoffice"])
        return types.SimpleNamespace(returncode=returncode, stderr="libreoffice failed")

    monkeypatch.setattr("subprocess.run", run)


def test_docx_to_pdf_windows_com_success_short_circuits(monkeypatch, tmp_path):
    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(monkeypatch, order, succeed=True)
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["com"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["com"]


def test_docx_to_pdf_macos_docx2pdf_success_short_circuits(monkeypatch, tmp_path):
    from context_menu import conversion_helpers

    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)
    monkeypatch.setattr(conversion_helpers.sys, "platform", "darwin")

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["docx2pdf"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["docx2pdf"]


def test_docx_to_pdf_invalid_com_output_falls_through_to_libreoffice(monkeypatch, tmp_path):
    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(monkeypatch, order, succeed=True, invalid=True)
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["com", "libreoffice"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["libreoffice"]


def test_docx_to_pdf_falls_through_to_docx2pdf(monkeypatch, tmp_path):
    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(monkeypatch, order, succeed=False)
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["com", "docx2pdf"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["docx2pdf"]


def test_docx_to_pdf_comtypes_binding_failure_falls_through_to_docx2pdf(monkeypatch, tmp_path):
    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(
        monkeypatch,
        order,
        succeed=False,
        error=ImportError("comtypes binding unavailable"),
    )
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["com", "docx2pdf"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["docx2pdf"]


def test_docx_to_pdf_direct_com_quits_word_after_open_failure(monkeypatch, tmp_path):
    order = []
    cleanup_calls = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(
        monkeypatch,
        order,
        succeed=True,
        fail_open=True,
        cleanup_calls=cleanup_calls,
    )
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["com", "docx2pdf"]
    assert cleanup_calls == ["quit"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["docx2pdf"]


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_docx_to_pdf_skips_docx2pdf_for_legacy_doc(monkeypatch, tmp_path, platform):
    from context_menu import conversion_helpers

    order = []
    src = tmp_path / "input.doc"
    src.write_bytes(b"legacy binary word document")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(monkeypatch, order, succeed=False)
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)
    monkeypatch.setattr(conversion_helpers.sys, "platform", platform)

    cm_window._convert_docx_to_pdf(str(src), str(out_dir))

    assert "docx2pdf" not in order
    if platform == "win32":
        assert order == ["com", "libreoffice"]
    else:
        assert order == ["libreoffice"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["libreoffice"]


def test_docx_to_pdf_skips_docx2pdf_for_uppercase_docx(monkeypatch, tmp_path):
    order = []
    src = _make_docx(tmp_path / "input.DOCX", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(monkeypatch, order, succeed=False)
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["com", "libreoffice"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["libreoffice"]


def test_docx_to_pdf_falls_through_to_libreoffice(monkeypatch, tmp_path):
    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(monkeypatch, order, succeed=False)
    _install_docx2pdf(monkeypatch, order, succeed=False)
    _install_libreoffice(monkeypatch, order, succeed=True)

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["com", "docx2pdf", "libreoffice"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["libreoffice"]


def test_docx_to_pdf_total_failure_raises(monkeypatch, tmp_path):
    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _install_com(monkeypatch, order, succeed=False)
    _install_docx2pdf(monkeypatch, order, succeed=False)
    _install_libreoffice(monkeypatch, order, succeed=False)
    monkeypatch.setattr(
        "docx.Document",
        lambda _path: (_ for _ in ()).throw(RuntimeError("reportlab failed")),
    )

    with pytest.raises(RuntimeError, match="All DOCX→PDF methods failed.") as exc_info:
        cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert "COM" in str(exc_info.value)
    assert "docx2pdf" in str(exc_info.value)
    assert order == ["com", "docx2pdf"]


def test_docx_to_pdf_total_failure_preserves_existing_output(monkeypatch, tmp_path):
    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    output = _make_pdf(out_dir / "input.pdf", ["stale"])
    original = Path(output).read_bytes()
    _install_com(monkeypatch, order, succeed=False)
    _install_docx2pdf(monkeypatch, order, succeed=False)
    _install_libreoffice(monkeypatch, order, succeed=False)
    monkeypatch.setattr(
        "docx.Document",
        lambda _path: (_ for _ in ()).throw(RuntimeError("reportlab failed")),
    )

    with pytest.raises(RuntimeError, match="All DOCX→PDF methods failed."):
        cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert Path(output).read_bytes() == original
    assert not list(tmp_path.glob("~fcp_pdf_stage_*"))


def test_docx_to_pdf_invalid_input_fails_before_engines(monkeypatch, tmp_path):
    order = []
    src = tmp_path / "invalid.docx"
    src.write_bytes(b"not a docx")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    output = _make_pdf(out_dir / "invalid.pdf", ["stale"])
    original = Path(output).read_bytes()
    _install_com(monkeypatch, order, succeed=True)
    _install_docx2pdf(monkeypatch, order, succeed=True)
    _install_libreoffice(monkeypatch, order, succeed=True)

    with pytest.raises(RuntimeError, match="Invalid Word input: not a DOCX"):
        cm_window._convert_docx_to_pdf(str(src), str(out_dir))

    assert order == []
    assert Path(output).read_bytes() == original


def test_docx_to_pdf_docx2pdf_system_exit_falls_through_on_macos(monkeypatch, tmp_path):
    from context_menu import conversion_helpers

    order = []
    src = _make_docx(tmp_path / "input.docx", ["input"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    module = types.ModuleType("docx2pdf")

    def convert(_src, _dst):
        order.append("docx2pdf")
        raise SystemExit(1)

    module.convert = convert
    monkeypatch.setitem(sys.modules, "docx2pdf", module)
    _install_libreoffice(monkeypatch, order, succeed=True)
    monkeypatch.setattr(conversion_helpers.sys, "platform", "darwin")

    cm_window._convert_docx_to_pdf(src, str(out_dir))

    assert order == ["docx2pdf", "libreoffice"]
    with fitz.open(out_dir / "input.pdf") as output:
        assert [page.get_text().strip() for page in output] == ["libreoffice"]


def test_pdf_to_docx_with_images_fake_backend_writes_real_docx(monkeypatch, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    calls = []
    module = types.ModuleType("pdf2docx")

    class FakeConverter:
        def __init__(self, path):
            calls.append(("init", path))

        def convert(self, path, **kwargs):
            calls.append(("convert", path, kwargs))
            doc = Document()
            doc.add_paragraph("fake pdf2docx output")
            doc.save(path)

        def close(self):
            calls.append(("close",))

    module.Converter = FakeConverter
    monkeypatch.setitem(sys.modules, "pdf2docx", module)
    monkeypatch.setattr(cm_window.sys, "platform", "linux")

    cm_window._convert_pdf_to_docx(str(src), str(out_dir), mode="with_images")

    output = out_dir / "input.docx"
    assert output.is_file()
    assert [paragraph.text for paragraph in Document(str(output)).paragraphs] == ["fake pdf2docx output"]
    assert [call[0] for call in calls] == ["init", "convert", "close"]


@pytest.mark.parametrize(
    ("module_name", "conversion_type", "helper_name", "kind"),
    [
        ("watcher", "merge_pdf_none", "_merge_pdfs", "pdf"),
        ("watcher", "merge_docx_none", "_merge_docx", "docx"),
        ("scheduler", "merge_pdf_none", "_merge_pdfs", "pdf"),
        ("scheduler", "merge_docx_none", "_merge_docx", "docx"),
    ],
)
def test_automation_non_ocr_merge_routing(monkeypatch, tmp_path, module_name, conversion_type, helper_name, kind):
    from tasks import scheduler, watcher

    helper_module = _helper_module()
    calls = []
    monkeypatch.setattr(helper_module, helper_name, lambda *args, **kwargs: calls.append((args, kwargs)))
    out_dir = tmp_path / "out"
    files = [str(tmp_path / f"one.{kind}"), str(tmp_path / f"two.{kind}")]
    runner = watcher._run_merge if module_name == "watcher" else scheduler._run_merge

    runner(conversion_type, files, str(out_dir), ocr=False)

    assert calls == [((files, str(out_dir), "none"), {})]


def test_automation_merge_none_uses_stable_path_order(monkeypatch, tmp_path):
    from tasks import watcher

    helper_module = _helper_module()
    calls = []
    monkeypatch.setattr(helper_module, "_merge_pdfs", lambda *args, **kwargs: calls.append((args, kwargs)))
    out_dir = tmp_path / "out"
    two = str(tmp_path / "two.pdf")
    one = str(tmp_path / "one.pdf")

    watcher._run_merge("merge_pdf_none", [two, one], str(out_dir), ocr=False)

    assert calls == [(([one, two], str(out_dir), "none"), {})]
